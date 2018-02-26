import urllib2
import json
import time
import collections
from flask import Flask
from flask import render_template
from datetime import datetime
from tinydb import TinyDB, Query


app = Flask(__name__) # instantiate Flask

# route for homepage
@app.route('/')
def index():

    stats = getStatsFromDb(getCurrentMonth())

    return render_template('patch.html', stats = stats, month = getCurrentMonth())

# REST endpoint for fetching stats by month
@app.route('/month/<month>')
def month():
    file = open("stats/" + month + ".json", "r")
    jsonText =  file.read()
    response = app.response_class(
        response=jsonText,
        status=200,
        mimetype='application/json'
    )
    return response

# loop through participants
def getParticipants():

    file = open('participants.json', "r")
    jsonText =  file.read()
    response = json.loads(jsonText)
    return response

# get user stats using Gerrit API
def getUserStats(username):
    
    if username!="":
        # concatenate url
        url = "https://gerrit.wikimedia.org/r/changes/?q=owner:" + username;
        
        request = urllib2.Request(url)
        result = urllib2.urlopen(request)
        jsonArray = result.read()

        jsonArray = jsonArray.replace(")]}'", ""); # Fix this error in headers of json tree
        return json.loads(jsonArray);

# create json file for monthly stats
def createJsonFile(jsonArray):
    filename = getCurrentMonth()
    with open('stats/' + filename + '.json', 'w') as f:
        f.write(str(jsonArray))  # convert result to string ad save it

# get current month
def getCurrentMonth():
    currentMonth = time.strftime("%Y-%m"); # eg 2018-02 
    return currentMonth 

# cron job for fetching and saving stats, for now fires in HTTP
@app.route('/cron')
def cronTask():
    # load and save participants list
    participants = getParticipants()

    # loop through participants
    for participant in participants:

        username = participant['username']
        patches = getUserStats(username)

        # loop through participant patches
        for patch in patches:

            # prepare patch dictionary
            patch['username'] = username;
            patch['name'] = participant['name'];
            patch['country'] = participant['country'];

            # persist patch to db
            db = getDb()
            db.insert(patch)

    # output the db as json
    output = db.all();

    response = app.response_class(
        response=json.dumps(output),
        status=200,
        mimetype='application/json'
    )

    return response 

# get monthly stats from db
def getStatsFromDb( month ):
    Patch = Query()
    db = getDb()

    stats = db.search(Patch.created.test(filterMonth, month))
    return stats

# custom Flask filter for datetimeformating
@app.template_filter()
def datetimeformat(value, format):

    return datetime.strptime(value, format)

# db object to be used indepently
def getDb():
    # setting the tinydb location
    db = TinyDB('db/db.json')
    return db

# get the list of patch submitters
def getSubmitters():

# filter month
def filterMonth(string, month):
    if month in string: 
        return True
    else:
        return False 

if __name__ == '__main__':
    app.run()