#!/usr/bin/env python

"""
This script skims tier2 files, determines which are good, and adds them together
with hadd. Use like this:

./combineGoodFiles.py *NotShaped_Amplified*DT*.root > & combine.log

arguments [sis tier 2 root files of events]
"""

import os
import sys
import glob
import commands

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TH1D
from ROOT import TH2D


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(filename):

    print "--> processing file: ", filename

    # open the root file and grab the tree
    root_file = TFile(filename)
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

    return 1



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)

    good_names = []

    for filename in sys.argv[1:]:
        if process_file(filename):
            good_names.append(filename)

    print "%i good files:" % len(good_names)
    #print "\n".join(good_names)
    cmd = "time hadd -O combined.root %s" % " ".join(good_names)
    #print cmd
    print commands.getstatusoutput(cmd)[1]



