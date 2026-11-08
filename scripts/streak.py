"""Build a compact vertical streak card (dist/streak.svg) from GitHub's contribution calendar."""
import datetime as dt, json, os, sys, urllib.request

USER = sys.argv[1]
TOKEN = os.environ["GH_TOKEN"]

def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req))["data"]

created = dt.datetime.fromisoformat(
    gql("query($u:String!){user(login:$u){createdAt}}", u=USER)["user"]["createdAt"].replace("Z", "+00:00")
)
now = dt.datetime.now(dt.timezone.utc)
days = {}
start = created
while start < now:
    end = min(start + dt.timedelta(days=365), now)
    cal = gql(
        "query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t)"
        "{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}",
        u=USER, f=start.isoformat(), t=end.isoformat(),
    )["user"]["contributionsCollection"]["contributionCalendar"]
    for w in cal["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]
    start = end

dates = sorted(days)
total = sum(days.values())
fmt = lambda s: dt.date.fromisoformat(s).strftime("%b %-d")

# longest streak
best, best_range, run, run_start = 0, None, 0, None
for d in dates:
    if days[d]:
        run_start = run_start if run else d
        run += 1
        if run > best:
            best, best_range = run, (run_start, d)
    else:
        run = 0

# current streak (today may still be empty)
cur, cur_end = 0, None
idx = len(dates) - 1
if idx >= 0 and days[dates[idx]] == 0:
    idx -= 1
while idx >= 0 and days[dates[idx]]:
    cur_end = cur_end or dates[idx]
    cur += 1
    idx -= 1
cur_range = f"{fmt(dates[idx + 1])} - {fmt(cur_end)}" if cur else "No active streak"
best_range = f"{fmt(best_range[0])} - {fmt(best_range[1])}" if best else "-"
since = dt.date.fromisoformat(dates[0]).strftime("%b %-d, %Y") + " - Present"

BLUE, TEXT, MUTED, BG, LINE, FIRE = "#58a6ff", "#e6edf3", "#8b949e", "#0d1117", "#21262d", "#ff7b54"
W, H = 240, 300
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
<g text-anchor="middle">
  <text x="120" y="44" font-size="28" font-weight="700" fill="{BLUE}">{total}</text>
  <text x="120" y="66" font-size="13" fill="{TEXT}">Total Contributions</text>
  <text x="120" y="83" font-size="11" fill="{MUTED}">{since}</text>
  <line x1="40" y1="100" x2="200" y2="100" stroke="{LINE}"/>
  <circle cx="120" cy="140" r="27" fill="none" stroke="{BLUE}" stroke-width="4"/>
  <path d="M120 103c4 5 7 8 7 12a7 7 0 0 1-14 0c0-3 2-5 3-7 1 3 2 4 4 4-1-3-1-6 0-9z" fill="{FIRE}"/>
  <text x="120" y="149" font-size="24" font-weight="700" fill="{TEXT}">{cur}</text>
  <text x="120" y="188" font-size="13" font-weight="700" fill="{BLUE}">Current Streak</text>
  <text x="120" y="205" font-size="11" fill="{MUTED}">{cur_range}</text>
  <line x1="40" y1="220" x2="200" y2="220" stroke="{LINE}"/>
  <text x="120" y="252" font-size="24" font-weight="700" fill="{BLUE}">{best}</text>
  <text x="120" y="272" font-size="13" fill="{TEXT}">Longest Streak</text>
  <text x="120" y="289" font-size="11" fill="{MUTED}">{best_range}</text>
</g>
</svg>
'''
os.makedirs("dist", exist_ok=True)
open("dist/streak.svg", "w").write(svg)
print(total, cur, cur_range, best, best_range)
