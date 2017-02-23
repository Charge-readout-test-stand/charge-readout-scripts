#!/usr/bin/env python

import os
import sys
import ROOT

"""
This script draws waveforms from nEXOdigi and prints info about them. 
"""

def main(filename):
  
    digi_file = ROOT.TFile(filename)
    tree = digi_file.Get("waveformTree")
    n_entries = tree.GetEntries()
    print "%i entries in tree" % n_entries

    canvas = ROOT.TCanvas("canvas", "")  
    canvas.SetGrid()

    tree.SetLineColor(ROOT.kBlue)
    tree.SetMarkerColor(ROOT.kBlue)
    tree.SetMarkerSize(0.8)
    tree.SetMarkerStyle(8)

    for i_entry in xrange(n_entries):

        tree.GetEntry(i_entry)

        print "entry %i | Evt %i | WFLen %i | WFTileId %i | WFLocalId %i | WFChannelCharge %i" % (
            i_entry, 
            tree.EventNumber,
            tree.WFLen,
            tree.WFTileId,
            tree.WFLocalId,
            tree.WFChannelCharge,
        )

        selection = "Entry$==%i" % i_entry
        tree.Draw("WFAmplitude:WFTime",selection,"pl")
        canvas.Update()

        val = raw_input("press enter (q to quit) ") 
        if val == 'q':
            sys.exit()


if __name__ == "__main__":

    if len(sys.argv) < 1:
      print "exiting"
      sys.exit(1)

    for filename in sys.argv[1:]:
      main(filename)
