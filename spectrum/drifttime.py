#!/usr/bin/env python

"""
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

import struck_analysis_parameters
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
    tree.SetLineWidth(3)

    canvas = TCanvas("canvas","", 1700, 900)
    pad = canvas.cd(1)
    pad.SetGrid(1,1)
    pad.SetLogy()
    legend = TLegend(0.1, 0.7, 0.4, 0.9)

    ## all events
    tree.Draw("rise_time_stop95-trigger_time >> hist1(300, -0.02 , 11.98)", "channel!=5&&channel!=8")
    hist1 = gDirectory.Get("hist1")
    hist1.SetLineColor(TColor.kBlack)
    legend.AddEntry(hist1, "All events", "l")

    ## charge energy between 475keV and 675keV
    tree.Draw("rise_time_stop95-trigger_time >> hist2(300, -0.02, 11.98)", "channel!=5&&channel!=8&&chargeEnergy>475&&chargeEnergy<675", "SAME")
    hist2 = gDirectory.Get("hist2")
    hist2.SetLineColor(TColor.kBlue)
    legend.AddEntry(hist2, "Charge energy 475 - 675 keV", "l")

    ## charge energy between 1000keV and 1200keV
    tree.Draw("rise_time_stop95-trigger_time >> hist3(300, -0.02, 11.98)", "channel!=5&&channel!=8&&chargeEnergy>1000&&chargeEnergy<1200", "SAME")
    hist3 = gDirectory.Get("hist3")
    hist3.SetLineColor(TColor.kRed)
    legend.AddEntry(hist3, "Charge energy 1000 - 1200 keV", "l")

    ## charge energy > 150keV
    tree.Draw("rise_time_stop95-trigger_time >> hist4(300, -0.02, 11.98)", "channel!=5&&channel!=8&&chargeEnergy>150", "SAME")
    hist4 = gDirectory.Get("hist4")
    hist4.SetLineColor(TColor.kGreen + 3)
    legend.AddEntry(hist4, "Charge energy > 150 keV", "l")


    legend.Draw()
    canvas.Update()
    canvas.Print("drifttime.png")
    canvas.Print("drifttime.pdf")

    


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



