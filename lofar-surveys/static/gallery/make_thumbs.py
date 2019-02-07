import glob
import os

g=glob.glob('*.png')

for f in g:
    if '_th' in f: continue
    os.system('convert -geometry 400x400! '+f+' '+f.replace('.png','_th.png'))
    
