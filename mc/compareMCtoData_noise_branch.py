"""

Compare MC & Struck data

use MC noise branch to smear MC energies. 

"""

import os
import sys
import ROOT

from struck import struck_analysis_cuts
from struck import struck_analysis_parameters

# options
#draw_cmd = "energy1_pz"
draw_cmd = "SignalEnergy"

drift_time_high = struck_analysis_parameters.max_drift_time
drift_time_low = struck_analysis_parameters.drift_time_threshold
#drift_time_high = 8.5
#drift_time_low = 8.0
nsignals = 1
# the usual:
#struck_selection = "nsignals<=%i && rise_time_stop95_sum-trigger_time>%s && rise_time_stop95_sum-trigger_time<%s" % (
#    nsignals, drift_time_low, drift_time_high)

# testing:
struck_selection = struck_analysis_cuts.get_drift_time_cut(
    drift_time_low=drift_time_low, drift_time_high=drift_time_high)
mc_selection = struck_analysis_cuts.get_drift_time_cut(
    drift_time_low=drift_time_low, drift_time_high=None, isMC=True)

#mc_selection = struck_selection

# hist options
min_bin = 300.0
max_bin = 1400.0
bin_width = 10 # keV
n_bins = int((max_bin - min_bin)/bin_width)


if len(sys.argv) < 3:
    print "provide tier3 files as arguments: MC file, struck data file"
    sys.exit(1)

mc_filename = sys.argv[1]
struck_filename = sys.argv[2]

canvas = ROOT.TCanvas("canvas","")
canvas.SetLeftMargin(0.12)
canvas.SetGrid(1,1)

mc_basename = os.path.splitext(os.path.basename(mc_filename))[0]
struck_basename = os.path.splitext(os.path.basename(struck_filename))[0]
basename = "%s_%s" % (mc_basename, struck_basename)

print "--> MC file:", mc_filename
mc_file = ROOT.TFile(mc_filename)
mc_tree = mc_file.Get("tree")
print "\t %i MC entries" % mc_tree.GetEntries()
mc_hist = ROOT.TH1D("mc_hist","", n_bins, min_bin, max_bin)
mc_hist.SetLineColor(ROOT.kRed)
mc_hist.SetFillColor(ROOT.kRed)
mc_hist.SetFillStyle(3004)
mc_hist.SetMarkerColor(ROOT.kRed)
mc_hist.SetMarkerStyle(21)
mc_hist.SetMarkerSize(1.5)
mc_hist.SetLineWidth(2)


print "--> Struck file:", struck_filename
struck_file = ROOT.TFile(struck_filename)
struck_tree = struck_file.Get("tree")
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


for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
    if val == 0: continue

    if draw_cmd == "energy1_pz":
        print "--> channel", channel, struck_analysis_parameters.channel_map[channel]
        struck_selection = " && ".join([struck_selection, "channel==%i" % channel])
        mc_selection = struck_selection

    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    #mc_draw_cmd = draw_cmd
    mc_multiplier = 1.01
    #mc_noise = 24.0 # keV
    mc_noise = 0.0 # keV
    mc_draw_cmd = "%s*%s" % (draw_cmd, mc_multiplier)
    if mc_noise > 0.0:
        if draw_cmd == "energy1_pz": mc_noise = struck_analysis_parameters.rms_keV[channel]
        mc_draw_cmd = "%s*%s + %s*noise[0]" % (draw_cmd, mc_multiplier, mc_noise)

    mc_hist.GetDirectory().cd()
    print "mc_draw_cmd:", mc_draw_cmd
    print "mc_selection:", mc_selection
    mc_tree.Draw("%s >> %s" % (mc_draw_cmd, mc_hist.GetName()),mc_selection)
    print "\t %i entries in hist" % mc_hist.GetEntries()

    struck_hist.GetDirectory().cd()
    print "draw_cmd:", draw_cmd
    print "struck_selection:", struck_selection
    struck_tree.Draw("%s >> %s" % (draw_cmd, struck_hist.GetName()),struck_selection)
    print "\t %i entries in hist" % struck_hist.GetEntries()

    start_bin = struck_hist.FindBin(350.0)
    stop_bin = struck_hist.FindBin(1400.0)

    scale_factor = 1.0*struck_hist.Integral(start_bin,stop_bin)/mc_hist.Integral(start_bin,stop_bin)
    print "MC scale factor:", scale_factor
    mc_hist.Scale(scale_factor)

    legend.AddEntry(mc_hist, "MC", "f")

    if draw_cmd == "energy1_pz":
        legend.AddEntry(struck_hist, "Data ch %i %s" % (channel, struck_analysis_parameters.channel_map[channel]), "f")
    else:
        legend.AddEntry(struck_hist, "Data", "f")

    # this doesn't work well for low stats:
    if False and draw_cmd == "SignalEnergy":
        y_max = struck_hist.GetMaximum()
        if mc_hist.GetMaximum() > y_max: y_max = mc_hist.GetMaximum()
        struck_hist.SetMaximum(y_max*1.1)

    struck_hist.Draw()
    #mc_hist.Draw("hist same")
    legend.Draw()
    canvas.Update()
    plotname = "comparison_%s" % draw_cmd
    if draw_cmd == "energy1_pz":
        plotname += "_ch%i" % channel
    plotname += "_drift_%i_to_%i_" % (drift_time_low*1e3, drift_time_high*1e3)
    plotname += "%i_signals_" % nsignals
    plotname += basename
    canvas.Print("%s.pdf" % plotname)

    pavetext = ROOT.TPaveText(0.12, 0.8, 0.9, 0.9, "ndc")
    pavetext.AddText(struck_selection[:50])
    pavetext.AddText("\nMC amplitude x %.2f, %.1f-keV add'l noise" % (scale_factor, mc_noise))
    pavetext.SetBorderSize(0)
    pavetext.SetFillStyle(0)
    pavetext.Draw()
    canvas.Update()
    canvas.Print("%s_cuts.pdf" % plotname)

    if not ROOT.gROOT.IsBatch():
        raw_input("any key to continue... ")

    if draw_cmd == "SignalEnergy": break

