"""
Back up data to LLNL's HPSS tape storage

run from oslic:
  ssh oslic

also, from aztec, try this to check on files:
  hoppper

instructions and hopper info:
https://computing.llnl.gov/tutorials/lc_resources/#FileTransfers

htar documentation:
https://computing.llnl.gov/LCdocs/htar/
"""


import os
import sys
import glob
import commands


# files to transfer:

# 12 Sept 2016
filenames = glob.glob("/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier0/*") 
#filenames = sys.argv[1:] 

filenames.sort() # sort names

# loop over all files, this takes ~ 3 seconds per file
# existing files on HPSS are overwritten by default
for i_file, filename in enumerate(filenames):
    print "--> processing %i of %i: %s" % (i_file, len(filenames), filename)

    # include file directories in the tar name. These must already exist on HPSS
    tar_name =  "/".join(filename.split("/")[-3:])
    tar_name = "%s.tar" % tar_name
    print "\t", tar_name

    cmd = "htar -c -v -f %s %s" % (tar_name, filename) 
    print "\t", cmd
    output = commands.getstatusoutput(cmd)
    print "\n",output[1]
    #break # debugging

