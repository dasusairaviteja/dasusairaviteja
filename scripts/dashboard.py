"""Render the real GitHub calendar as a GitHub-dark SVG dashboard."""
from html import escape
import datetime as dt
from pathlib import Path

def render_dashboard(days, total, active, longest, busiest, collection, stars):
    days = sorted(days, key=lambda d: d['date'])
    def text(x,y,s,size=18,color='#c9d1d9',font='Arial, sans-serif'):
        return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-family="{font}">{escape(str(s))}</text>'
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="960" height="430" viewBox="0 0 960 430" role="img" aria-label="Real GitHub contribution activity"><rect x="1" y="1" width="958" height="428" rx="12" fill="#161b22" stroke="#30363d"/>'
    svg+=text(30,34,'GITHUB / ACTIVITY SNAPSHOT',12,'#58a6ff')+text(30,79,'A year of building, one square at a time.',31,'#f0f6fc','Georgia, serif')
    metrics=[('CONTRIBUTIONS',total),('ACTIVE DAYS',active),('LONGEST STREAK',str(longest)+' days'),('BUSIEST DAY',busiest['contributionCount'] if busiest else 0)]
    for i,(label,value) in enumerate(metrics):
        x=34+i*232;svg+=text(x,123,label,12,'#58a6ff')+text(x,164,value,32,'#f0f6fc','Georgia, serif')
    start=dt.date.fromisoformat(days[0]['date']);offset=(start.weekday()+1)%7
    maxval=max(d['contributionCount'] for d in days)
    colors=['#161b22','#0e4429','#006d32','#26a641','#39d353']
    for day in days:
        date=dt.date.fromisoformat(day['date']);n=(date-start).days+offset
        count=day['contributionCount'];level=0 if count==0 else min(4,1+int(count/max(1,maxval)*3))
        svg+=f'<rect x="{34+(n//7)*16}" y="{195+(n%7)*16}" width="12" height="12" rx="2" fill="{colors[level]}"><title>{day["date"]}: {count} contributions</title></rect>'
    svg+=text(34,330,f'{days[0]["date"]} — {days[-1]["date"]} · GitHub-visible contributions',13)
    peak=busiest['date'] if busiest else 'none';svg+=text(34,352,f'Busiest date: {peak} · Refreshed {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M UTC}',13)
    svg+='<path d="M30 369H930" stroke="#30363d"/>'
    line=f"Commits: {collection['totalCommitContributions']}     PRs: {collection['totalPullRequestContributions']}     Issues: {collection['totalIssueContributions']}     Public repository stars: {stars}"
    svg+=text(34,401,line,18)+'</svg>'
    Path('assets/activity-dashboard.svg').write_text(svg)
