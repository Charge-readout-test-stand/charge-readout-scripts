"""
compare early and late times from 9th LXe
"""

import os
import sys
import ROOT
ROOT.gROOT.SetBatch(True)

from struck import struck_analysis_cuts
from struck import struck_analysis_parameters

# options
#draw_cmd = "energy1_pz" # individual channel spectra
#draw_cmd = "Sum$(energy_pz*signal_map)" # testing
draw_cmd = "SignalEnergy" # the usual

drift_time_high = struck_analysis_parameters.max_drift_time
drift_time_low = struck_analysis_parameters.drift_time_threshold
#drift_time_high = 8.0
#drift_time_low = 8.0
#drift_time_low = 3.0
#drift_time_high = 8.5
#drift_time_high = 9.0
#drift_time_high = 0.0
#drift_time_low = 0.0
nsignals = 15
# the usual:
selection = "nsignals<=%i && rise_time_stop95_sum-trigger_time>%s && rise_time_stop95_sum-trigger_time<%s" % ( nsignals, drift_time_low, drift_time_high)
#selection = ""
#selection = "nsignals==1 && rise_time_stop95_sum-8>8.5&&rise_time_stop95_sum-8<8.9&&rise_time_stop50_sum-8>7" # like Conti
#selection += "&& rise_time_stop50_sum>8.0"
#selection += " && signal_map[16]==0 && signal_map[7]==0 && signal_map[21]==0"
#selection += " && signal_map[16]==0"
#selection = "nsignals>=0"
selection += "&& !is_pulser && !is_bad"


# hist options
min_bin = 300.0
max_bin = 1400.0
bin_width = 5 # keV
n_bins = int((max_bin - min_bin)/bin_width)


if len(sys.argv) < 2:
    print "provide tier3 files as arguments"
    sys.exit(1)

struck_filename = sys.argv[1]

canvas = ROOT.TCanvas("canvas","")
canvas.SetLeftMargin(0.12)
canvas.SetGrid(1,1)

basename = os.path.splitext(os.path.basename(struck_filename))[0]

print "--> Struck file:", struck_filename
struck_file = ROOT.TFile(struck_filename)
struck_tree = struck_file.Get("tree")

struck_tree.SetBranchStatus("*",0) # first turn off all branches
struck_tree.SetBranchStatus(draw_cmd,1) 
struck_tree.SetBranchStatus("nsignals",1) 
struck_tree.SetBranchStatus("channel",1) 
struck_tree.SetBranchStatus("rise_time_stop95_sum",1) 
struck_tree.SetBranchStatus("trigger_time",1) 
struck_tree.SetBranchStatus("is_pulser",1) 
struck_tree.SetBranchStatus("is_bad",1) 
struck_tree.SetBranchStatus("file_start_time",1) 
struck_tree.SetBranchStatus("sampling_freq_Hz",1) 
struck_tree.SetBranchStatus("time_stampDouble",1) 

print "\t %i Struck entries" % struck_tree.GetEntries()
struck_hist = ROOT.TH1D("struck_hist","", n_bins, min_bin, max_bin)
struck_hist.SetXTitle("%s [keV]" % draw_cmd)
struck_hist.SetYTitle("Counts / %.1f keV" % struck_hist.GetBinWidth(1))
struck_hist.GetYaxis().SetTitleOffset(1.5)
struck_hist.SetLineColor(ROOT.kBlue)
struck_hist.SetFillColor(ROOT.kBlue)
struck_hist.SetFillStyle(3004)
struck_hist.SetMarkerColor(ROOT.kBlue)
struck_hist.SetMarkerStyle(21)
struck_hist.SetMarkerSize(1.5)
struck_hist.SetLineWidth(2)

struck_hist2 = struck_hist.Clone("struck_hist2")
struck_hist2.SetLineColor(ROOT.kRed)
struck_hist2.SetFillColor(ROOT.kRed)

struck_tree.GetEntry(0)
start_time = struck_tree.file_start_time
struck_tree.GetEntry(struck_tree.GetEntries()-1)
end_time = struck_tree.file_start_time + struck_tree.time_stampDouble/struck_tree.sampling_freq_Hz
print start_time
print end_time
n_hours = (end_time - start_time)/60.0/60.0
print n_hours

# make selection strings
first_times = "(file_start_time-%f+time_stampDouble/sampling_freq_Hz)*1.0/60/60<10" % start_time
last_times = "(%f - file_start_time-time_stampDouble/sampling_freq_Hz)*1.0/60/60<10" % end_time
print first_times
print last_times

for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
    if val == 0: continue

    if draw_cmd == "energy1_pz":
        print "--> channel", channel, struck_analysis_parameters.channel_map[channel]
        struck_selection = " && ".join([selection, "channel==%i" % channel])
    else:
        struck_selection = selection

    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    struck_hist2.GetDirectory().cd()
    this_selection = "%s && %s" % (last_times, struck_selection)
    print "this_selection:", this_selection
    struck_tree.Draw("%s >> %s" % (draw_cmd, struck_hist2.GetName()),this_selection)
    print "\t %i entries in hist" % struck_hist2.GetEntries()

    struck_hist.GetDirectory().cd()
    print "draw_cmd:", draw_cmd
    this_selection = "%s && %s" % (first_times, struck_selection)
    print "selection:", this_selection
    struck_tree.Draw("%s >> %s" % (draw_cmd, struck_hist.GetName()),this_selection)
    print "\t %i entries in hist" % struck_hist.GetEntries()

    start_bin = struck_hist.FindBin(300.0)
    stop_bin = struck_hist.FindBin(1400.0)

    try:
        scale_factor = 1.0*struck_hist.Integral(start_bin,stop_bin)/struck_hist2.Integral(start_bin,stop_bin)
    except ZeroDivisionError: 
        scale_factor = 1.0
        print "No counts in  hist 1!!"
    print "hist 1 scale factor:", scale_factor
    struck_hist2.Scale(scale_factor)

    if draw_cmd == "energy1_pz":
        legend.AddEntry(struck_hist, "First 10 hours ch %i %s" % (channel, struck_analysis_parameters.channel_map[channel]), "f")
    else:
        legend.AddEntry(struck_hist, "First 10 hours (%.1e)" % struck_hist.GetEntries(), "f")
    legend.AddEntry(struck_hist2, "Last 10 hours (%.1e)" % struck_hist2.GetEntries(), "f")

    # this doesn't work well for low stats:
    #if draw_cmd != "energy1_pz":
    if True:
        struck_hist.SetMaximum() # reset since we keep filling the same hist... 
        y_max = struck_hist.GetMaximum()
        if struck_hist2.GetMaximum() > y_max: y_max = struck_hist2.GetMaximum()
        struck_hist.SetMaximum(y_max*1.1)

    struck_hist.Draw()
    struck_hist2.Draw("hist same")
    struck_hist.Draw("same")
    legend.Draw()
    canvas.Update()
    plotname = "comparison_%s" % draw_cmd
    if "Sum" in draw_cmd:
        plotname = "comparison_test" 
    if draw_cmd == "energy1_pz":
        plotname += "_ch%i" % channel
    plotname += "_%ikeV_bins" % bin_width

    canvas.Print("%s_%s.pdf" % (plotname, basename))

    pavetext = ROOT.TPaveText(0.12, 0.8, 0.9, 0.9, "ndc")
    pavetext.AddText(struck_selection[:200])
    pavetext.AddText("\nstruck 2 amplitude x %.2f" % (scale_factor, ))
    pavetext.SetBorderSize(0)
    pavetext.SetFillStyle(0)
    pavetext.Draw()

    plotname += "_drift_%i_to_%i_" % (drift_time_low*1e3, drift_time_high*1e3)
    plotname += "%i_signals_" % nsignals
    canvas.Update()
    canvas.Print("%s_%s_cuts.pdf" % (plotname, basename))

    if not ROOT.gROOT.IsBatch():
        raw_input("any key to continue... ")

    if draw_cmd != "energy1_pz": break

