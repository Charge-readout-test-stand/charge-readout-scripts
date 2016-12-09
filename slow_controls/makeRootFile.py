#!/usr/bin/env python

"""
this script converts slow controls *.dat files to root files

using TTree:ReadFile()
https://root.cern.ch/root/html/TTree.html#TTree:ReadFile

07 January 2014 AGS
"""

import os
import sys

from ROOT import gROOT
gROOT.SetBatch(True) #run in batch mode
from ROOT import TTree
from ROOT import TFile
from ROOT import TColor


def main(filename):

    print "--> processing file:", filename

    # find the number of columns in the data file:
    data_file = file(filename)
    line0 = data_file.readline()
    #print line0 # debugging
    n_cols = len(line0.split())
    print "%i columns in data file" % n_cols

    # identify columns of variables in the .dat file:
    branchList = [
      "timeStamp/D",
      "tCuBot",
      "tCellTop",
      "tCellMid",
      "tCellBot",
      "tCuTop",
      "tAmbient",
      "tLnFtIn",
      "tLnFtOut",
      "tXeRecoveryBottle",
      "T_min_set",
      "T_max_set",
      "tXV5",
      "tReg",
      "tOmega",
      "lnValveOpen",
      "lnEnabled",
      "heaterOn",
      "massFlowRateUncorr",
      "pXenon",
      "pVacuum",
      "pCCG",
      "massLN",
      "massXe",
      "capacitance",
      "T_max_offset",
      "T_min_offset",
      "pHFE",
      "massLnTare",
      "lnRecoveryValveOpen",
      ]

    if n_cols > len(branchList): 
        branchList.append("massFlowValveClosed")
    if n_cols > len(branchList): 
        branchList.append("pXeBottles")

    # for any extra columns, add some extra arbitrary variable names to make
    # this work:
    for i in xrange(n_cols - len(branchList)):
        branchList.append("var%i" % i)
    
    print "length of branchList:", len(branchList)

    branchDescriptor = ":".join(branchList)
    #print branchDescriptor

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    #print basename

    output_file = TFile("%s.root" % basename, "recreate")
    
    tree = TTree("tree","tree created from test stand slow control data")
    print "reading in the data file with root..."
    tree.ReadFile(filename, branchDescriptor)
    print "...done"

    #tree.Print()
    tree.SetLineColor(TColor.kBlue)
    tree.SetLineWidth(2)
    tree.SetMarkerColor(TColor.kBlue)
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

    for filename in sys.argv[1:]:

        main(filename)

