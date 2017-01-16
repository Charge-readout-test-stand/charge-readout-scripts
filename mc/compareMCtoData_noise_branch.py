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
#drift_time_low = 0.0
#drift_time_high = 8.0
#drift_time_low = 6.4 # Gaosong's cut
#drift_time_high = 8.4 # Gaosong's cut
nsignals = 0 # only consider events where one strip is hit
#nstrips = 1 # only use single-strip channels
#nsignals = 0
# the usual:
struck_selection = []
#struck_selection.append(struck_analysis_cuts.get_standard_cut( # can't use this on old MC
#    nsignals=nsignals,
#    drift_time_high=drift_time_high))
if nsignals == 0:
    struck_selection.append("nsignals>%i" % nsignals)
else:
    struck_selection.append("nsignals==%i" % nsignals)
struck_selection.append( struck_analysis_cuts.get_drift_time_selection(
    drift_time_low=drift_time_low,
    drift_time_high=drift_time_high))
try:
    struck_selection.append(struck_analysis_cuts.get_nstrips_events(nstrips=nstrips))
except:
    pass
#struck_selection.append("(signal_map[6]+signal_map[7]+signal_map[8]+signal_map[20]+signal_map[21]+signal_map[22]==nsignals)")
#struck_selection.append("signal_map[16]==0") # noisy channel
struck_selection = " && ".join(struck_selection)
print "\nselection:"
print struck_selection, "\n"


# hist options
min_bin = 300.0
max_bin = 1400.0
bin_width = 10 # keV
n_bins = int((max_bin - min_bin)/bin_width)

filenames = []
filenames.append("/p/lscratchd/alexiss/mc_slac/red_jobs_0_to_3399.root")
#filenames.append("/g/g17/alexiss/scratch/9thLXe/2016_09_19_overnight/tier3_added/overnight_9thLXe_v3.root")
filenames.append("/p/lscratchd/alexiss/mc_slac/red_mc_cathode_mesh_800.root")

if len(sys.argv) < 3:
    print "provide tier3 files as arguments: MC file, struck data file"
if len(sys.argv) > 1:
    filenames = sys.argv[1:]


canvas = ROOT.TCanvas("canvas","")
canvas.SetLeftMargin(0.12)
canvas.SetGrid(1,1)

tfiles = []
trees = []
hists = []
basenames = []
colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen+1]

for i, filename in enumerate(filenames):

    basename = os.path.splitext(os.path.basename(filename))[0]
    basenames.append(basename)
    # grab tree
    print "--> file:", filename
    tfile = ROOT.TFile(filename)
    tfiles.append(tfile)
    tree = tfile.Get("tree")
    trees.append(tree)
    print "\t %i tree entries" % tree.GetEntries()
    #tree.GetTitle()

    # set up hist
    hist = ROOT.TH1D("hist%i" % i,"", n_bins, min_bin, max_bin)
    hist.SetLineColor(colors[i])
    hist.SetFillColor(colors[i])
    hist.SetFillStyle(3004)
    hist.SetMarkerColor(colors[i])
    hist.SetMarkerStyle(21)
    hist.SetMarkerSize(1.5)
    hist.SetLineWidth(2)
    hists.append(hist)

    # speed things up by turning off most branches:
    tree.SetBranchStatus("*",0) # first turn off all branches
    tree.SetBranchStatus("SignalEnergy",1) 
    tree.SetBranchStatus("nsignals",1) 
    if "signal_map" in struck_selection:
        tree.SetBranchStatus("signal_map",1) 
    tree.SetBranchStatus("rise_time_stop95_sum",1) 
    tree.SetBranchStatus("trigger_time",1) 
    if not struck_analysis_parameters.is_tree_MC(tree):
        print "\t tree is NOT MC"
        tree.SetBranchStatus("is_pulser",1) 
        tree.SetBranchStatus("is_bad",1) 
    else:
        print "\t tree is MC"
    print "\n"

basename = "_".join(basenames)
print "basename:", basename, "\n"

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

    for i, hist in enumerate(hists):

        tree = trees[i]
        print "file", i, ":", os.path.basename(filenames[i])
        print "tree", i, ":", tree.GetTitle()

        # construct draw command
        multiplier = 1.0 
        selection = struck_selection
        if struck_analysis_parameters.is_tree_MC(tree):
            multiplier = 1.01
        else: selection += " && !is_bad && !is_pulser"
        this_draw_cmd = "%s*%s" % (draw_cmd, multiplier)

        mc_noise = 0.0 # keV
        if struck_analysis_parameters.is_tree_MC(tree) and mc_noise > 0.0:
            print "--> adding noise"
            if draw_cmd == "energy1_pz": mc_noise = struck_analysis_parameters.rms_keV[channel]
            this_draw_cmd = "%s*%s + %s*noise[0]" % (draw_cmd, multiplier, mc_noise)

        # draw hist
        hist.GetDirectory().cd()
        print "\tdraw_cmd:", this_draw_cmd
        print "\tselection:", selection
        tree.Draw("%s >> %s" % (this_draw_cmd, hist.GetName()), selection, "goff")
        print "\t%i entries in hist" % hist.GetEntries()

        label = "Data"
        if struck_analysis_parameters.is_tree_MC(tree): label = "MC"
        legend.AddEntry(hist, label, "f")
        #legend.AddEntry(hist, basenames[i], "f")

        print "\n"
        # end loop filling hists


    # integrate both hists over energy range to determine scaling
    start_bin = hists[0].FindBin(min_bin)
    stop_bin = hists[0].FindBin(max_bin)
    for hist in hists[1:]:
        try:
            scale_factor = 1.0*hists[0].Integral(start_bin,stop_bin)/hist.Integral(start_bin,stop_bin)
        except ZeroDivisionError: 
            scale_factor = 1.0
            print "No counts in hist!!"
        print "scale factor:", scale_factor
        hist.Scale(scale_factor)

    if True:
        y_max = 0
        for hist in hists:
            hist.SetMaximum() # reset since we keep filling the same hist... 
            if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()
        hists[0].SetMaximum(y_max*1.1)

    hists[0].Draw()
    for hist in hists[1:]:
        hist.Draw("hist same")
    hists[0].Draw("same")
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
    try: 
        plotname += "_%istrips" % nstrips
    except:
        pass
    canvas.Update()
    canvas.Print("%s_%s_cuts.pdf" % (plotname, basename))

    if not ROOT.gROOT.IsBatch(): raw_input("any key to continue... ")

    # if we are not looping over all channels, break
    if draw_cmd != "energy1_pz": break

    # end loop over channels

