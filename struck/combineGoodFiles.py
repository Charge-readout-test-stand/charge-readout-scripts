#!/usr/bin/env python

"""
This script skims tier2 files, determines which are good, and adds them together
with hadd. Use like this:

./combineGoodFiles.py *NotShaped_Amplified*DT*.root > & combine.log

or

( time ./combineGoodFiles.py tier2_*NotShaped_Amplified*DT*.root ) > & combine.log

arguments [sis tier 2 root files of events]
"""

import sys
import commands

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TFile


def process_file(filename):

    print "--> processing file: ", filename

    if filename == "tier2_LXe_Run1_1700VC_1200VPMT_0134AM_NotShaped_Amplified_403mVDT_1.root":
        print "chose to skip this file", filename
        return 0

    # open the root file and grab the tree
    root_file = TFile(filename)
    
    if root_file.IsZombie():
        print "\t BAD FILE (zombie)!!"
        return False

    tree = root_file.Get("tree")
    try:
        n_entries = tree.GetEntries()
        print "\t %i entries" % n_entries
    except AttributeError:
        print "BAD FILE!"
        return 0
        

    n_entries = tree.Draw("lightEnergy","lightEnergy>100","goff")
    print "\t %i entries with lightEnergy > 100" % n_entries
    if n_entries == 0:
        print "\t skipping this file (too few light entries)!!"
        return 0

    # figure out the light threshold:
    print "\t minimum light Energy %i" % tree.GetMinimum("lightEnergy")
    print "\t maximum light Energy %i" % tree.GetMaximum("lightEnergy")

    return n_entries



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)

    good_names = []

    total_entries = 0

    for filename in sys.argv[1:]:
        entries =  process_file(filename)
        if entries > 0:
            good_names.append(filename)
            total_entries += entries

    print "total entries: ", total_entries

    print "%i good files:" % len(good_names)
    #print "\n".join(good_names)
    cmd = "time hadd -O combined.root %s" % " ".join(good_names)
    #print cmd
    print commands.getstatusoutput(cmd)[1]



