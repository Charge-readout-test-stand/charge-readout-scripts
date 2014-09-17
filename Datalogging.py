"""
This script finds the most recent labview data file and generates plots from it.
"""

import os
import glob 
import shutil
#import threading
import TPMLog

def datalog():
    directory = 'C://Users//xenon//Dropbox//labViewPlots/'
    if not os.path.isdir(directory):
        print "trying alexis' path..."
        directory = '/Users/alexis/Downloads/'
    files = os.path.join(directory, '*.dat')
    flist = glob.glob(files)
    # use the last file, in alphabetical order -- this will be the most recent
    testfile = flist[-1]
    plot_string = TPMLog.main(testfile)
    #print "plot string", plot_string
    current_plot_dir = 'C://Users//xenon//Dropbox//currentPlots/'
    if not os.path.isdir(current_plot_dir):
        current_plot_dir = '/Users/alexis/Downloads/'
    plot_filenames = glob.glob(plot_string)
    for plot_filename in plot_filenames:
        #print plot
        basename = os.path.basename(plot_filename)
        #print basename
        filetype =  os.path.splitext(basename)[1]
        current_name = basename.split('_')[0] 
        current_name += filetype
        current_name = os.path.join(current_plot_dir, current_name)
        #print current_name
        shutil.copyfile(plot_filename, current_name)
    #threading.Timer(600, datalog).start()
    
    
    

datalog()
