#!/usr/bin/env python

"""
this script compares struck and MC drift times
"""

import os
import sys

import ROOT
# it seems like if this is commented out the legend has red background
ROOT.gROOT.SetBatch(True) # comment out to run interactively

from struck import struck_analysis_parameters


ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       


def process_file(mc_filename, struck_filename):

    selection = "SignalEnergy>300"
    draw_cmd = "rise_time_stop95_sum-trigger_time+0.020"

    print "draw_cmd:", draw_cmd
    print "selection:", selection

    # options:
    hist_max = 35.0
    hist_min = -8.0
    n_bins = (hist_max - hist_min)/0.040/5
    print "n_bins:", n_bins
    n_bins = int(n_bins)
    print "hist_min: %i | hist_max: %i | n_bins: %i" % (hist_min, hist_max, n_bins)

    # construct a basename from the input filename
    basename = os.path.basename(mc_filename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix

    # make a histogram to hold energies
    hist = ROOT.TH1D("hist", "", n_bins, hist_min, hist_max)
    hist.SetLineColor(ROOT.kRed)
    hist.SetFillColor(ROOT.kRed)
    hist.SetFillStyle(3004)
    hist.SetLineWidth(2)

    hist_struck = ROOT.TH1D("hist_struck","", n_bins, hist_min, hist_max)
    hist_struck.SetLineColor(ROOT.kBlue)
    hist_struck.SetFillColor(ROOT.kBlue)
    hist_struck.SetFillStyle(3004)
    hist_struck.SetLineWidth(2)

    # open the struck file and get its entries
    print "processing Struck file: ", struck_filename
    struck_file = ROOT.TFile(struck_filename)
    struck_tree = struck_file.Get("tree")
    print "\tEntries in struck tree:", struck_tree.GetEntries()
    hist_struck.GetDirectory().cd()

    # do a special selection for struck data -- first round of 10th LXe tier3
    # processing has some bugs; is_pulser is set in the MC and is_bad is
    # flagged for ~all data events:
    struck_selection = selection+"&&!is_pulser&&pmt_chi2<=3"

    print "\tstruck_selection:", struck_selection
    struck_entries = struck_tree.Draw(
        "%s >> %s" % (draw_cmd, hist_struck.GetName()),
        struck_selection,
        "goff"
    )
    print "\t%.1e struck entries drawn" % struck_entries

    print "processing MC file: ", mc_filename
    # open the root file and grab the tree
    mc_file = ROOT.TFile(mc_filename)
    mc_tree = mc_file.Get("tree")
    print "\t%.2e events in MC tree" % mc_tree.GetEntries()

    hist.GetDirectory().cd()
    mc_entries = mc_tree.Draw(
        "%s >> %s" % (draw_cmd, hist.GetName()),
        selection,
        "goff"
    )
    print "\t%.1e MC entries drawn" % mc_entries
    print "\t%.1e entries in MC hist" % hist.GetEntries()

    # set up a canvas
    canvas = ROOT.TCanvas("canvas","")
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
    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)
    legend.AddEntry(hist, "MC", "f")
    legend.AddEntry(hist_struck, "Struck data", "f")

    if hist.GetMaximum() > hist_struck.GetMaximum():
        hist_struck.SetMaximum(hist.GetMaximum()*1.1)

    hist_struck.Draw("")
    hist.Draw("same") 
    legend.Draw()
    #hist_struck.Draw("same")
    print "%i struck hist entries" % hist_struck.GetEntries()
    print "%i mc hist entries" % hist.GetEntries()

    canvas.Update()
    canvas.Print("%s_drift_times.pdf" % basename)

    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("%s_drift_times_lin.pdf" % basename)

    if not ROOT.gROOT.IsBatch():
        canvas.Update()
        raw_input("pause...")


if __name__ == "__main__":

    #mc_file = "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207_Full_Ralph/Tier3/all_tier3_Bi207_Full_Ralph.root"
    mc_file = "207biMc.root"
    data_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root"

    if len(sys.argv) == 3:
        mc_file = sys.argv[1]
        data_file = sys.argv[2]
    process_file(mc_file, data_file)



