"""

Compare MC & Struck data

use MC noise branch to smear MC energies. 

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
drift_time_high = 8.0
#drift_time_low = 6.4 # Gaosong's cut
#drift_time_high = 8.4 # Gaosong's cut
nsignals = 1 # only consider events where one strip is hit
nstrips = 1 # only use single-strip channels
#nsignals = 0
# the usual:
struck_selection = []
#struck_selection.append(struck_analysis_cuts.get_standard_cut( # can't use this on old MC
#    nsignals=nsignals,
#    drift_time_high=drift_time_high))
struck_selection.append("nsignals==%i" % nsignals)
struck_selection.append( struck_analysis_cuts.get_drift_time_selection(
    drift_time_low=drift_time_low,
    drift_time_high=drift_time_high))
struck_selection.append(struck_analysis_cuts.get_nstrips_events(nstrips=nstrips))
#struck_selection.append("signal_map[16]==0") # noisy channel
struck_selection = " && ".join(struck_selection)
mc_selection = struck_selection
selection = struck_selection


# hist options
min_bin = 300.0
max_bin = 1400.0
bin_width = 10 # keV
n_bins = int((max_bin - min_bin)/bin_width)

mc_filename = "/p/lscratchd/alexiss/mc_slac/red_jobs_0_to_3399.root"
struck_filename = "/g/g17/alexiss/scratch/9thLXe/2016_09_19_overnight/tier3_added/overnight_9thLXe_v3.root"

if len(sys.argv) < 3:
    print "provide tier3 files as arguments: MC file, struck data file"
if len(sys.argv) > 1:
    mc_filename = sys.argv[1]
    struck_filename = sys.argv[2]


canvas = ROOT.TCanvas("canvas","")
canvas.SetLeftMargin(0.12)
canvas.SetGrid(1,1)

mc_basename = os.path.splitext(os.path.basename(mc_filename))[0]
struck_basename = os.path.splitext(os.path.basename(struck_filename))[0]
basename = "%s_%s" % (mc_basename, struck_basename)
# grab MC tree
print "--> MC file:", mc_filename
mc_file = ROOT.TFile(mc_filename)
mc_tree = mc_file.Get("tree")
print "\t %i MC entries" % mc_tree.GetEntries()
print mc_tree.GetTitle()

# set up MC hist
mc_hist = ROOT.TH1D("mc_hist","", n_bins, min_bin, max_bin)
mc_hist.SetLineColor(ROOT.kRed)
mc_hist.SetFillColor(ROOT.kRed)
mc_hist.SetFillStyle(3004)
mc_hist.SetMarkerColor(ROOT.kRed)
mc_hist.SetMarkerStyle(21)
mc_hist.SetMarkerSize(1.5)
mc_hist.SetLineWidth(2)

# grab Struck tree
print "--> Struck file:", struck_filename
struck_file = ROOT.TFile(struck_filename)
struck_tree = struck_file.Get("tree")
print "\t %i Struck entries" % struck_tree.GetEntries()
print struck_tree.GetTitle()

# set up Struck hist
struck_hist = ROOT.TH1D("struck_hist","", n_bins, min_bin, max_bin)
struck_hist.SetXTitle("%s [keV]" % draw_cmd)
struck_hist.SetYTitle("Counts / %i keV" % struck_hist.GetBinWidth(1))
struck_hist.GetYaxis().SetTitleOffset(1.5)
struck_hist.SetLineColor(ROOT.kBlue)
struck_hist.SetFillColor(ROOT.kBlue)
struck_hist.SetFillStyle(3004)
struck_hist.SetMarkerColor(ROOT.kBlue)
struck_hist.SetMarkerStyle(21)
struck_hist.SetMarkerSize(1.5)
struck_hist.SetLineWidth(2)

# speed things up by turning off most branches:
for tree in [mc_tree, struck_tree]:
    tree.SetBranchStatus("*",0) # first turn off all branches
    tree.SetBranchStatus("SignalEnergy",1) 
    tree.SetBranchStatus("nsignals",1) 
    tree.SetBranchStatus("signal_map",1) 
    tree.SetBranchStatus("rise_time_stop95_sum",1) 
    tree.SetBranchStatus("trigger_time",1) 
    if not struck_analysis_parameters.is_tree_MC(tree):
        tree.SetBranchStatus("is_pulser",1) 
        tree.SetBranchStatus("is_bad",1) 

# loop over all channels (if draw_cmd is SignalEnergy, break after first
# iteration)
for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
    if val == 0: continue

    # if draw_cmd is energy1_pz, we are drawing different hists for each
    # channel, so construct selection for that:
    if draw_cmd == "energy1_pz":
        print "--> channel", channel, struck_analysis_parameters.channel_map[channel]
        struck_selection = " && ".join([selection, "channel==%i" % channel])

    # set up the legend
    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    # construct MC drw command
    mc_multiplier = 1.0 
    if struck_analysis_parameters.is_tree_MC(mc_tree):
        mc_multiplier = 1.02
    #mc_draw_cmd = draw_cmd
    #mc_noise = 24.0 # keV
    mc_noise = 0.0 # keV
    mc_draw_cmd = "%s*%s" % (draw_cmd, mc_multiplier)
    if mc_noise > 0.0:
        if draw_cmd == "energy1_pz": mc_noise = struck_analysis_parameters.rms_keV[channel]
        mc_draw_cmd = "%s*%s + %s*noise[0]" % (draw_cmd, mc_multiplier, mc_noise)

    # draw MC hist
    mc_hist.GetDirectory().cd()
    print "mc_draw_cmd:", mc_draw_cmd
    mc_tree.Draw("%s >> %s" % (mc_draw_cmd, mc_hist.GetName()),struck_selection)
    print "\t %i entries in hist" % mc_hist.GetEntries()

    # construct struck draw cmd, draw struck hist
    mc_multiplier = 1.0 
    if struck_analysis_parameters.is_tree_MC(struck_tree):
        mc_multiplier = 1.02
    struck_hist.GetDirectory().cd()
    struck_draw_cmd = "%s*%s" % (draw_cmd, mc_multiplier)
    print "struck_draw_cmd:", struck_draw_cmd
    print "struck_selection:", struck_selection
    struck_tree.Draw("%s >> %s" % (struck_draw_cmd, struck_hist.GetName()),struck_selection)
    print "\t %i entries in hist" % struck_hist.GetEntries()

    # integrate both hists over energy range to determine scaling
    start_bin = struck_hist.FindBin(min_bin)
    stop_bin = struck_hist.FindBin(max_bin)
    try:
        scale_factor = 1.0*struck_hist.Integral(start_bin,stop_bin)/mc_hist.Integral(start_bin,stop_bin)
    except ZeroDivisionError: 
        scale_factor = 1.0
        print "No counts in MC hist!!"
    print "MC scale factor:", scale_factor
    mc_hist.Scale(scale_factor)

    if draw_cmd == "energy1_pz":
        legend.AddEntry(struck_hist, "Data ch %i %s" % (channel, struck_analysis_parameters.channel_map[channel]), "f")
    else:
        legend.AddEntry(struck_hist, "Data", "f")
        #legend.AddEntry(struck_hist, struck_basename, "f")

    #legend.AddEntry(mc_hist, mc_basename, "f")
    legend.AddEntry(mc_hist, "MC", "f")

    # this doesn't work well for low stats:
    #if draw_cmd != "energy1_pz":
    if True:
        struck_hist.SetMaximum() # reset since we keep filling the same hist... 
        y_max = struck_hist.GetMaximum()
        if mc_hist.GetMaximum() > y_max: y_max = mc_hist.GetMaximum()
        struck_hist.SetMaximum(y_max*1.1)

    struck_hist.Draw()
    mc_hist.Draw("hist same")
    struck_hist.Draw("same")
    legend.Draw()
    canvas.Update()
    plotname = "comparison_%s" % draw_cmd
    if "Sum" in draw_cmd:
        plotname = "comparison_test" 
    if draw_cmd == "energy1_pz":
        plotname += "_ch%i" % channel
    plotname += "%ikeV_bins" % bin_width

    # print one "clean" plot
    canvas.Print("%s_%s.pdf" % (plotname, basename))

    # draw some info about cuts on next plot
    pavetext = ROOT.TPaveText(0.12, 0.8, 0.9, 0.9, "ndc")
    pavetext.AddText(struck_selection[:200])
    pavetext.AddText("\nMC amplitude x %.2f, %.1f-keV add'l noise" % (scale_factor, mc_noise))
    pavetext.SetBorderSize(0)
    pavetext.SetFillStyle(0)
    pavetext.Draw()

    # print one plot with details of cuts
    plotname += "_drift_%i_to_%i_" % (drift_time_low*1e3, drift_time_high*1e3)
    plotname += "%i_signals_" % nsignals
    canvas.Update()
    canvas.Print("%s_%s_cuts.pdf" % (plotname, basename))

    if not ROOT.gROOT.IsBatch(): raw_input("any key to continue... ")

    # if we are not looping over all channels, break
    if draw_cmd != "energy1_pz": break

    # end loop over channels

