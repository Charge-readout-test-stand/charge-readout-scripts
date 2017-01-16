#!/usr/bin/env python

"""
This script loops through directories; finds & removes bad root files
"""


import os
import sys
import glob
import commands

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TFile

TFile.Recover=0


def is_root_file_ok(filename):
    """
    check whether this is a valid file
    """

    print "--> processing file:", filename

    file_type = os.path.splitext(filename)[1]
    #print file_type
    if file_type != ".root":
        return True


    size = os.path.getsize(filename)

    print "\t size:", size
    
    root_file = TFile(filename)
    if root_file.IsZombie():
        print "\t BAD FILE (zombie)!!"
        return False

    if root_file.TestBit(TFile.kRecovered):
        print "\t RECOVERED file"
        return False

    tree = root_file.Get("HitTree")

    try:
        n_entries = tree.GetEntriesFast()
        print "\t n_entries", n_entries
        return True
    except AttributeError:
        print "\t BAD FILE!!"  
        return False
    


def process_directory(
    directory,  # directory we're searching
    bad_file_dir,  # place to put bad files
):
    n_bad_files = 0

    print "--> processing directory:", directory

    # loop over each item in this directory, process as a file or directory
    items = glob.glob("%s/*" % directory)
    for item in items:

        if os.path.isdir(item):
            process_directory(item, bad_file_dir)

        else:
            test_result = is_root_file_ok(item)

            if not test_result:
                cmd = 'mv %s %s/' % (item, bad_file_dir)
                print cmd
                (status, output) = commands.getstatusoutput(cmd)
                if status != 0:
                    print output
                n_bad_files += 1

    print "==> %i bad files" % n_bad_files
        #break # debugging


    

directories = sys.argv[1:]

# make a directory to hold bad files
bad_file_dir = 'bad_files'
cmd = "mkdir %s" % bad_file_dir
print cmd
(status, output) = commands.getstatusoutput(cmd)
if status != 0:
    print output


for directory in directories:

    process_directory(directory, bad_file_dir)

    #break # debugging







