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


def process_file(filenames):

    selection = "SignalEnergy>300 && !is_bad && !is_pulser"
    draw_cmd = "rise_time_stop95_sum-trigger_time+0.020"

    print "draw_cmd:", draw_cmd
    print "selection:", selection

    # options:
    #hist_max = 35.0
    #hist_min = -8.0
    hist_max = 25.0
    hist_min = -0.0
    n_bins = (hist_max - hist_min)/0.040/5
    print "n_bins:", n_bins
    n_bins = int(n_bins)
    print "hist_min: %i | hist_max: %i | n_bins: %i" % (hist_min, hist_max, n_bins)


    hists = []

    colors = [
        ROOT.kBlue,
        ROOT.kRed,
        ROOT.kGreen+2,
        ROOT.kViolet,
        ROOT.kCyan+3,
        ROOT.kOrange+1,
    ]
    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)


    # set up a canvas
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)


    for i, filename in enumerate(filenames):

        # construct a basename from the input filename
        basename = os.path.basename(filename) # get rid of file path
        basename = os.path.splitext(basename)[0] # get rid of file suffix

        # make a histogram to hold energies
        hist = ROOT.TH1D("hist%i" % i, "", n_bins, hist_min, hist_max)
        hist.SetLineColor(colors[i])
        hist.SetFillColor(colors[i])
        hist.SetFillStyle(3004)
        hist.SetLineWidth(2)


        # open the file and get its entries
        print "processing file: ", filename
        tfile = ROOT.TFile(filename)
        tree = tfile.Get("tree")
        print "\tEntries in tree:", tree.GetEntries()

        tree.SetBranchStatus("*",0)
        tree.SetBranchStatus("rise_time_stop95_sum",1)
        tree.SetBranchStatus("trigger_time",1)
        tree.SetBranchStatus("SignalEnergy",1)
        tree.SetBranchStatus("is_pulser",1)
        tree.SetBranchStatus("is_bad",1)

        hist.GetDirectory().cd()

        isMC = struck_analysis_parameters.is_tree_MC(tree)

        # do a special selection for struck data -- first round of 10th LXe tier3
        # processing has some bugs; is_pulser is set in the MC and is_bad is
        # flagged for ~all data events:
        this_selection = selection
        #if not isMC:
        #    this_selection = selection+"&&!is_pulser&&pmt_chi2<=3"
        new_drift_velocity = 1.79
        my_draw_cmd = draw_cmd

        # testing new drift velocities for low fields
        #if basename == "mc_dcoeff50_10thLXe_wn_2":
        #    my_draw_cmd = "(%s)*1.85/%f" % (draw_cmd, new_drift_velocity)
        #if basename == "jobs_0_to_3399":
        #    my_draw_cmd = "(%s)*2.0/%f" % (draw_cmd, new_drift_velocity)
        print "\tmy_draw_cmd:", my_draw_cmd

        print "\tthis_selection:", this_selection
        entries = tree.Draw(
            "%s >> %s" % (my_draw_cmd, hist.GetName()),
            this_selection,
            "goff norm"
        )
        print "\t%.1e entries drawn" % entries
        print "\t%.1e entries in hist" % hist.GetEntries()
        legend.AddEntry(hist, basename, "f")
        hists.append(hist)

    hists[0].SetXTitle("Drift time [#mus]")
    hists[0].SetYTitle("Counts  / %.2f #mus" % (
        hists[0].GetBinWidth(1),
    ))

    y_max = 0
    for hist in hists:
        if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()

    hists[0].SetMaximum(y_max*1.1)
    hists[0].SetMinimum(1e-4)
    hists[0].Draw("")
    for hist in hists:
        hist.Draw("same")
    legend.Draw()

    canvas.Update()
    canvas.Print("drift_times_%i.pdf" % len(filenames))

    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("drift_times_lin_%i.pdf" % len(filenames))

    hists[0].SetAxisRange(5,15)
    canvas.Update()
    canvas.Print("drift_times_lin_zoom_%i.pdf" % len(filenames))

    if not ROOT.gROOT.IsBatch():
        canvas.Update()
        raw_input("pause...")


if __name__ == "__main__":

    #mc_file = "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207_Full_Ralph/Tier3/all_tier3_Bi207_Full_Ralph.root"
    mc_file = "207biMc.root"
    data_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root"

    filenames = [mc_file, data_file]

    if len(sys.argv) != 1:
        filenames = sys.argv[1:]
    process_file(filenames)



