import glob
import os
from PIL import Image

def system(s):
    print s
    os.system(s)

g=glob.glob('*.png')+glob.glob('*.jpg')

for f in g:
    if '_th' in f: continue
    im=Image.open(f)
    print f,im.size
    width,height=im.size
    if width>height:
        sqsize=height
        xoffset=(width-height)/2
        yoffset=0
    else:
        sqsize=width
        yoffset=(height-width)/2
        xoffset=0
    system(('convert -extract %ix%i+%i+%i -geometry 400x400! '+f+' '+f[:-4]+'_th.png') % (sqsize,sqsize,xoffset,yoffset))
    
