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

os.chdir(rootdir)
    
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

tabs=['Welcome','The Surveys','Image Gallery','For Astronomers','Publications','Data Releases','For Collaborators']
location=['index.html','surveys.html','gallery_preview.html','astronomers.html','publications.html','releases.html','collaborators.html']
label=[l.replace('.html','') for l in location]
nav=list(zip(tabs,location,label))[::-1]

extras=['status.html','progress.html','co-observing.html','lotss-tier1.html','news.html','credits.html']

@app.route('/')
def index():
    return render_template('index.html',nav=nav)

# downloads from downloads directory
@app.route('/downloads/<path:path>')
@basic_auth.required
def get_file(path):
    """Download a file."""
    return send_from_directory(rootdir+'/downloads', path, as_attachment=True)

# downloads from public directory
@app.route('/public/<path:path>')
def get_public_file(path):
    """Download a file."""
    if '.html' in path:
        return send_from_directory(rootdir+'/public', path, as_attachment=False)
    else:
        return send_from_directory(rootdir+'/public', path, as_attachment=True)

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

@app.route('/reprocessing.html')
def reprocessing():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('select id,fields,ra,decl,size,mask,frqavg,timeavg,extract_version,selfcal_version,extract_status,selfcal_status,priority from reprocessing order by id')
    data=cursor.fetchall()
    conn.close()
    return render_template('reprocessing.html',data=data,nav=nav)

@app.route('/gallery_preview.html')
def gallery_preview():
    ilist=glob.glob('static/gallery/*_th.png')
    descs=[]
    links=[]
    for i,fname in enumerate(ilist):
        textfile=fname.replace('_th.png','.txt')
        link=fname.replace('_th.png','.png').replace('+','%2b')
        if os.path.isfile(textfile):
            with open(textfile) as infile:
                description=infile.read().decode('utf8').rstrip()
        else:
            description='A mysterious LOFAR image!'
        cut=80
        if len(description)>cut:
            while cut<len(description) and description[cut]!=' ':
                cut+=1
            description=description[:cut]+' ...'
        descs.append(description)
        links.append(link)
    return render_template('gallery_preview.html',nav=nav,idesc=list(zip(ilist,descs,links)))


@app.route('/gallery.html')
def gallery():
    ilist=[f for f in (glob.glob('static/gallery/*.png')+glob.glob('static/gallery/*.jpg')) if '_th' not in f]
    filename=request.args.get('file')
    if filename is not None:
        filename.replace('_th.png','.png')
        imageno=ilist.index(filename)
    else:
        imageno=request.args.get('image')
        if imageno is None:
            imageno=0
        else:
            imageno=int(imageno)
    descs=[]
    for i,fname in enumerate(ilist):
        textfile=fname[:-4]+'.txt'
        if os.path.isfile(textfile) and i==imageno:
            with open(textfile) as infile:
                description=infile.read().decode('utf8').rstrip()
        else:
            description='A mysterious LOFAR image!'
        descs.append(description)
    if imageno==0:
        last=len(ilist)-1
        next=1
    elif imageno==len(ilist)-1:
        next=0
        last=imageno-1
    else:
        next=imageno+1
        last=imageno-1
        
    return render_template('gallery.html',nav=nav,image=ilist[imageno],desc=descs[imageno],last=last,next=next)
    

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
    app.run(debug=True,host='0.0.0.0')
