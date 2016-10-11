"""
Convert data from SRS RGA ASCII / text file to root format. 
"""

import os
import sys
from array import array

from ROOT import gROOT
gROOT.SetBatch(True) #run in batch mode
import ROOT

def process_file(filename):

    print "--> processing", filename

    # identify columns of variables in the .dat file:
    branchList = [
        "mass/D",
        "pressure",
        ]
    
    print "length of branchList:", len(branchList)

    branchDescriptor = ":".join(branchList)
    #print branchDescriptor

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    #print basename

    output_file = ROOT.TFile("%s.root" % basename, "recreate")
     
    tree = ROOT.TTree("tree","RGA scan mass vs. pressure data")
    print "reading in the data file with root..."
    tree.ReadFile(filename, branchDescriptor,",")
    print "...done"

    #tree.Print()
    tree.SetLineColor(ROOT.kBlue)
    tree.SetLineWidth(2)
    tree.SetMarkerColor(ROOT.kBlue)
    tree.SetMarkerStyle(8)
    tree.SetMarkerSize(0.5)
    tree.Write()
    n_entries = tree.GetEntries()
    print "%i entries in tree" % n_entries

    data_tree = ROOT.TTree("data_tree","RGA scan header data")

    # header data to store in data_tree:
    noise_floor = array("i", [-1]) # I think noise floor is related to scan speed. 
    data_tree.Branch("noise_floor", noise_floor, "noise_floor/I")

    data_file = file(filename)
    for i_line, line in enumerate(data_file):
        print i_line, line
        split_line = line.split(",")
        if split_line[0] == "Noise Floor":
            noise_floor[0] =  int(split_line[1])
            #break
        if i_line >= 19: break

    data_tree.Fill()
    data_tree.Write()

    output_file.Close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [RGA *.txt files]"
        sys.exit(1)

    for filename in sys.argv[1:]:

        process_file(filename)

