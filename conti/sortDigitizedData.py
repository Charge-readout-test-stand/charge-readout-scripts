"""
sort data in digitized Conti .txt file so that the x axis is always increasing
"""


import os
import sys
import ROOT
from array import array

def process_file(filename):
    print "--> processing", filename
    basename = os.path.splitext(os.path.basename(filename))[0]

    data = {}
    data_file = file(filename)

    # grab data from text file
    i_line = 0
    for line in data_file:
        #print "i_line:", i_line
        if i_line != 0: 
            try:
                key = float(line.split(",")[0])
                val = float(line.split(",")[1])
                data[key] = val
                print i_line, key, val
            except: pass
        i_line += 1

    # sort dict keys
    keys = data.keys()
    keys.sort()

    # set up root output file & tree
    tfile = ROOT.TFile("%s.root" % basename,"recreate")
    tree = ROOT.TTree("tree","Sorted digitized Conti data")
    te = array('d', [0]) # double
    tree.Branch("TE",te,"TE/D")
    counts = array('d', [0]) # double
    tree.Branch("counts",counts,"counts/D")

    # fill tree
    for key in keys:
        te[0] = key
        counts[0] = data[key]
        tree.Fill()

    # format & write tree
    tree.SetLineColor(ROOT.kGreen+2)
    tree.SetLineWidth(2)
    tree.SetMarkerColor(ROOT.kGreen+2)
    tree.SetMarkerStyle(8)
    tree.SetMarkerSize(0.5)
    n_entries = tree.GetEntries()
    print "%i entries in tree" % n_entries
    tree.Write()
    tfile.Close()


if __name__ == "__main__":
  
  filename = "ContiIonization.txt"
  if len(sys.argv) > 1:
      filename = sys.argv[1]

  process_file(filename) 
