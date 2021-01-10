from ghapi import GhApi
import requests, json
from fastcore.xtras import repr_dict,obj2dict
github_access_token = '7386ec7242c169af34743d690a253a4d6cc724aa'
api = GhApi(token = github_access_token)
#print(api.users.get_authenticated())
#events = api('/users/{username}/events?per_page={perpage}&page={page}','GET',route=dict(username='ShreyasKudari', perpage='30', page=''))
# URL = "https://api.github.com/users/{}/events".format('ShreyasKudari')
# params = {
#     'per_page': 100,
#     'page': 3
# }
# events = requests.get(url=URL,params = params, headers = {'Authorization': 'token %s' % github_access_token})
commits = 0
name = 'Shreyas Kudari'
username = 'shreyaskudari'
page = 1
forked_repos = {}
forks = 0
collaborators = {}
repos = {}
times = {}
streaks = 0
max_streak = 0
streak_day = 0
streak_month = 0
streak_year = 0
PRs = 0
issues = {
    'opened': 0,
    'closed': 0
}
for i in range(0,10):
    events = api('/users/{username}/events?per_page={perpage}&page={page}','GET',route=dict(username='ShreyasKudari', perpage='30', page=page))
    if events is None: 
        break
    dict_events = obj2dict(events)
    for event in dict_events:
        date = event['created_at'].split('T')[0].split('-')
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])

        if streaks == 0:
            streaks = 1
            streak_day = day
            streak_month = month
            streak_year = year
        elif streak_month == month:
            if streak_day-day == 1:
                streaks+=1
            else:
                streaks = 1
            streak_day = day

        else:
            if streak_day==1 and (day==31 or day==30):
                streaks+=1
            else:
                streaks = 1
            streak_day = day
            streak_month = month

        if max_streak<streaks:
             max_streak=streaks

        if event['repo']['name'] in repos:
            repos[event['repo']['name']]+=1
        else:
            repos[event['repo']['name']]=1

        if event['type'] == "PushEvent":
            for commit in event['payload']['commits']:
                if (commit['author']['name'].lower() == name.lower() or commit['author']['name'].lower() == username.lower()) and commit['distinct']:
                    commits+=1
                elif (commit['author']['name'].lower() != name.lower()) and (commit['author']['name'].lower() != username.lower()):
                    if commit['author']['name'].lower() in collaborators:
                        collaborators[commit['author']['name'].lower()]+=1
                    else:
                         collaborators[commit['author']['name'].lower()]=1

        elif event['type'] == "IssuesEvent":
            if event['payload']['action'] == 'opened':
                issues['opened']+=1
            elif event['payload']['action'] == 'closed':
                issues['closed']+=1
        elif event['type'] == "PullRequestEvent" and event['payload']['action'] == 'opened':
            PRs+=1
        elif event['type'] == "ForkEvent":
            forked_repos[event['payload']['forkee']['full_name']]=1
            forks+=1


    page+=1


fav_colab = None
fav_repo = None
max_repo = 0
max_commits=0

#get favorite collaborator
for colab in collaborators:
    if collaborators[colab]>max_commits:
        fav_colab=colab
        max_commits=collaborators[colab]

#get favorite repository
for repo in repos:
    if repos[repo]>max_repo:
        fav_repo = repo
        max_repo = repos[repo]
# print(collaborators)
print("In the past 90 days, you made {} commits!".format(commits))
if fav_colab is not None:
    print("Your fav collaborator in the past 90 days was {}!".format(fav_colab))
if fav_colab is not None:
    print("Your fav repository in the past 90 days was {}!".format(fav_repo))
if issues['opened'] > 0:
    print("You opened {} issues".format(issues['opened']))
if issues['closed'] > 0:
    print("You closed {} issues!!".format(issues['closed']))
if forks>0:
    print("You forked {} repos".format(forks))
    print(forked_repos)
print("Your longest push streak was {} days!".format(max_streak))
# print(page-1)
# print(api.rate_limit.get())