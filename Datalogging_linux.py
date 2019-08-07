#!/usr/bin/env python

"""
This script finds the most recent labview data file and geneates plots from it.  
Works on the Ubuntu DAQ machine.  
"""

import os
import sys
import glob
import shutil
import TPMLog
import commands
import time

def download_file():
    #Here you can hardcode a specific file.
    #Won't get most recent but if at SLAC this makes more sense.

    down_link = "https://www.dropbox.com/s/hm41x102wk78cbg/test_20181101_173908.dat"

    print "--------->Downloading hardlinked file"
    print "........", down_link
    testfile  = os.path.basename(down_link)
    if os.path.isfile(testfile):
        print "File %s exists so firt delete it---->"
        cmd = 'rm %s' % testfile
        print "...... %s" % cmd,
        output = commands.getstatusoutput(cmd)
        #print output[0], output[1]
        if output[0]!=0:
            print "Failed to rm file"
            sys.exit(1)

    print "Downloading %s" % down_link
    cmd = "wget %s" % down_link
    output = commands.getstatusoutput(cmd)
    if output[0] != 0: 
        print "Failed to download", 
        sys.exit(1)
    #print output[0], output[1]
    if not os.path.isfile(testfile):
        print "Can't find file", testfile
        sys.exit(1)

    print "Download success"

    return testfile

def get_recent():
    #This gets the most recent LV file in dropbox.
    #Need to have the dropbox file saved locally otherwise use download_file

    print "----->Getting most recent LV file"
    #Dropbox location on this computer
    directory = "/home/teststand/Dropbox/TestStandESIII/"
    if not os.path.isdir(directory):
        print "Can't find the Dropbox folder", directory
        sys.exit(1)
    #Get file list using glob.  Should auto sort by date.
    files=os.path.join(directory, '*.dat')
    flist=glob.glob(files)
    #Sort files by time (oldest first)
    flist.sort(key=os.path.getmtime)

    if len(flist)==0:
        print "........... No files found .....", directory
        print "............ Pause and try again"
        time.sleep(5)
        
        print "..........Try #2"
        files=os.path.join(directory, '*.dat')
        flist=glob.glob(files)
        
        if len(flist)==0: 
            print "..... Still can't find exiting?", directory
            sys.exit(1)
    
    #print flist
    testfile = flist[-1] #last file = youngest
    print "......... Most recent file is ", testfile
    return testfile

def make_plots(testfile):
    #============Run Plots==================
    #=======================================
    plot_string = TPMLog.main(testfile)
    #=======================================
    #=======================================
    
    #raw_input("PAUSE")

    #Now move plots around to the dropbox plot folder
    #current_plot_dir='/home/teststand/Dropbox/'
    current_plot_dir = '/home/teststand/Dropbox/test_stand_shared/currentLVPlots/'
    if not os.path.isdir(current_plot_dir):
        print "Can't find the Dropbox folder", current_plot_dir
        sys.exit(1)
    plot_filenames=glob.glob(plot_string)
    
    #print plot_filenames
    #raw_input("PAUSE2")

    #Now loop over plots and remove basename
    for plot_filename in plot_filenames:
        basename=os.path.basename(plot_filename)
        filetype = os.path.splitext(basename)[1]
        current_name = basename.split('_')[0]
        current_name += filetype
        current_name = os.path.join(current_plot_dir, current_name)
        #shutil.copyfile(plot_filename, current_name)
        if '.dat' in plot_filename: continue
        shutil.move(plot_filename, current_name)
    print 'done'

def Run():
    #fname=download_file()
    fname=get_recent()
    make_plots(fname)

if __name__ == '__main__':
    Run()


