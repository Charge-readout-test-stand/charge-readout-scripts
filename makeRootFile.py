#!/usr/bin/env python

"""
this script converts *.dat files to root files

using TTree:ReadFile()
https://root.cern.ch/root/html/TTree.html#TTree:ReadFile

this is a draft, written for test_20141106_142221.dat

07 January 2014 AGS
"""

import os
import sys

from ROOT import gROOT
gROOT.SetBatch(True) #run in batch mode
from ROOT import TTree
from ROOT import TFile


def main(filename):

    print "--> processing file:", filename

    # find the number of columns in the data file:
    data_file = file(filename)
    line0 = data_file.readline()
    #print line0 # debugging
    n_cols = len(line0.split())
    print "%i columns in data file" % n_cols

    # identify the first few columns of variables in the .dat file:
    branchList = [
      "timeStamp",
      "tCuBot0",
      "tCellTop",
      "tCellMid",
      "tCellBot",
      "tCuTop",
      "tAmbient",
      "pLN",
      "sLN",
      "heat",
      ]

    # ignore the rest of the columns
    # add some extra arbitrary variable names to make this work:
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
    tree.Write()


    output_file.Close()




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [*.dat files]"
        sys.exit(1)

    filename = sys.argv[1]

    main(filename)

