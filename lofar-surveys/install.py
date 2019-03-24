#!/usr/bin/python

import os

INSTALLDIR='/home/mjh/lofar-surveys'

os.system('cp lofar.py '+INSTALLDIR)
os.system('rsync -avu templates '+INSTALLDIR)
os.system('rsync -avu static '+INSTALLDIR)
