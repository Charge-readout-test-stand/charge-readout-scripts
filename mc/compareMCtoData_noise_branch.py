"""

Compare MC & Struck data

use MC noise branch to smear MC energies. 

"""

import os
import sys
import ROOT

import struck_analysis_parameters

# options
#draw_cmd = "energy1_pz"
draw_cmd = "SignalEnergy"

mc_selection = ""
struck_selection = ""

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
        struck_selection = "channel==%i" % channel

    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    #mc_draw_cmd = draw_cmd
    mc_multiplier = 1.02
    mc_noise = 25.0 # keV
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
    stop_bin = struck_hist.FindBin(1600.0)

    scale_factor = 1.0*struck_hist.Integral(start_bin,stop_bin)/mc_hist.Integral(start_bin,stop_bin)
    print "MC scale factor:", scale_factor
    mc_hist.Scale(scale_factor)

    #legend.AddEntry(mc_hist, "MC x %.2f" % scale_factor , "f")
    legend.AddEntry(mc_hist, "MC", "f")
    if draw_cmd == "energy1_pz":
        legend.AddEntry(struck_hist, "Data ch %i %s" % (channel, struck_analysis_parameters.channel_map[channel]), "f")
    else:
        legend.AddEntry(struck_hist, "Data", "f")

    struck_hist.Draw()
    mc_hist.Draw("hist same")
    legend.Draw()
    canvas.Update()
    canvas.Print("comparison_%s_ch%i.pdf" % (draw_cmd, channel))

    raw_input("any key to continue... ")

    if draw_cmd == "SignalEnergy": break

