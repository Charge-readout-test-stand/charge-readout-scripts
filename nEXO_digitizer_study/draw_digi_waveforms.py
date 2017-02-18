#!/usr/bin/env python

import os
import sys
from ROOT import gROOT
from ROOT import TTree
from ROOT import TFile
from ROOT import TCanvas


def main(filename):
  
    digi_file = TFile(filename)
    tree = digi_file.Get("waveformTree")
    n_entries = tree.GetEntries()
    canvas = TCanvas("canvas", "", 100, 20000)  
    i_entry = 0
    while i_entry < n_entries:
        tree.GetEntry(i_entry)
        i_entry+=1
        selection = "Entry$==%i" % i_entry
        tree.Draw("WFAmplitude:WFTime",selection,"l")
        canvas.Update()
        raw_input("press enter") 

if __name__ == "__main__":

    if len(sys.argv) < 1:
      print "exiting"
      sys.exit(1)

    for filename in sys.argv[1:]:
      main(filename)
