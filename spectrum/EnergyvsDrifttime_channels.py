#!/usr/bin/env python

"""
This script creates an eventlist from a tree. The criteria is specified in the script (subject to modification).

The eventlist will be saved to a root file. The script "ViewEventsUsingEventlist.py" can be run afterwards to view the events.

To run:
python /path/to/this/script /path/to/tier3_root_file
"""

import os
import sys
import glob
import time

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TH2D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gDirectory
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TMath
from ROOT import TTree
from ROOT import TEventList

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

from struck import struck_analysis_parameters
n_chargechannels = struck_analysis_parameters.n_chargechannels

gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import CLHEP

def process_file(filename):

    print "processing file: ", filename
    start_time = time.clock()

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")

    canvas = TCanvas("c1", "c1", 1700, 900)
    pad = canvas.cd(1)
    pad.SetGrid(1,1)
    pad.SetLogz()

    for i in xrange(n_chargechannels):
        tree.Draw("energy1_pz[%i]:rise_time_stop95[%i]-trigger_time >> h(300, -0.02, 11.98, 250, 0., 200.)" % (i,i), "", "colz")
        h = gDirectory.Get("h")
        h.SetXTitle("Drift time (#mus)")
        h.SetYTitle("Energy (keV)")
        h.SetTitle("Channel %i" % i)
        canvas.Update()
        canvas.Print("channel%i_zoomin.pdf" % i)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



