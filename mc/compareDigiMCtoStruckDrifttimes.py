#!/usr/bin/env python

"""
this script compares struck and MC drift times
"""

import os
import sys

from ROOT import gROOT
# it seems like if this is commented out the legend has red background
#gROOT.SetBatch(True) # comment out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle

from struck import struck_analysis_parameters


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(mc_filename, struck_filename):


    # options:
    hist_max = 22.0
    hist_min = -2.0
    n_bins = int((hist_max - hist_min)*4.0)
    print hist_min, hist_max, n_bins

    mc_selection = []
    mc_channels = struck_analysis_parameters.MCcharge_channels_to_use
    for (channel, value)  in enumerate(mc_channels):
        if mc_channels[channel]:
            print "MC channel %i" % channel
            mc_selection.append("(channel==%i)" % channel)

    mc_selection = " || ".join(mc_selection)
    print mc_selection

    # construct a basename from the input filename
    basename = os.path.basename(mc_filename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix

    # make a histogram to hold energies
    hist = TH1D("hist", "", n_bins, hist_min, hist_max)
    hist.SetLineColor(TColor.kRed)
    hist.SetFillColor(TColor.kRed)
    hist.SetFillStyle(3004)
    hist.SetLineWidth(2)

    hist_struck = TH1D("hist_struck","", n_bins, hist_min, hist_max)
    hist_struck.SetLineColor(TColor.kBlue)
    hist_struck.SetFillColor(TColor.kBlue)
    hist_struck.SetFillStyle(3004)
    hist_struck.SetLineWidth(2)

    # open the struck file and get its entries
    print "processing Struck file: ", struck_filename
    struck_file = TFile(struck_filename)
    struck_tree = struck_file.Get("tree")
    hist_struck.GetDirectory().cd()
    struck_entries = struck_tree.Draw(
        "rise_time_stop95-trigger_time >> %s" % hist_struck.GetName(),
        "channel!=8 && energy1_pz>200",
        "goff"
    )
    #hist_struck.SetMaximum(20e3)
    print "\t%.1e struck entries" % struck_entries

    print "processing MC file: ", mc_filename
    # open the root file and grab the tree
    mc_file = TFile(mc_filename)
    mc_tree = mc_file.Get("tree")
    print "\t%.2e events in MC tree" % mc_tree.GetEntries()

    hist.GetDirectory().cd()
    mc_entries = mc_tree.Draw(
        "rise_time_stop95-trigger_time >> %s" % hist.GetName(),
        "(%s) && energy1_pz>200 && Entry$<1e6" % mc_selection,
        "goff"
    )
    print "\t%.1e MC entries" % mc_entries

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    scale_factor = 1.0*struck_entries/mc_entries
    print "scale_factor", scale_factor
    hist.Scale(scale_factor)

    hist_struck.SetXTitle("Drift time [#mus]")
    hist_struck.SetYTitle("Counts  / %.2f #mus" % (
        hist.GetBinWidth(1),
    ))

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)
    legend.AddEntry(hist, "MC", "fl")
    legend.AddEntry(hist_struck, "Struck data", "fl")

    hist_struck.Draw()
    hist.Draw("same") 
    legend.Draw()
    #hist_struck.Draw("same")
    print "%i struck entries" % hist_struck.GetEntries()
    print "%i mc entries" % hist.GetEntries()

    canvas.Update()
    canvas.Print("%s_drift_times.pdf" % basename)

    if not gROOT.IsBatch():
        canvas.Update()
        raw_input("pause...")

if __name__ == "__main__":

    #if len(sys.argv) < 2:
    #    print "arguments: [sis root files]"
    #    sys.exit(1)

    # loop over all provided arguments
    #process_file(sys.argv[1], sys.argv[2])


    #mc_file = "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207_Full_Ralph/Tier3/all_tier3_Bi207_Full_Ralph.root"
    mc_file = "207biMc.root"
    data_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root"

    process_file(mc_file, data_file)



