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

# 8th LXe
#filenames = glob.glob("/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier0/*") # 12 Sept 2016
#filenames = glob.glob("/p/lscratchd/alexiss/2016_08_15_8th_LXe/tier0/*") # 13 Sept 2016

# 9th LXe
#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_cooldown/tier0/*") # 20 Sept 2016
#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_setup_LXeFull/tier0/*") # 20 Sept 2016

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_20160919*") # 20 Sept 2016 -- 66 files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609200[0123]*") # 20 Sept 2016 -- 240 files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609200[456]*") # 20 Sept 2016 -- 178? files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609200[789]*") # 21 Sept 2016 -- 180 files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609201*") # 22 Sept 2016 -- 598 files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609202*") # 22 Sept 2016 -- 238? files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609210*") # 22 Sept 2016 -- 596 files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609211*") # 22 Sept 2016 -- 594 files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_201609212*") # 22 Sept 2016 -- 238 files

#filenames = glob.glob("/p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier0/SIS3316Raw_2016*") # 23 Sept 2016 -- all 9th LXe overnight tier0 files


# 10th LXe
filenames = glob.glob("/p/lscratchd/alexiss/2017_01_10_10th_LXe/tier0/SIS3316Raw_*") # 16 Jan 2016 -- all 10th LXe tier0 files



filenames.sort() # sort names
print len(filenames)
#sys.exit() # debug

# loop over all files, this takes ~ 3 seconds per file
# existing files on HPSS are overwritten by default
for i_file, filename in enumerate(filenames):
    print "\n\n--> processing %i of %i: %s" % (i_file, len(filenames), filename)

    # include file directories in the tar name. These must already exist on HPSS
    #tar_name =  "/".join(filename.split("/")[-3:])
    tar_name =  "/".join(filename.split("/")[4:])
    tar_name = "%s.tar" % tar_name
    print "\t", tar_name
    #break # debugging

    #cmd = "htar -c -v -f %s %s" % (tar_name, filename) 
    cmd = "htar -c -P -v -Y dualcopy -f %s %s" % (tar_name, filename) 
    print "\t", cmd
    output = commands.getstatusoutput(cmd)
    print "\n",output[1]
    #break # debugging

