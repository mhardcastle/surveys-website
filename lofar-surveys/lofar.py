from flask import Flask,render_template,request,send_from_directory
from flask_basicauth import BasicAuth

import os
import glob

app = Flask(__name__)

if os.path.isdir('/Users/mayahorton'):
    laptop=True
    rootdir='/Users/mayahorton/LOFAR/surveys-website/lofar-surveys'
elif os.path.isdir('/home/mjh/git/surveys-website'):
    laptop=True
    rootdir='/home/mjh/git/surveys-website/lofar-surveys'
else:
    laptop=False
    rootdir='/home/mjh/lofar-surveys'

if not laptop:
    from flaskext.mysql import MySQL
    mysql = MySQL()

authlines=open(rootdir+'/.authfile').readlines()
for l in authlines:
    keyword,value=l.rstrip().split()
    app.config[keyword]=value

basic_auth = BasicAuth(app)
if not laptop:
    mysql.init_app(app)

tabs=['The Surveys','For Astronomers','Publications','Data Releases','For Collaborators']
location=['index.html','astronomers.html','publications.html','releases.html','collaborators.html']
label=[l.replace('.html','') for l in location]
nav=list(zip(tabs,location,label))[::-1]

extras=['status.html','progress.html','co-observing.html']

@app.route('/')
def index():
    return render_template('index.html',nav=nav)

# downloads from downloads directory
@app.route('/downloads/<path:path>')
@basic_auth.required
def get_file(path):
    """Download a file."""
    return send_from_directory(rootdir+'/downloads', path, as_attachment=True)

@app.route('/fields.html')
def fields():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('select id,status,ra,decl,username,clustername,nodename,location,priority,start_date,end_date,gal_l,gal_b from fields order by id')
    data=cursor.fetchall()
    conn.close()
    return render_template('fields.html',data=data,nav=nav)

@app.route('/observations.html')
def observations():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('select * from observations order by id')
    data=cursor.fetchall()
    conn.close()
    return render_template('observations.html',data=data,nav=nav)


@app.route('/collaborators.html')
@basic_auth.required
def collaborators():
    return render_template('collaborators.html',nav=nav)

@app.route('/dr2.html')
@basic_auth.required
def dr2():
    return render_template('dr2.html',nav=nav)

@app.route('/hetdex.html')
@basic_auth.required
def hetdex():
    return render_template('hetdex.html',nav=nav)

@app.route('/legacy.html')
@basic_auth.required
def legacy():
    return render_template('legacy.html',nav=nav)

#default handler for static pages

def render():
    return render_template(request.endpoint+'.html',nav=nav)

for _,location,label in nav:
    try:
        app.add_url_rule('/'+location,label,render)
    except AssertionError:
        pass

for location in extras:
    label=location.replace('.html','')
    try:
        app.add_url_rule('/'+location,label,render)
    except AssertionError:
        pass

    
if __name__=='__main__':
    app.run(debug=True)
