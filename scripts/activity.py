"""Refresh public profile activity; never substitutes sample numbers on failure."""
from dashboard import render_dashboard
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.request


def api(url, payload=None):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-activity'}
    if payload is not None:
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def summarize(days):
    days = sorted(days, key=lambda d: d['date'])
    total = active = longest = streak = 0
    previous = None
    for day in days:
        date = dt.date.fromisoformat(day['date'])
        count = day['contributionCount']
        total += count
        if count:
            active += 1
            streak = streak + 1 if previous and date - previous == dt.timedelta(days=1) else 1
        else:
            streak = 0
        longest = max(longest, streak)
        previous = date
    busiest = max(days, key=lambda d: d['contributionCount']) if total else None
    return total, active, longest, busiest


def main():
    owner = os.environ['PROFILE_OWNER']
    query = '''query($login:String!){user(login:$login){contributionsCollection{startedAt endedAt totalCommitContributions totalIssueContributions totalPullRequestContributions contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
    response = api('https://api.github.com/graphql', {'query': query, 'variables': {'login': owner}})
    if response.get('errors'):
        raise RuntimeError('GitHub contribution query failed; previous assets retained')
    c = response['data']['user']['contributionsCollection']
    days = [d for w in c['contributionCalendar']['weeks'] for d in w['contributionDays']]
    if not days:
        raise RuntimeError('No calendar returned')
    total, active, longest, busiest = summarize(days)
    stars = 0
    page = 1
    while True:
        repos = api(f'https://api.github.com/users/{owner}/repos?type=owner&per_page=100&page={page}')
        stars += sum(r['stargazers_count'] for r in repos if not r['fork'])
        if len(repos) < 100:
            break
        page += 1
    peak = f"{busiest['date']} ({busiest['contributionCount']} contributions)" if busiest else 'No active day'
    render_dashboard(days, total, active, longest, busiest, c, stars)
    block = f'''<img src="assets/activity-dashboard.svg" alt="Real GitHub activity dashboard" width="100%" />

![Contribution snake](assets/contribution-snake.svg)

<details><summary>Activity figures and refresh details</summary>


| Contributions | Active days | Longest streak | Busiest day |
| :--- | :--- | :--- | :--- |
| {total} | {active} | {longest} days | {peak} |

| Commit contributions | Pull-request contributions | Issue contributions | Stars on owned public non-fork repositories |
| :--- | :--- | :--- | :--- |
| {c['totalCommitContributions']} | {c['totalPullRequestContributions']} | {c['totalIssueContributions']} | {stars} |

Calendar period: {days[0]['date']} to {days[-1]['date']}. GitHub-visible contribution data; stars are a current total, not a yearly count. Updated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. Scheduled daily; last successful update remains visible if a refresh fails.
'''
    block += '\n</details>\n'
    path = Path('README.md')
    text = path.read_text()
    text, count = re.subn(r'(?s)(<!-- ACTIVITY:START -->).*?(<!-- ACTIVITY:END -->)', lambda m: m[1]+'\n'+block+'\n'+m[2], text)
    if count != 1:
        raise RuntimeError('Expected one activity block')
    if not Path('assets/contribution-snake.svg').is_file():
        raise RuntimeError('Snake output missing')
    path.write_text(text)

if __name__ == '__main__':
    main()

