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

from struck import struck_analysis_parameters


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
    is_MC = is_tree_MC(tree)

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use

    canvas = TCanvas("canvas","", 1700, 900)
    pad = canvas.cd(1)
    pad.SetGrid(1,1)
    pad.SetLogy()
    legend = TLegend(0.12, 0.81, 0.55, 0.89)
    legend.SetNColumns(struck_analysis_parameters.n_chargechannels + 1)

    chargeenergy_low = 1000 
    chargeenergy_high = 1200

    ## all channels
    tree.Draw("rise_time_stop95-trigger_time >> hist_all(300, -0.02, 11.98)", "channel!=5&&channel!=8&&chargeEnergy>%i&&chargeEnergy<%i" % (chargeenergy_low, chargeenergy_high))
    hist_all = gDirectory.Get("hist_all")
    hist_all.SetLineColor(TColor.kBlack)
    hist_all.SetTitle("Charge energy %i to %i" % (chargeenergy_low, chargeenergy_high))
    hist_all.SetXTitle("Drift time (#mus)")
    hist_all.SetYTitle("Counts per %.2f #mus bin" % hist_all.GetBinWidth(1))
    legend.AddEntry(hist_all, "All channels", "l")

    ## individual channels
    hist = {}
    for i in xrange(len(charge_channels_to_use)):
        if not charge_channels_to_use[i]:
            continue

        tree.Draw("rise_time_stop95[%i]-trigger_time >> hist%i(300, -0.02 , 11.98)" % (i, i),
                "chargeEnergy>%i&&chargeEnergy<%i" % (chargeenergy_low, chargeenergy_high),
                "SAME")
        hist[i] = gDirectory.Get("hist%i" % i)
        hist[i].SetLineColor(struck_analysis_parameters.get_colors()[i])
        legend.AddEntry(hist[i], struck_analysis_parameters.channel_map[i], "l")

    legend.Draw()
    canvas.Update()
    canvas.Print("drifttime_channels_chargeEnergy_%ito%i.png" % (chargeenergy_low, chargeenergy_high))
    canvas.Print("drifttime_channels_chargeEnergy_%ito%i.pdf" % (chargeenergy_low, chargeenergy_high))
    


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



