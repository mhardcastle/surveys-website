from flask import Flask,render_template,request,send_from_directory,send_file
from flask_basicauth import BasicAuth
from flask_misaka import Misaka

from astropy.coordinates import SkyCoord,get_icrs_coordinates,name_resolve
from astropy import units as u

from lbcs2fits import generate_table, filter_table

import os
import glob
import numpy as np
import io

factor=180.0/np.pi

def sepn(r1,d1,r2,d2):
    """
    Calculate the separation between 2 sources, RA and Dec must be
    given in radians. Returns the separation in radians
    """
    # NB slalib sla_dsep does this
    # www.starlink.rl.ac.uk/star/docs/sun67.htx/node72.html
    cos_sepn=np.sin(d1)*np.sin(d2) + np.cos(d1)*np.cos(d2)*np.cos(r1-r2)
    sepn = np.arccos(cos_sepn)
    # Catch when r1==r2 and d1==d2 and convert to 0
    sepn = np.nan_to_num(sepn)
    return sepn

def separation(ra1,dec1,ra2,dec2):
    # same as sepn but in degrees
    return factor*sepn(ra1/factor,dec1/factor,ra2/factor,dec2/factor)

# Next codes adapted from Neal J's scripts

def corr_astro (a1,ra1col,dec1col,a2,ra2col,dec2col,dist):
    a1 = np.array([a1]) if a1.ndim == 1 else a1
    a2 = np.array([a2]) if a2.ndim == 1 else a2
    c1 = SkyCoord(np.asarray(a1[:,ra1col],dtype='f')*u.degree,\
                  np.asarray(a1[:,dec1col],dtype='f')*u.degree)
    c2 = SkyCoord(np.asarray(a2[:,ra2col],dtype='f')*u.degree,\
                  np.asarray(a2[:,dec2col],dtype='f')*u.degree)
    c = c2.search_around_sky (c1,dist*u.deg)
    a = np.asarray(np.column_stack((c[0],c[1],c[2])),dtype='f')
    return a

def cat2html (ra=240.,dec=55.,radius=3.0,catname='lbcs_stats.sum',wd='/data/lofar/lbcs'):
    filetypes = ['L.png','R.png','.pic','.log','_plot.ps']
    labels = ['PL','PR','D','L','F']
    filedirs = ['pngfiles','pngfiles','picfiles','logfiles','frifiles']
    dir_key = np.loadtxt(wd+'/dir_key',dtype='str')
    lbcs = np.loadtxt(wd+'/'+catname,dtype='str')
    lbcs_coord = np.asarray(lbcs[:,-2:],dtype='f')
    in_coord = np.array([[ra,dec]])
    a = corr_astro (in_coord,0,1,lbcs_coord,0,1,radius)
    data=[]
    for i in a:
        line=[]
        links=[]
        l,dist = lbcs[int(i[1])], i[2]
        epoch_idx = np.argwhere(dir_key[:,1]==l[0])[0][0]
        epoch_l = dir_key[epoch_idx,0]
        for j in l:
            line.append("%s"%j)
        line.append('%.5f'%dist)
        for j in range (len(filetypes)):
            line.append(labels[j])
            links.append("/public/lbcs/%s/%s/%s%s" % (epoch_l,filedirs[j],l[0],filetypes[j]))
        data.append((line+links))
    return data
                    
def render_deepfield(fieldname,nav=None):
    if fieldname=='bootes':
        name="Bo&ouml;tes"
    elif fieldname=='en1':
        name="ELAIS-N1"
    else:
        name=fieldname.capitalize()
    dir='/beegfs/lofar/deepfields/data_release/'+fieldname+'/'
    lines=open(dir+'README.txt').readlines()
    fd=[]
    started=False
    for l in lines:
        if l[0]=='=' and not started:
            started=True
        elif l[0]=='=' and started:
            break
        elif started:
            if l[0]=='-':
                bits=l[2:].split(' : ')
                if len(bits)==2:
                    fd.append((fieldname+'_'+bits[0],bits[1]))
    return render_template('deepfield_catalogue.html',field=fieldname,name=name,fd=fd,nav=nav)
                    

app = Flask(__name__)
Misaka(app,autolink=True,tables=True,math=True,math_explicit=True)

laptop=False
try:
    rootdir=os.environ['LOFAR_ROOT']
except:
    rootdir='/home/mjh/lofar-surveys'

print 'Working in',rootdir
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

extras=['status.html','progress.html','co-observing.html','lotss-tier1.html','news.html','lbcs.html']

@app.route('/')
def index():
    return render_template('index.html',nav=nav)

@app.route('/hips/<path:path>')
@basic_auth.required
def get_hips(path):
    if path[-1]=='/':
        path+='index.html'
    return send_from_directory(rootdir+'/hips', path, as_attachment=False)

@app.route('/public_hips/<path:path>')
@basic_auth.required
def get_public_hips(path):
    if path[-1]=='/':
        path+='index.html'
    return send_from_directory(rootdir+'/public_hips', path, as_attachment=False)

# downloads from downloads directory
@app.route('/downloads/<path:path>')
@basic_auth.required
def get_file(path):
    # download from PRIVATE area
    # first rewrite paths...
    bits=os.path.split(path)
    if 'deepfields' in path:
        for prefix in ['en1','lockman','bootes']:
            if bits[1].startswith(prefix+'_'):
                path=bits[0]+'/'+bits[1].replace(prefix+'_','')
            
    if path.endswith('.html'):
        return send_from_directory(rootdir+'/downloads', path, as_attachment=False)
    elif path.endswith('.md'):
        data=open(rootdir+'/downloads/'+path).read()
        return render_template('deepfields_md.html',mkd=data,name=bits[1])
    else:
        return send_from_directory(rootdir+'/downloads', path, as_attachment=True,attachment_filename=bits[1])

# downloads from public directory
@app.route('/public/<path:path>')
def get_public_file(path):
    """Download a file."""
    if path.endswith('.html') or path.endswith('.png'):
        return send_from_directory(rootdir+'/public', path, as_attachment=False)
    elif path.endswith('/'):
        return send_from_directory(rootdir+'/public', path+'index.html', as_attachment=False)
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
    cursor.execute('select id,field,status,project_code,integration,dt,nchan,nsb,date,calibrator_id,location,calibrator_dt,calibrator_nchan,calibrator_nsb,calibrator_name,calibrator_date,bad_baselines,priority from observations order by id')
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

@app.route('/credits.html')
def credits():
    files=[]
    links=[]
    for l in open('static/logos/files.txt').readlines():
        bits=l.rstrip().split()
        files.append(bits[0])
        links.append(bits[1])
    return render_template('credits.html',nav=nav,ilink=list(zip(files,links)))

@app.route('/gallery_preview.html')
def gallery_preview():
    ilist=glob.glob('static/gallery/*_th.png')
    ilist.sort(key=os.path.getmtime,reverse=True)
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

@app.route('/lba.html')
@basic_auth.required
def lba():
    return render_template('lba.html',nav=nav)

@app.route('/gama.html')
@basic_auth.required
def gama():
    return render_template('gama.html',nav=nav)

@app.route('/deepfields.html')
@basic_auth.required
def deepfields():
    return render_template('deepfields.html',nav=nav)

@app.route('/deepfields_bootes.html')
@basic_auth.required
def df_bootes():
    return render_deepfield('bootes',nav=nav)

@app.route('/deepfields_lockman.html')
@basic_auth.required
def df_lockman():
    return render_deepfield('lockman',nav=nav)

@app.route('/deepfields_en1.html')
@basic_auth.required
def df_en1():
    return render_deepfield('en1',nav=nav)

@app.route('/dr2.html')
@basic_auth.required
def dr2():
    return render_template('dr2.html',nav=nav)

@app.route('/widefields.html')
@basic_auth.required
def widefields():
    return render_template('widefields.html',nav=nav)

@app.route('/lbcs-search.html',methods=['GET'])
def lbcs_search():
    error=None
    ra=request.args.get('ra')
    dec=request.args.get('dec')
    radius=request.args.get('radius')
    if ra is None or dec is None or radius is None:
        error='Arguments not supplied'
    else:
        try:
            ra=float(ra)
            dec=float(dec)
            radius=float(radius)
        except Exception as e:
            error=str(e)
            print error
        if ra<0 or ra>360 or dec<0 or dec>90:
            error='Co-ordinates out of range'
    if error:
        return render_template('lbcs-search-error.html',error=error,nav=nav)
    
    data=cat2html(ra=ra,dec=dec,radius=radius)
    print data
    return render_template('lbcs-search.html',ra=ra,dec=dec,data=data,radius=radius,nav=nav)

@app.route('/lbcs-search.fits',methods=['GET'])
def lbcs_fits():
    error=None
    ra=request.args.get('ra')
    dec=request.args.get('dec')
    radius=request.args.get('radius')
    if ra is None or dec is None or radius is None:
        error='Arguments not supplied'
    else:
        try:
            ra=float(ra)
            dec=float(dec)
            radius=float(radius)
        except Exception as e:
            error=str(e)
            print error
        if ra<0 or ra>360 or dec<0 or dec>90:
            error='Co-ordinates out of range'
    if error:
        return render_template('lbcs-search-error.html',error=error,nav=nav)

    t=filter_table(ra,dec,radius)
    mem=io.BytesIO()
    t.write(mem,format='fits')
    mem.seek(0)
    return send_file(
        mem,
        mimetype='application/fits',
        attachment_filename='lbcs.fits',
        as_attachment=True,
        cache_timeout=0,
    )

@app.route('/field-search.html',methods=['POST'])
@basic_auth.required
def field_search():
    # code modified from find_pos
    offset=4
    pos=request.form.get('pos')
    try:
        sc=get_icrs_coordinates(pos)
    except name_resolve.NameResolveError as n:
        sc=None
    if sc is not None:
        ra=sc.ra.value
        dec=sc.dec.value
        with mysql.connect() as conn:
            cur=conn # what??
            cur.execute('select fields.id,ra,decl,fields.status,observations.date from fields left join observations on observations.field=fields.id')
            results=cur.fetchall()

        ras=[r[1] for r in results]
        decs=[r[2] for r in results]
        fsc=SkyCoord(ras,decs,unit='deg')
        seps=sc.separation(fsc).value

        rs=[]
        for i,r in enumerate(results):
            if seps[i]>offset: continue
            id=r[0]
            rra=r[1]
            rdec=r[2]
            status=r[3]
            obsdate=r[4]
            if status=='Archived':
                url="/downloads/DR2/fields/%s/image_full_ampphase_di_m.NS_shift.int.facetRestored.fits" % id
            else:
                url=None
            rn=(id,rra,rdec,status,('%.2f' % seps[i]),url,obsdate)
            rs.append(rn)

        return render_template('field-search.html',nav=nav,pos=pos,ra=sc.ra.value,dec=sc.dec.value,results=rs)
    else:
        return render_template('dr2-search-error.html',error=n,nav=nav,pos=pos)

@app.route('/dr2-search.html',methods=['POST'])
@basic_auth.required
def dr2_search():
    # code modified from find_pos
    offset=2
    pos=request.form.get('pos')
    try:
        sc=get_icrs_coordinates(pos)
    except name_resolve.NameResolveError as n:
        sc=None
    if sc is not None:
        ra=sc.ra.value
        dec=sc.dec.value
        with mysql.connect() as conn:
            cur=conn # what??
            cur.execute('select id,ra,decl from fields where dr2>0 and dr2_final_mosaic>0')
            results=cur.fetchall()

        ras=[r[1] for r in results]
        decs=[r[2] for r in results]
        fsc=SkyCoord(ras,decs,unit='deg')
        seps=sc.separation(fsc).value

        rs=[]
        for i,r in enumerate(results):
            if seps[i]>offset: continue
            id=r[0]
            url="/downloads/DR2/mosaics/%s/" % id
            if not os.path.isdir(rootdir+url):
                continue
            rra=r[1]
            rdec=r[2]
            rn=(id,rra,rdec,('%.2f' % seps[i]),url)
            rs.append(rn)

        return render_template('dr2-search.html',nav=nav,pos=pos,ra=sc.ra.value,dec=sc.dec.value,results=rs)
    else:
        return render_template('dr2-search-error.html',error=n,nav=nav,pos=pos)

@app.route('/dynspec-search.html',methods=['POST'])
@basic_auth.required
def dynspec_search():
    pos=request.form.get('pos')
    offset=float(request.form.get('radius'))
    
    try:
        sc=get_icrs_coordinates(pos)
    except name_resolve.NameResolveError as n:
        sc=None
    if sc is not None:
        ra=sc.ra.value
        dec=sc.dec.value
        with mysql.connect() as conn:
            cur=conn # what??
            cur.execute('select name,field,obsid,type,ra,decl,filename from spectra where type!="Off"')
            results=cur.fetchall()

        ras=[r[4] for r in results]
        decs=[r[5] for r in results]
        fsc=SkyCoord(ras,decs,unit='deg')
        seps=sc.separation(fsc).value

        rs=[]
        for i,r in enumerate(results):
            if seps[i]>offset: continue
            rn=r+('%.2f' % seps[i],)
            rs.append(rn)

        return render_template('dynspec-search.html',offset=offset,nav=nav,pos=pos,ra=sc.ra.value,dec=sc.dec.value,results=rs)
    else:
        return render_template('dr2-search-error.html',error=n,nav=nav,pos=pos)

@app.route('/dynspecs.html')
@basic_auth.required
def dynspecs():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute('select fields.id,fields.ra,fields.decl,observations.id,observations.date,fields.end_date from observations right join fields on fields.id=observations.field where fields.status="Archived" and observations.status="DI_Processed" order by fields.ra,observations.date')
    data=cursor.fetchall()
    conn.close()
    return render_template('dynspecs.html',data=data,nav=nav)

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
