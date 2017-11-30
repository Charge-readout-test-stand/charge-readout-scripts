#!/usr/bin/env python
"""
This script calls takeData.takeData() in a loop. 
"""

import time
import takeData
import time
import os

# take struck data in a loop!
takeData.takeData(doLoop=True,n_hours=1) # set up the digitizer, take data

#is_running = True
#
#fname = "/home/teststand/2017_11_13_SiPM_Run/overnight_new_bias/tier0/logger.txt"
#
#
#while True:
#    if os.path.exists(fname):
#        print 'script is running, wait for 60s ...'
#        time.sleep(60)
#    else:
#        is_running = False
#        break
#
#if not is_running:
#    os.system('touch %s' % fname)
#    takeData.takeData(doLoop=True, n_hours = 60./3600)
#
#os.system('rm %s' % fname)
#print 'job finished, delete', fname
