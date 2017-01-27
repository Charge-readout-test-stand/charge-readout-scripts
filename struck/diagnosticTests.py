#!/usr/bin/env python

"""
Draw some plots to help with simple diagnostics

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


def draw_channel_plots(
    tree,           # the TTree/TChain
    var,            # variable to plot, e.g. baseline_rms*calibration
    plot_name,      # plot name, e.g. baseline_rms_x_calibration
    min_bin=0.0,    # min y bin
    max_bin=30.0,   # max y bin
    units=None,     # keV, etc
    basename="",       # file basename
    ):

    """
    Draw var vs. time, for each channel
    """

    print "=====> Drawing %s vs. time" % var

    # selections
    #selection = "!is_pulser && !is_bad" # usual
    selection = "1"
    #selection = "Entry$<10000 && !is_pulser && !is_bad" # debugging

    # get the run start and end times:
    tree.GetEntry(0)
    start_time = tree.file_start_time
    tree.GetEntry(tree.GetEntries()-1)
    end_time = tree.file_start_time + tree.time_stampDouble/tree.sampling_freq_Hz
    print "start_time:", start_time
    print "end_time:", end_time
    n_hours = int((end_time - start_time)/60.0/60.0)+1
    print "n_hours:", n_hours

    # time since run start, in hours:
    time_string = "(file_start_time-%.1f+time_stampDouble/sampling_freq_Hz)*1.0/60/60" % start_time

    draw_cmd = "%s:%s" % (var, time_string)


    # set up the canvas
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetLeftMargin(0.12)
    canvas.SetGrid(1,1)
    canvas.SetLogz(1)

    # loop over channels
    for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):

        label = struck_analysis_parameters.channel_map[channel]
        print "--> channel %i, %s: %s" % (channel, label, var)

        # set up the hist:
        hist = ROOT.TH2D("hist_%i" % channel, "", 50, 0, n_hours, 50, min_bin, max_bin)
        hist.SetXTitle("Time [hours]")
        hist.GetXaxis().SetTitleOffset(1.2)
        ytitle = var
        if units != None:
            ytitle += " [%s]" % units
        hist.SetYTitle(ytitle)

        ch_selection = "%s && channel==%i" % (selection, channel)
        ch_draw_cmd = "%s >> %s" % (draw_cmd, hist.GetName())
        print "\t ch_draw_cmd:", ch_draw_cmd
        print "\t ch_selection:", ch_selection

        n_drawn =  tree.Draw(ch_draw_cmd, ch_selection, "goff") 
        print "\t %i entries drawn" % n_drawn
        print "\t %i entries in hist" % hist.GetEntries()
        

        # add more details to the title
        title = " channel %i: %s | %.2e counts | mean: %.2f | rms: %.2f" % (
            channel, 
            label,
            n_drawn,
            hist.GetMean(),
            hist.GetRMS(),
        )
        print "\t %s" %  title
        hist.SetTitle(title)

        hist.Draw("colz")
        canvas.Update()
        ch_plot_name = "diagnostic_%s_%s_ch_%i.png" % (basename, plot_name, channel)
        canvas.Print(ch_plot_name)

        if not ROOT.gROOT.IsBatch():
            raw_input("any key to continue... ")

    print "====> done drawing %s vs. time \n\n" % var





def process_file(filenames):

    print "processing files: ", len(filenames)

    basename = os.path.commonprefix(filenames)
    basename = os.path.basename(basename)
    basename = os.path.splitext(basename)[0]
    print basename


    # open the root file and grab the tree
    tree = ROOT.TChain("tree")
    for filename in filenames:
        tree.Add(filename)
    print "%i entries in tree" % tree.GetEntries()

    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("is_bad",1)
    tree.SetBranchStatus("is_pulser",1)

    # needed to plot time on x axis:
    tree.SetBranchStatus("file_start_time",1) 
    tree.SetBranchStatus("sampling_freq_Hz",1) 
    tree.SetBranchStatus("time_stampDouble",1) 


    #tree.SetBranchStatus("energy1_pz")
    #tree.SetBranchStatus("SignalEnergy",1)
    #tree.SetBranchStatus("signal_map",1)


    if True:
        # baseline_rms
        tree.SetBranchStatus("baseline_rms",1)
        tree.SetBranchStatus("calibration",1)
        draw_channel_plots(tree, "baseline_rms*calibration", "baseline_rms_x_calibration", 0.0, 30.0, "keV", basename)

        # energy1
        tree.SetBranchStatus("energy1",1)
        draw_channel_plots(tree, "energy1", "energy1", 0.0, 1000.0, "keV", basename)

    # baseline_mean
    tree.SetBranchStatus("baseline_mean",1)
    draw_channel_plots(tree, "baseline_mean", "baseline_mean", 0.0, pow(2,14), "ADC units", basename)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [tier3 root files]"
        sys.exit(1)

    process_file(sys.argv[1:])



