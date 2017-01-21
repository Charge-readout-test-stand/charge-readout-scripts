#!/usr/bin/env python

"""
Draw diagnostic plots

arguments [tier3 root files]
"""

import os
import sys

import ROOT
ROOT.gROOT.SetBatch(True)


ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       

import struck_analysis_parameters


def process_file(filename):

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    print basename

    hists = []
    n_channels = struck_analysis_parameters.n_channels
    hist = ROOT.TH2D("histwtf", basename, n_channels, -0.5, n_channels-0.5, n_channels, -0.5, n_channels-0.5)
    hists.append(hist)

    # open the root file and grab the tree
    root_file = ROOT.TFile(filename)
    tree = root_file.Get("tree")
    print "%i entries in tree" % tree.GetEntries()

    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("signal_map",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("is_bad",1)
    tree.SetBranchStatus("is_pulser",1)

    hist.GetDirectory().cd()

    print hist.GetName(), hist.GetTitle()
    for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
        #if val == 0: continue
        label = struck_analysis_parameters.channel_map[channel]
        print "channel %i: %s" % (channel, label)

        draw_cmd = "channel:%i >>+ %s" % (channel, hist.GetName())
        selection = "signal_map && signal_map[%i]" % channel
        selection += " && !is_bad && !is_pulser"
        print "\t", draw_cmd
        print "\t", selection

        n_counts = tree.Draw("channel","signal_map[%i]" % channel, "goff")
        print "\t n_counts in this slice: %i " % n_counts
        if n_counts == 0: continue
        selection = "(%s)*1.0/%i" % (selection, n_counts)
        print "\t", selection

        n_drawn = tree.Draw(draw_cmd, selection, "goff")
        print "\t %i entries drawn" % n_drawn
        print "\t %i entries in hist" % hist.GetEntries()

    # set up a canvas
    canvas = ROOT.TCanvas("canvas","", 600, 600)
    canvas.SetGrid(1,1)
    canvas.SetLogz(1)
    hist.Draw("colz")
    canvas.Update()
    canvas.Print("two_channel_correlations_%s_log.pdf" % basename)

    canvas.SetLogz(0)
    canvas.Update()
    canvas.Print("two_channel_correlations_%s_lin.pdf" % basename)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [tier3 root files]"
        sys.exit(1)

    for filename in sys.argv[1:]:
        process_file(filename)



