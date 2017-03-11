"""
compare results from nEXO digi studies.

copied from compareMCtoData_noise_branch.py

one sample processed event:

    ======> EVENT:0
     EventNumber     = 0
     Energy          = 2.4578
     GenX            = -138.617
     GenY            = -163.914
     GenZ            = 182.2
     ChannelChargeSum = 102714
     NumChannels     = 7
     noise_electrons = 200
     W_value         = 0.0248756
     ADCunits_per_keV = 0.4096
     sampling_freq_Hz = 4e+06
     digitizer_bits  = 11
     n_baseline_samples = 100
     n_channels_hit  = 7
     WFTileId        = 63, 
                      63, 63, 63, 63, 63, 63
     WFLocalId       = 40, 
                      17, 18, 41, 19, 42, 43
     WFChannelCharge = 1, 
                      10729, 50750, 23827, 1, 17402, 
                      4
     is_hit_MC       = 0
     SignalEnergy    = 2490.75
     ChEnergy        = -13.7207, 
                      251.904, 1247.44, 575.366, -13.4033, 416.04, 
                      -14.4043
     signal_map      = 0, 
                      1, 1, 1, 0, 1, 0
     nsignals        = 4
     smoothed_max    = 2499.66
     rise_time_stop10 = 45
     rise_time_stop20 = 48.5
     rise_time_stop30 = 50
     rise_time_stop40 = 51
     rise_time_stop50 = 51.75
     rise_time_stop60 = 52
     rise_time_stop70 = 52
     rise_time_stop80 = 52
     rise_time_stop90 = 52
     rise_time_stop95 = 52
     rise_time_stop99 = 52

"""

import os
import sys
import ROOT
ROOT.gROOT.SetBatch(True)


#-------------------------------------------------------------------------------
# options
#-------------------------------------------------------------------------------

is_noise_study = False
is_threshold_study = False

#draw_cmd = "SignalEnergy" # the usual
#draw_cmd = "ChEnergy" # channel energy 
#draw_cmd = "Energy*1e3"
#draw_cmd = "ChannelChargeSum" # NTE, I think 
#draw_cmd = "rise_time_stop95 - n_baseline_samples/sampling_freq_Hz*1e6"
draw_cmd = "rise_time_stop90 - rise_time_stop10"
#draw_cmd = "nsignals+0.5"

#nsignals = 1 # only consider events where one strip is hit
#nsignals = 2
nsignals = 0 # consider nsignals>0


# hist options
min_bin = 0.0 # 8th LXe low fields
max_bin = 3000.0
bin_width = 10.0 

if draw_cmd == "SignalEnergy":
    min_bin = 2000
    bin_width = 5.0

if draw_cmd == "Energy*1e3":
    min_bin = 2400
    max_bin = 2500
    bin_width = 1.0

if "rise_time_stop" in draw_cmd:
    min_bin = -0.125
    max_bin = 800.0+min_bin
    bin_width = 10.0 
if "rise_time_stop90 - rise_time_stop10" in draw_cmd:
    max_bin = 40.0+min_bin
    #max_bin = 100.0
    bin_width = 0.25
    #bin_width = 0.25 # for checking sampling freq
if "nsignals" in draw_cmd:
    min_bin = 0.0
    max_bin = 40.0
    bin_width = 1.0
if "ChannelChargeSum" in draw_cmd:
    min_bin = 70000.0
    max_bin = 120000.0
    bin_width = (max_bin-min_bin)/200.0


#-------------------------------------------------------------------------------

if is_threshold_study:
    min_bin = 0.0
    max_bin = 50.0
    bin_width = 0.5

# selections:
selection = []
selection.append("Energy*1e3>2450") # select full-energy peak

if draw_cmd == "SignalEnergy" or draw_cmd == "ChannelChargeSum":
    selection.append("Energy*1e3>2450") # select full-energy peak
else:
    selection.append("%s>0" % draw_cmd)

# specify nsignals
if nsignals == 0:
    selection.append("nsignals>%i" % nsignals)
    #pass
else:
    selection.append("nsignals==%i" % nsignals)

if draw_cmd == "ChEnergy":
    selection.append("signal_map") # for threshold study
selection = " && ".join(selection)
print "\nselection:"
print selection, "\n"


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


if len(sys.argv) < 2:
    print "provide tier3 files as arguments: MC file"
    sys.exit()
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
    #hist.SetMarkerColor(colors[i])
    #hist.SetMarkerStyle(21)
    #hist.SetMarkerSize(1.5)
    hist.SetLineWidth(2)
    hist.Sumw2(True)
    hists.append(hist)
    hist.SetXTitle(draw_cmd)
    hist.GetYaxis().SetTitleOffset(1.4)
    hist.SetYTitle("Counts / %.1f" % hist.GetBinWidth(1))
    if "Energy" in draw_cmd:
        hist.SetYTitle("Counts / %.1f keV" % hist.GetBinWidth(1))
        #hist.SetXTitle("Energy [keV]")
    if "rise_time_stop" in draw_cmd:
        hist.SetYTitle("Counts / %s #mus" % hist.GetBinWidth(1))
        hist.SetXTitle("%s [#mus]" % draw_cmd)
    if "n_baseline_samples" in draw_cmd and "rise_time_stop" in draw_cmd:
        hist.SetXTitle("Drift time [#mus]")

    # speed things up by turning off most branches:
    tree.SetBranchStatus("*",0) # first turn off all branches
    tree.SetBranchStatus("Energy", 1)
    tree.SetBranchStatus(draw_cmd, 1)
    tree.SetBranchStatus("nsignals",1) 
    if "SignalEnergy" in draw_cmd:
        tree.SetBranchStatus("SignalEnergy",1) 
    if "signal_map" in selection:
        tree.SetBranchStatus("signal_map",1) 
    if "rise_time_stop95" in draw_cmd:
        tree.SetBranchStatus("rise_time_stop95",1) 
    if "rise_time_stop90" in draw_cmd:
        tree.SetBranchStatus("rise_time_stop90",1) 
    if "rise_time_stop10" in draw_cmd:
        tree.SetBranchStatus("rise_time_stop10",1) 
    if "n_baseline_samples" in draw_cmd:
        tree.SetBranchStatus("n_baseline_samples",1) 
    if "sampling_freq_Hz" in draw_cmd:
        tree.SetBranchStatus("sampling_freq_Hz",1) 
    print "\n"

basename = "_".join(basenames)
print "basename:", basename, "\n"


# set up the legend
legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
#legend.SetNColumns(2)
legend.SetFillStyle(0)
legend.SetFillColor(0)

for i, hist in enumerate(hists):

    this_selection = selection
    #print "selection:", selection
    print "this_selection:", this_selection

    tree = trees[i]
    bname = os.path.splitext(os.path.basename(filenames[i]))[0]
    print "\t --> file", i, ":", bname
    print "\t\t tree:", tree.GetTitle()

    # draw hist
    hist.GetDirectory().cd()
    #if i == 1: draw_cmd += "*0.97" # FIXME -- testing NEST beta scale
    print "\t\t draw_cmd:", draw_cmd
    print "\t\t this_selection:", this_selection
    #sys.exit() # debugging
    tree.Draw("%s >> %s" % (draw_cmd, hist.GetName()), this_selection, "norm goff")
    #tree.Draw("%s >> %s" % (draw_cmd, hist.GetName()), this_selection, "goff")
    print "\t\t %i entries in tree" % tree.GetEntries()
    print "\t\t %i entries in hist" % hist.GetEntries()

    label = basenames[i].split("proc_")
    label = label[-1]
    label = label.split("_digi")
    label = label[0]
    label += " (%.1e evts)" % hist.GetEntries()
    #part = " #bar{x}: %.2e, #sigma/E: %.2f" % (
    part = " #bar{x}: %.2e, RMS/E: %.2f" % (
        hist.GetMean(),
        hist.GetRMS()/hist.GetMean()*100.0,
    ) + " %"
    #label += part
    print "\t\t", label
    print "\t\t", part

    if is_noise_study:
        label += " #sigma=%.1f" % hist.GetRMS()
        label += ", x=%.1f" % hist.GetMean()
        print "\t\t hist mean:", hist.GetMean()
        print "\t\t hist rms:", hist.GetRMS()

    legend.AddEntry(hist, label, "f")
    #legend.AddEntry(hist, part, "")

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

#option = "e hist"
option = "hist"
hists[0].Draw(option)
for hist in hists[1:]:
    hist.Draw("%s same" % option)
#hists[0].Draw("%s same" % option)
legend.Draw()
canvas.Update()
plotname = "comparison_%s" % draw_cmd
if draw_cmd == "Energy*1e3":
    plotname = "Energy"
if "nsignals" in draw_cmd:
    plotname = "nsignals"
if "rise_time_stop" in draw_cmd:
    plotname = "comparison_rise_time"
if "rise_time_stop" in draw_cmd and  "n_baseline_samples" in draw_cmd:
    plotname = "comparison_drift_time"
    
if "Sum" in draw_cmd:
    plotname = "comparison_test" 
plotname += "_%ibins" % bin_width

# print one "clean" plot
#canvas.Print("%s_%s.pdf" % (plotname, basename))

# draw some info about cuts on next plot
#pavetext = ROOT.TPaveText(0.12, 0.8, 0.9, 0.9, "ndc") # full width
pavetext = ROOT.TPaveText(0.12, 0.86, 0.9, 0.9, "ndc")
pavetext.AddText(selection[:200])
pavetext.SetBorderSize(0)
pavetext.SetFillStyle(0)
pavetext.Draw()

# print one plot with details of cuts
if nsignals != 0:
    plotname += "%i_signals_" % nsignals
canvas.Update()
canvas.SetLogy(1)
canvas.Print("%s_%s_cuts_log.pdf" % (plotname, basename))

hists[0].SetMinimum(0)
canvas.SetLogy(0)
canvas.Update()
canvas.Print("%s_%s_cuts_lin.pdf" % (plotname, basename))


if not ROOT.gROOT.IsBatch(): raw_input("any key to continue... ")


