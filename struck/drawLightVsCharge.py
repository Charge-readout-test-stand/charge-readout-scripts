import os
import sys
import ROOT

import struck_analysis_parameters
import struck_analysis_cuts

#ROOT.gStyle.SetPalette(51) # deep sea doesn't look good

# 8th LXe overnight, v3, at LLNL:
filename = "/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v3.root"
basename = os.path.splitext(os.path.basename(filename))[0]


tfile = ROOT.TFile(filename)
tree = tfile.Get("tree")
n_entries = tree.GetEntries()

canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid(1,1)
canvas.SetLogz()

#energy_var = "chargeEnergy"

#selection = ""
#selection = struck_analysis_cuts.get_drift_time_cut(drift_time_high=struck_analysis_parameters.max_drift_time)
energy_var = struck_analysis_cuts.get_few_channels_cmd_baseline_rms()
selection = struck_analysis_cuts.get_drift_time_cut(
    drift_time_low=8.0,
    drift_time_high=struck_analysis_parameters.max_drift_time)



print "energy var:", energy_var.split("+")[0] + "+ ..."
print "selection:"
print selection

hist = ROOT.TH2D("hist","",200,100,2000,200,0,2000)
hist.SetTitle("%s: %s  + ..." % (basename, energy_var.split("+")[0]))
hist.SetYTitle("Scintillation Energy")
hist.SetXTitle("Ionization Energy")
hist.GetYaxis().SetTitleOffset(1.2)


hist.GetDirectory().cd()
n_drawn = tree.Draw(
    "lightEnergy*3.0:%s >> hist" % energy_var,
    selection,
    "colz")

print "%i in tree | %i drawn | %i in hist" % (n_entries, n_drawn, hist.GetEntries())

canvas.SetLogz(0)
canvas.Update()
canvas.Print("chargeVsLight_lin_%s.png" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

canvas.SetLogz(1)
canvas.Update()
canvas.Print("chargeVsLight_log%s.png" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

