#!/usr/bin/env python
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
import io

def generate_table():

    lines=open('/data/lofar/lbcs/lbcs_stats.sum').readlines()

    bitsa=[l.rstrip().split() for l in lines if l[0]!='#']

    cols=[]
    for c in range(11):
        cols.append([])

    for b in bitsa:
        for c in range(11):
            if c in [8,9,10]:
                cols[c].append(float(b[c]))
            else:
                cols[c].append(b[c])

    t=Table([cols[0],cols[9],cols[10]]+cols[3:9],names=['Observation','RA','DEC','Date','Time','Goodness','Flags','FT_Goodness','Quality'])
    return t

def filter_table(ra,dec,radius=2.0):
    t=generate_table()
    scr=SkyCoord(ra*u.deg,dec*u.deg)
    sc=SkyCoord(t['RA']*u.deg,t['DEC']*u.deg)
    sep=sc.separation(scr)
    return t[sep.value<radius]

if __name__=='__main__':
    import sys
    t=filter_table(float(sys.argv[1]),float(sys.argv[2]))
    mem=io.BytesIO()
    t.write(mem,overwrite=True,format='fits')
    
