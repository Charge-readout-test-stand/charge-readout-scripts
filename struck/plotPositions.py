"""
copied from compareMCtoData_noise_branch.py
"""

import os
import sys
import ROOT
ROOT.gROOT.SetBatch(True)

from struck import struck_analysis_cuts
from struck import struck_analysis_parameters


def process_file(drift_time_low, drift_time_high):

        
    print "===> drift_time_low: %.2f, drift_time_high: %.2f" % (drift_time_low, drift_time_high)

    # options
    # chs 0-15 are y, ch 16-30 are x
    # if two channels are hit, the min channel id is the y channel and the max channel
    # is the x channel
    # exclude pulser & channel 0
    draw_cmd = "MinIf$(channel,signal_map*(channel!=0)):MaxIf$(channel,signal_map*(channel!=%i))-16" % struck_analysis_parameters.pulser_channel
    nsignals = 2
    # the usual:
    selection = "signal_map && nXsignals==1 && nYsignals==1 && rise_time_stop95_sum-trigger_time>%f && rise_time_stop95_sum-trigger_time<%f" % ( 
        drift_time_low, drift_time_high)

    #selection = ""
    selection += "&& !is_pulser && !is_bad"


    # hist options
    min_bin = -0.5
    max_bin = 16.5
    bin_width = 1.0 # keV
    n_bins = int((max_bin - min_bin)/bin_width)

    struck_filename = "~/9thLXe/overnight_9thLXe_v3.root" # LLNL
    if "teststand" in os.getlogin():
        struck_filename = "~/9th_LXe/twoSignals_overnight_9thLXe_v3.root" # DAQ
        struck_filename = "~/9th_LXe/overnight_9thLXe_v3.root" # DAQ

    if len(sys.argv) > 1:
        struck_filename = sys.argv[1]

    canvas = ROOT.TCanvas("canvas","", 500, 500)
    canvas.SetRightMargin(0.15)
    canvas.SetGrid(1,1)
    canvas.SetLogz(1)

    basename = os.path.splitext(os.path.basename(struck_filename))[0]

    print "--> Struck file:", struck_filename
    struck_file = ROOT.TFile(struck_filename)
    struck_tree = struck_file.Get("tree")

    struck_tree.SetBranchStatus("*",0) # first turn off all branches
    struck_tree.SetBranchStatus("SignalEnergy",1) 
    struck_tree.SetBranchStatus("nsignals",1) 
    struck_tree.SetBranchStatus("channel",1) 
    struck_tree.SetBranchStatus("nXsignals",1) 
    struck_tree.SetBranchStatus("nYsignals",1) 
    struck_tree.SetBranchStatus("signal_map",1) 
    struck_tree.SetBranchStatus("rise_time_stop95_sum",1) 
    struck_tree.SetBranchStatus("trigger_time",1) 
    struck_tree.SetBranchStatus("is_pulser",1) 
    struck_tree.SetBranchStatus("is_bad",1) 

    print "\t %i Struck entries" % struck_tree.GetEntries()
    struck_hist = ROOT.TH2D("struck_hist","", n_bins, min_bin, max_bin, n_bins, min_bin, max_bin)
    #struck_hist.SetTitle("%s {%s}" % (draw_cmd, selection))
    struck_hist.SetTitle(selection)
    struck_hist.SetTitle("drift times from %.2f to %.2f #mus" % (drift_time_low, drift_time_high))
    struck_hist.SetXTitle("X channel")
    struck_hist.SetYTitle("Y channel")
    #struck_hist.GetYaxis().SetTitleOffset(1.5)
    struck_hist.SetLineColor(ROOT.kBlue)
    struck_hist.SetFillColor(ROOT.kBlue)
    struck_hist.SetFillStyle(3004)
    struck_hist.SetMarkerColor(ROOT.kBlue)
    struck_hist.SetMarkerStyle(21)
    struck_hist.SetMarkerSize(1.5)
    struck_hist.SetLineWidth(2)


    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    struck_hist.GetDirectory().cd()
    print "draw_cmd:", draw_cmd
    print "selection:", selection
    struck_tree.Draw("%s >> %s" % (draw_cmd, struck_hist.GetName()),selection)
    print "\t %i entries in hist" % struck_hist.GetEntries()

    start_bin = struck_hist.FindBin(300.0)
    stop_bin = struck_hist.FindBin(1400.0)


    struck_hist.Draw("colz")
    #legend.Draw()
    canvas.Update()
    plotname = "hitLocations"

    canvas.Print("%s_%s.pdf" % (plotname, basename))
    canvas.Print("%s_%s.png" % (plotname, basename))

    pavetext = ROOT.TPaveText(0.12, 0.8, 0.9, 0.9, "ndc")
    pavetext.AddText(selection[:200])
    pavetext.SetBorderSize(0)
    pavetext.SetFillStyle(0)
    #pavetext.Draw()

    plotname += "_drift_%i_to_%i_" % (drift_time_low*1e3, drift_time_high*1e3)
    plotname += "%i_signals_" % nsignals
    canvas.Update()
    canvas.Print("%s_%s_cuts.pdf" % (plotname, basename))
    canvas.Print("%s_%s_cuts.png" % (plotname, basename))

    if not ROOT.gROOT.IsBatch():
        raw_input("any key to continue... ")


if __name__ == "__main__":

    delta_t = 0.5 # time bin, microseconds

    drift_time_high = struck_analysis_parameters.max_drift_time
    #drift_time_high = 9.0

    drift_time_low = drift_time_high - delta_t
    #while drift_time_low > struck_analysis_parameters.drift_time_threshold:
    while drift_time_low > 0.0:
        process_file(drift_time_low, drift_time_high)
        drift_time_high -= delta_t
        drift_time_low = drift_time_high - delta_t
    #drift_time_high = 0.0
    #drift_time_low = 0.0


