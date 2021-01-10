from flask import Flask, request, g, session, redirect, url_for, render_template
from flask import render_template_string, jsonify
from flask_github import GitHub

from ghapi import GhApi
from fastcore.xtras import obj2dict
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URI = 'sqlite:///backend\\github-flask.db'
SECRET_KEY = 'development key'
DEBUG = True
GITHUB_CLIENT_ID = '8b069af36a352b27c01c'
GITHUB_CLIENT_SECRET = 'f3d775d909b27caa635fae3eb9c7700287a3919e'
CORS_SUPPORTS_CREDENTIALS = True

app = Flask(__name__)
app.config.from_object(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
github = GitHub(app) #using for OAuth


engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(String(255))
    avatar_url = Column(String(255))
    login = Column(String(255))
    name = Column(String(255))
    def __init__(self, github_access_token):
        self.github_access_token = github_access_token


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response

@app.route('/')
def index():
    return render_template("index.html")
@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize(scope='user,repo')
    else:
        return render_template("home.html")

@app.route('/logincheck')
def logincheck():
    if session.get('user_id', None) is None:
        return jsonify({'status': 'False'})
    else:
        return jsonify({'status': 'True'})

@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    #TODO
    # index_url = 'C:\\Users\\Shreyas Kudari\\Documents\\semester5\\Project_nwHacks2020\\FrontEnd\\home.html'
    # get_data_url = "C:\\Users\\Shreyas Kudari\\Documents\\semester5\\Project_nwHacks2020\\FrontEnd\\home.html"

    if access_token is None:
        return render_template("index.html")

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)

    user.github_access_token = access_token
    g.user = user
    db_session.commit()

    session['user_id'] = user.id
    return render_template("home.html")
 
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return 'logged out'

@app.route('/get_data')
def get_data():
    g.api = GhApi(token = g.user.github_access_token) #using for data
    data = {}
    userdata = obj2dict(g.api.users.get_authenticated())
    g.user.avatar_url = userdata["avatar_url"]
    g.user.username = userdata["login"]
    g.user.name = userdata["name"]
    data["User_Info"] = {
                    'avatar_url': g.user.avatar_url,
                    'login': g.user.username,
                    'name': g.user.name
                }
                
    data["Git_Info"] = get_commits()
    return jsonify(data)

def get_commits():
    #TODO
    #get events
    g.commits = 0
    page = 1
    g.streaks = 0
    g.max_streak = 0
    g.streak_day = 0
    g.streak_month = 0
    g.streak_year = 0
    g.times = {}
    g.collaborators = {}
    g.repos = {}
    g.forked_repos = {}
    g.forks = 0
    g.PRs = 0
    g.issues = {
        'opened': 0,
        'closed': 0
    }
    for i in range(0,10):
        events = g.api('/users/{username}/events?per_page={perpage}&page={page}','GET',route=dict(username=g.user.username, perpage='30', page=page))
        if events is None: 
            break
        dict_events = obj2dict(events)
        for event in dict_events:
            logic(event)
        page+=1
    g.fav_colab = None
    g.fav_repo = None
    g.fav_time = None
    g.max_repo = 0
    g.max_commits=0
    g.max_push_count = 0
    g.max_push_hour = None
    
    for colab in g.collaborators:
        if g.collaborators[colab]>g.max_commits:
            g.fav_colab=colab
            g.max_commits=g.collaborators[colab]

    #get favorite repository
    for repo in g.repos:
        if g.repos[repo]>g.max_repo:
            g.fav_repo = repo
            g.max_repo = g.repos[repo]
    #get favorite collaborator
    postprocessing()

    results = {}
    results["commits"] = g.commits
    results["fav_repo"] = g.fav_repo
    results["fav_colab"] = g.fav_colab
    results["issues_opened"] = g.issues['opened']
    results["issues_closed"] = g.issues['closed']
    results["PR_opened"] = g.PRs
    results["fork_count"] = g.forks
    results["forked_repos"] = g.forked_repos 
    results["push_streak"] = g.max_streak
    results["times"] = g.times
    results["favorite_time"] = g.fav_time
    return results

def postprocessing():
    #get favorite push time
    for hour in g.times:
        if g.times[hour]>g.max_push_count:
            g.max_push_hour = hour
            g.max_push_count = g.times[hour]
    fav_hour = int(g.max_push_hour)
    if (fav_hour >= 0 and fav_hour <= 3) or (fav_hour>=20 and fav_hour<=23):
        g.fav_time = "Night"
    elif (fav_hour >=4 and fav_hour<=12):
        g.fav_time = "Morning"
    else:
        g.fav_time = "Afternoon"


def logic(event):
    
    if event['repo']['name'] in g.repos:
        g.repos[event['repo']['name']]+=1
    else:
        g.repos[event['repo']['name']]=1

    if event['type'] == "PushEvent":
        get_streaks(event)
        push_event(event)

    elif event['type'] == "IssuesEvent":
        if event['payload']['action'] == 'opened':
            g.issues['opened']+=1
        elif event['payload']['action'] == 'closed':
            g.issues['closed']+=1
    elif event['type'] == "PullRequestEvent" and event['payload']['action'] == 'opened':
        g.PRs+=1
    elif event['type'] == "ForkEvent":
        g.forked_repos[event['payload']['forkee']['full_name']]=1
        g.forks+=1

def get_streaks(event):
    datetime = event['created_at'].split('T')
    date = datetime[0].split('-')
    time = datetime[1].split(':')[0]
    if time in g.times:
        g.times[time]+=1
    else: 
        g.times[time]=1
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])

    if g.streaks == 0:
        g.streaks = 1
        g.streak_day = day
        g.streak_month = month
        g.streak_year = year
    elif g.streak_month == month:
        if g.streak_day-day == 1:
            g.streaks+=1
        else:
            g.streaks = 1
        g.streak_day = day

    else:
        if g.streak_day==1 and (day==31 or day==30):
            g.streaks+=1
        else:
            g.streaks = 1
        g.streak_day = day
        g.streak_month = month

    if g.max_streak<g.streaks:
            g.max_streak=g.streaks

def push_event(event):
    for commit in event['payload']['commits']:
        if (commit['author']['name'].lower() == g.user.name.lower() or commit['author']['name'].lower() == g.user.username.lower()) and commit['distinct']:
            g.commits+=1
        elif (commit['author']['name'].lower() != g.user.name.lower()) and (commit['author']['name'].lower() != g.user.username.lower()):
            if commit['author']['name'].lower() in g.collaborators:
                g.collaborators[commit['author']['name'].lower()]+=1
            else:
                g.collaborators[commit['author']['name'].lower()]=1


if __name__=='__main__':
    init_db()
    app.run(host='127.0.0.1',port=5050, debug=True)
