#!/usr/bin/env python

"""
this script converts slow controls *.dat files to root files

using TTree:ReadFile()
https://root.cern.ch/root/html/TTree.html#TTree:ReadFile

this is a draft, written for test_20141106_142221.dat

07 January 2014 AGS
"""

import os
import sys

import ROOT
ROOT.gROOT.SetBatch(True) #run in batch mode


def main(filename):

    print "--> processing file:", filename

    # find the number of columns in the data file:
    n_cols = 2
    print "%i columns in data file" % n_cols

    # identify the first few columns of variables in the .dat file:
    branchList = [
      "TE/D",
      "Counts/D",
      ]

    print "length of branchList:", len(branchList)

    branchDescriptor = ":".join(branchList)
    #print branchDescriptor

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    #print basename

    output_file = ROOT.TFile("%s.root" % basename, "recreate")
    
    tree = ROOT.TTree("tree","tree created from digitized Conti data")
    print "reading in the data file with root..."
    tree.ReadFile(filename, branchDescriptor,",")
    print "...done"

    #tree.Print()
    tree.SetLineColor(ROOT.kGreen+2)
    tree.SetLineWidth(2)
    tree.SetMarkerColor(ROOT.kGreen+2)
    tree.SetMarkerStyle(8)
    tree.SetMarkerSize(0.5)
    tree.Write()
    n_entries = tree.GetEntries()
    print "%i entries in tree" % n_entries


    output_file.Close()




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [*.dat files]"
        sys.exit(1)

    filename = sys.argv[1]

    main(filename)

