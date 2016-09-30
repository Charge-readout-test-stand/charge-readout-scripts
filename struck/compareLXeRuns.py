"""

copied from compareMCtoData_noise_branch.py

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
drift_time_high = 9.0
#drift_time_high = 0.0
#drift_time_low = 0.0
nsignals = 0
# the usual:
selection = "nsignals>=%i && rise_time_stop95_sum-trigger_time>%s && rise_time_stop95_sum-trigger_time<%s" % ( nsignals, drift_time_low, drift_time_high)
#selection = "nsignals==1 && rise_time_stop95_sum-8>8.5&&rise_time_stop95_sum-8<8.9&&rise_time_stop50_sum-8>7" # like Conti
#selection += "&& rise_time_stop50_sum>8.0"
#selection += " && signal_map[16]==0 && signal_map[7]==0 && signal_map[21]==0"
#selection += " && signal_map[16]==0"
#selection = "nsignals>=0"


# hist options
min_bin = 300.0
max_bin = 1400.0
bin_width = 5 # keV
n_bins = int((max_bin - min_bin)/bin_width)


if len(sys.argv) < 3:
    print "provide tier3 files as arguments: struck file 1 , struck file 2"
    sys.exit(1)

struck1_filename = sys.argv[1]
struck_filename = sys.argv[2]

canvas = ROOT.TCanvas("canvas","")
canvas.SetLeftMargin(0.12)
canvas.SetGrid(1,1)

struck1_basename = os.path.splitext(os.path.basename(struck1_filename))[0]
struck_basename = os.path.splitext(os.path.basename(struck_filename))[0]
basename = "%s_%s" % (struck1_basename, struck_basename)

print "--> Struck file 1:", struck1_filename
struck1_file = ROOT.TFile(struck1_filename)
struck1_tree = struck1_file.Get("tree")
print "\t %i entries" % struck1_tree.GetEntries()
struck1_hist = ROOT.TH1D("struck1_hist","", n_bins, min_bin, max_bin)
struck1_hist.SetLineColor(ROOT.kRed)
struck1_hist.SetFillColor(ROOT.kRed)
struck1_hist.SetFillStyle(3004)
struck1_hist.SetMarkerColor(ROOT.kRed)
struck1_hist.SetMarkerStyle(21)
struck1_hist.SetMarkerSize(1.5)
struck1_hist.SetLineWidth(2)


print "--> Struck file 2:", struck_filename
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
        struck_selection = " && ".join([selection, "channel==%i" % channel])
    else:
        struck_selection = selection

    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    struck1_hist.GetDirectory().cd()
    print "struck1_draw_cmd:", draw_cmd
    print "struck1_selection:", struck_selection
    struck1_tree.Draw("%s >> %s" % (draw_cmd, struck1_hist.GetName()),struck_selection)
    print "\t %i entries in hist" % struck1_hist.GetEntries()

    struck_hist.GetDirectory().cd()
    print "draw_cmd:", draw_cmd
    print "struck_selection:", struck_selection
    struck_tree.Draw("%s >> %s" % (draw_cmd, struck_hist.GetName()),struck_selection)
    print "\t %i entries in hist" % struck_hist.GetEntries()

    start_bin = struck_hist.FindBin(300.0)
    stop_bin = struck_hist.FindBin(1400.0)

    try:
        scale_factor = 1.0*struck_hist.Integral(start_bin,stop_bin)/struck1_hist.Integral(start_bin,stop_bin)
    except ZeroDivisionError: 
        scale_factor = 1.0
        print "No counts in  hist 1!!"
    print "hist 1 scale factor:", scale_factor
    struck1_hist.Scale(scale_factor)

    if draw_cmd == "energy1_pz":
        legend.AddEntry(struck_hist, "Data ch %i %s" % (channel, struck_analysis_parameters.channel_map[channel]), "f")
    else:
        legend.AddEntry(struck_hist, "Data", "f")
    legend.AddEntry(struck1_hist, "Data 2", "f")

    # this doesn't work well for low stats:
    #if draw_cmd != "energy1_pz":
    if True:
        struck_hist.SetMaximum() # reset since we keep filling the same hist... 
        y_max = struck_hist.GetMaximum()
        if struck1_hist.GetMaximum() > y_max: y_max = struck1_hist.GetMaximum()
        struck_hist.SetMaximum(y_max*1.1)

    struck_hist.Draw()
    struck1_hist.Draw("hist same")
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

