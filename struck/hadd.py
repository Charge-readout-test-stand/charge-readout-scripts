"""
Add all tier3 together to make 1 file

add files with hadd, then hadd -O to optimize branches. 
"""

import os
import sys
import commands

do_opt = False # run hadd a second time with -O argument to reoptimize TTree branches

filenames = sys.argv[1:]

#basename = "overnight_9thLXe_v4"
basename = os.path.commonprefix(filenames)
directory = os.path.dirname(basename)
print "directory:", directory
basename = os.path.basename(basename)
no_opt_name = "%s.root" % basename
if do_opt:
    no_opt_name = "no_opt_%s.root" % basename
print "no_opt_name:", no_opt_name

# hadd, but don't reoptimize TTree branches:

# have to use *.root here or get an error, I think the arguments are too long 
#cmd = "time hadd %s %s/*.root" % (no_opt_name, directory)
cmd = "time hadd -k %s %s/*.root" % (no_opt_name, directory) # with -k
print cmd[:1000]
#print ""
output = commands.getstatusoutput(cmd)
print output[1]
if output[0] != 0:
    print "=====> ERROR!"

if do_opt:
    print "running hadd -O"
    # hadd again, this time reoptimize TTree branches
    cmd = "time hadd -O %s %s" % (basename, no_opt_name)
    output = commands.getstatusoutput(cmd)
    print output[1]

    # remove the no_opt version
    cmd = "rm %s" % no_opt_name
    output = commands.getstatusoutput(cmd)
    print output[1]

