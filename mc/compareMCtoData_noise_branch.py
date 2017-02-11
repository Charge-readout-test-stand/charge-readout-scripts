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

#-------------------------------------------------------------------------------
# options
#-------------------------------------------------------------------------------

is_noise_study = False
is_threshold_study = False

draw_cmd = "SignalEnergy" # the usual
#draw_cmd = "energy1_pz" # individual channel spectra
#draw_cmd = "energy_rms1_pz"
#draw_cmd = "Sum$(energy_pz*signal_map)" # testing
#draw_cmd = "energy1" 
#draw_cmd = "energy_rms1" 
#draw_cmd = "baseline_rms*calibration" 
#draw_cmd = "baseline_rms" 

drift_time_high = struck_analysis_parameters.max_drift_time+1.0
drift_time_low = struck_analysis_parameters.drift_time_threshold
#drift_time_low = 6.43 # up to 9th LXe
#drift_time_high = drift_time_high - 2.0

# 8th and 9th:
#drift_time_low = 6.43
#drift_time_high = 9.08-1
#drift_time_high = 42

#drift_time_high = 8.0
#drift_time_low = 6.4 # Gaosong's cut
#drift_time_high = 8.4 # Gaosong's cut, down from 9.08


#nsignals = 2 # only consider events where one strip is hit
nsignals = 0 # conside nsignals>0
nsignals=1
#nsignals = 2

#nstrips = 1 # only use single-strip channels

# hist options
min_bin = 300.0
min_bin = 100.0 # 8th LXe low fields
max_bin = 3000.0
bin_width = 10.0 # keV



#-------------------------------------------------------------------------------

if is_threshold_study:
    min_bin = 0.0
    max_bin = 100.0
    bin_width = 0.5

if is_noise_study:
    drift_time_low = -8.0
    drift_time_high = 42.0 - 8.0

# selections:
struck_selection = []

# these 2 get handled below for specific runs:
#struck_selection.append("!is_bad")
#struck_selection.append("!is_pulser")

if is_threshold_study:
    pass
elif is_noise_study:
    #struck_selection.append("nsignals==%i" % nsignals)
    print "no nsignals for now"
elif nsignals == 0:
    struck_selection.append("nsignals>%i" % nsignals)
else:
    struck_selection.append("nsignals==%i" % nsignals)

if not is_noise_study and not is_threshold_study:
    struck_selection.append( struck_analysis_cuts.get_drift_time_selection(
        drift_time_low=drift_time_low,
        drift_time_high=drift_time_high))
    try:
        struck_selection.append(struck_analysis_cuts.get_nstrips_events(nstrips=nstrips))
    except:
        print "not considering a specific number of strips."
        pass
else:
    print "no drift time cut for now..."

#struck_selection.append("(signal_map[6]+signal_map[7]+signal_map[8]+signal_map[20]+signal_map[21]+signal_map[22]==nsignals)")
#struck_selection.append("signal_map[16]==0") # noisy channel
if is_threshold_study:
    struck_selection.append("signal_map") # for threshold study
struck_selection = " && ".join(struck_selection)
print "\nselection:"
print struck_selection, "\n"


if is_noise_study: # for noise studies
    min_bin = -20.0
    max_bin = 20.0
    bin_width = 0.2
    if "baseline_rms" in draw_cmd or "energy_rms1" in draw_cmd or "energy_rms1_pz" in draw_cmd:
        min_bin = 5.0
        #max_bin = 35.0
        bin_width = 0.2
        max_bin = 100.0
    if "baseline_rms" in draw_cmd:
        max_bin = 60.0 # 09 Feb, for baseline_rms*calibration

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
scale_factor = 1.0

tfiles = []
trees = []
hists = []
basenames = []
colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen+2, ROOT.kViolet]

for i, filename in enumerate(filenames):

    basename = os.path.splitext(os.path.basename(filename))[0]
    basenames.append(basename)
    # grab tree
    print "--> file:", filename
    # is TChain this faster?
    if False:
        # 223m37.657s for 8th, 9th, 11th LXe baseline_rms noise study
        tree = ROOT.TChain("tree")
        tree.Add(filename)
    else:
        # 176m44.941s minutes for 8th, 9th, 11th LXe energy_rms1_pz threshold study
        tfile = ROOT.TFile(filename)
        tree = tfile.Get("tree")
        tfiles.append(tfile)
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
    hist.SetXTitle("Energy [keV]")
    hist.GetYaxis().SetTitleOffset(1.4)
    hist.SetYTitle("Counts / %.1f keV" % hist.GetBinWidth(1))

    # speed things up by turning off most branches:
    tree.SetBranchStatus("*",0) # first turn off all branches
    tree.SetBranchStatus(draw_cmd,1) 
    if not is_threshold_study:
        tree.SetBranchStatus("nsignals",1) 
    if "signal_map" in struck_selection:
        tree.SetBranchStatus("signal_map",1) 
    if not is_noise_study or not is_threshold_study:
        tree.SetBranchStatus("rise_time_stop95_sum",1) 
        tree.SetBranchStatus("trigger_time",1) 
    if not struck_analysis_parameters.is_tree_MC(tree):
        print "\t tree is NOT MC"
        if not "8th" in basename:
            tree.SetBranchStatus("is_pulser",1) 
            tree.SetBranchStatus("is_bad",1) 
    else:
        print "\t tree is MC"
    if not "SignalEnergy" in draw_cmd:
        tree.SetBranchStatus("channel",1) 
    if "calibration" in draw_cmd:
        tree.SetBranchStatus("calibration",1) 
    if "baseline_rms" in draw_cmd:
        tree.SetBranchStatus("baseline_rms",1) 
    if is_noise_study:
        tree.SetBranchStatus("lightEnergy",1) 

    print "\n"

basename = "_".join(basenames)
print "basename:", basename, "\n"

# loop over all channels (if draw_cmd is SignalEnergy, break after first
# iteration)
for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
    if val == 0: continue

    print "---> channel %i: %s" % (channel, struck_analysis_parameters.channel_map[channel])

    # set up the legend
    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    for i, hist in enumerate(hists):

        this_selection = struck_selection
        #print "struck_selection:", struck_selection
        print "this_selection:", this_selection

        tree = trees[i]
        bname = os.path.splitext(os.path.basename(filenames[i]))[0]
        print "\t --> file", i, ":", bname
        print "\t\t tree:", tree.GetTitle()

        isMC = struck_analysis_parameters.is_tree_MC(tree)
        print "\t\t isMC:", isMC

        # construct draw command
        multiplier = 1.0 
        if isMC:
            #multiplier = 1.01 # 8th & 9th LXe
            #multiplier = 0.96 # 10th LXe 
            #multiplier = 0.94 # 10th LXe v3
            multiplier = 1.05 # 11th LXe MC
            if is_noise_study:
                multiplier = 1.0
        else:
            if not "8th" in bname: 
                if is_noise_study:
                    #part = "!is_bad && is_pulser && lightEnergy<20" # noise studies
                    part = "!is_bad && !is_pulser" # noise studies
                else:
                    part = "!is_bad && !is_pulser"
                if this_selection != "" and len(this_selection) > 0:
                    this_selection += " && " + part
                    print "added this_selection to part"
                else:
                    this_selection = part
            # handle different drift lengths:
            if not is_threshold_study and not is_noise_study:
                if "10th" in bname or "11th" in bname or isMC:
                    # longer minimum drift time
                    if drift_time_low < struck_analysis_parameters.drift_time_threshold:
                        this_selection += " && rise_time_stop95_sum-trigger_time>=%f" % struck_analysis_parameters.drift_time_threshold
                else:      
                    # shorter max drift
                    this_selection += " && rise_time_stop95_sum-trigger_time<=%f" % (18.16/2.0)

            # minor mods to energy calibration
            if "10th" in bname:
                multiplier = 1.1
            if "11th" in bname:
                #multiplier = 0.97
                pass
                #this_selection += " && signal_map[0]==0" # Y1-10
                #this_selection += " && signal_map[16]==0" # X1-12

                #print "this_selection:", this_selection
        this_draw_cmd = "%s*%s" % (draw_cmd, multiplier)

        mc_noise = 0.0 # keV
        if isMC and mc_noise > 0:
            print "--> adding noise"
            if "energy1" in draw_cmd: mc_noise = struck_analysis_parameters.rms_keV[channel]
            this_draw_cmd = "%s*%s + %s*noise[0]" % (draw_cmd, multiplier, mc_noise)

        # if draw_cmd is energy1_pz, we are drawing different hists for each
        # channel, so construct selection for that:
        #if "energy1" in draw_cmd:
        if not "SignalEnergy" in draw_cmd:
            part = "channel==%i" % channel
            if this_selection != "" and len(this_selection)>0:
                this_selection = part + " && " + this_selection
            else:
                this_selection = part
            #print "\t\t this_selection:", this_selection

        # draw hist
        hist.GetDirectory().cd()
        print "\t\t draw_cmd:", this_draw_cmd
        print "\t\t this_selection:", this_selection
        #sys.exit() # debugging
        tree.Draw("%s >> %s" % (this_draw_cmd, hist.GetName()), this_selection, "norm goff")
        print "\t\t %i entries in hist" % hist.GetEntries()

        #label = "Data"
        #if isMC: label = "MC"
        label = basenames[i]
        if is_noise_study:
            label += " #sigma=%.1f" % hist.GetRMS()
            label += ", x=%.1f" % hist.GetMean()
            print "\t\t hist mean:", hist.GetMean()
            print "\t\t hist rms:", hist.GetRMS()

        if draw_cmd != "SignalEnergy":
            label += " ch %s" % struck_analysis_parameters.channel_map[channel]
        legend.AddEntry(hist, label, "f")

        print "\n"
        # end loop filling hists


    # integrate both hists over energy range to determine scaling
    if False: # do scaling
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
            val = hist.GetMaximum()
            #val = hist.GetBinContent(hist.FindBin(570))*1.2
            if val > y_max: y_max = val
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
    if not "SignalEnergy" in draw_cmd:
        plotname += "_ch%i" % channel
    plotname += "_%ikeV_bins" % bin_width

    # print one "clean" plot
    #canvas.Print("%s_%s.pdf" % (plotname, basename))

    # draw some info about cuts on next plot
    pavetext = ROOT.TPaveText(0.12, 0.8, 0.9, 0.9, "ndc")
    pavetext.AddText(struck_selection[:200])
    text = "\nMC amplitude x %.2f" % scale_factor
    if mc_noise != 0.0:
        text += "%.1f-keV add'l noise" % mc_noise
    #pavetext.AddText(text)
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
    canvas.SetLogy(1)
    canvas.Print("%s_%s_cuts_log.pdf" % (plotname, basename))

    hists[0].SetMinimum(0)
    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("%s_%s_cuts_lin.pdf" % (plotname, basename))


    if not ROOT.gROOT.IsBatch(): raw_input("any key to continue... ")

    # if we are not looping over all channels, break
    if "SignalEnergy" in draw_cmd: break

    # end loop over channels

