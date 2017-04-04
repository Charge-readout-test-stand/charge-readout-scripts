import os
import sys
import ROOT

import struck_analysis_parameters
import struck_analysis_cuts

#ROOT.gStyle.SetPalette(51) # deep sea doesn't look good

# input file
# 8th LXe overnight, most recent version, at LLNL:
#filename = "/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe.root"
filename = "~/scratch/mc_slac/red_overnight8thLXe_v6.root" # alexis @ LLNL
filename = sys.argv[1] # or use command-line argument, if provided
basename = os.path.splitext(os.path.basename(filename))[0]


# open file & draw tree
tfile = ROOT.TFile(filename)
tree = tfile.Get("tree")
n_entries = tree.GetEntries()
print "%i entries in tree" % n_entries

# make a canvas
canvas = ROOT.TCanvas("canvas","", 600, 600)
margin = 0.13
canvas.SetMargin(margin, margin, margin, margin)
canvas.SetGrid(1,1)
canvas.SetLogz()

#-------------------------------------------------------------------------------
# options
#-------------------------------------------------------------------------------

# from spe fitting script, pmt_1pe.py
adc_counts_per_spe = 1.27387e+01

energy_var = "SignalEnergy"

drift_time_high = struck_analysis_parameters.max_drift_time-0.5
selection = []
selection.append(struck_analysis_cuts.get_drift_time_selection(drift_time_high=drift_time_high))

#selection = struck_analysis_cuts.get_drift_time_cut( drift_time_low=8.0, drift_time_high=drift_time_high)
#selection = "rise_time_stop95_sum-8>%s && rise_time_stop95_sum-8<%s" % (drift_time_low, drift_time_high)

# for 11th LXe
nsignal_strips = 2
#nsignal_strips = 4
#nsignal_strips = 0
if nsignal_strips > 0:
    selection.append("nsignal_strips==%i" % nsignal_strips)
else:
    selection.append("nsignal_strips>%i" % nsignal_strips)

selection.append("nXsignals==1 && nYsignals==1")

selection = " && ".join(selection)

basename += "_%isignalstrips" % nsignal_strips

#-------------------------------------------------------------------------------

# turn off most branches for speed:
tree.SetBranchStatus("*",0)
tree.SetBranchStatus("SignalEnergy",1)
tree.SetBranchStatus("lightEnergy",1)
tree.SetBranchStatus("nsignals",1)
tree.SetBranchStatus("is_bad",1)
tree.SetBranchStatus("is_pulser",1)
tree.SetBranchStatus("channel",1)
tree.SetBranchStatus("calibration",1)
#tree.SetBranchStatus("energy1_pz",1)
tree.SetBranchStatus("trigger_time",1)
tree.SetBranchStatus("rise_time_stop95_sum",1)
#tree.SetBranchStatus("rise_time_stop95",1)
if "nXsignals" in selection:
    tree.SetBranchStatus("nXsignals",1)
if "nYsignals" in selection:
    tree.SetBranchStatus("nYsignals",1)
if "nsignal_strips" in selection:
    tree.SetBranchStatus("nsignal_strips",1)

# print some info
print "energy var:", energy_var[:100]
print "selection:"
print selection

n_bins = 150
max_bin = 2000
hist = ROOT.TH2D("hist","",n_bins,0,max_bin,n_bins,0,max_bin)
hist.SetTitle("%s: %s {%s}" % (basename, energy_var, selection))
hist.SetYTitle("Scintillation Energy")
hist.SetXTitle("Ionization Energy")
hist.GetYaxis().SetTitleOffset(1.6)
hist.GetXaxis().SetTitleOffset(1.2)

lightEnergy_multiplier = 0.95
hist.GetDirectory().cd()
n_drawn = tree.Draw(
    "lightEnergy*%s:%s >> hist" % (lightEnergy_multiplier, energy_var),
    selection,
    "colz")

print "%i in tree | %i drawn | %i in hist" % (n_entries, n_drawn, hist.GetEntries())

canvas.SetLogz(0)
canvas.Update()
canvas.Print("chargeVsLight_lin_%s.png" % basename)
#if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

canvas.SetLogz(1)
canvas.Update()
canvas.Print("chargeVsLight_log_%s.png" % basename)

line = ROOT.TLine(0.0,0.0,2000.0,2000.0)
line.SetLineWidth(2)
line.SetLineStyle(2)
line.Draw()
canvas.Update()
canvas.Print("chargeVsLight_log_line_%s.png" % basename)

if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

canvas = ROOT.TCanvas("acanvas","")
canvas.SetGrid()
canvas.cd()

# set up 1d charge and light hists:
n_bins = 290
chargeHist = ROOT.TH1D("chargeHist","",n_bins, 100, 3000)
chargeHist.SetLineWidth(2)
chargeHist.SetLineColor(ROOT.kBlue)
chargeHist.GetYaxis().SetTitleOffset(1.3)
chargeHist.SetXTitle("Energy [keV]")
chargeHist.SetYTitle("Counts / %.1f keV" % chargeHist.GetBinWidth(1))
lightHist = chargeHist.Clone("lightHist")
lightHist.SetLineColor(ROOT.kRed)

legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
legend.SetNColumns(2)
legend.AddEntry(chargeHist, "Ionization")
legend.AddEntry(lightHist, "Scintillation")

# fill & draw 1-d hists
tree.Draw("SignalEnergy >> chargeHist",selection)
tree.Draw("lightEnergy*%s >> lightHist" % lightEnergy_multiplier,selection,"same")
legend.Draw()

# print log scale
canvas.SetLogy(1)
canvas.Update()
canvas.Print("lightAndCharge_%s_log.pdf" % basename)
#if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

# print lin scale
canvas.SetLogy(0)
canvas.Update()
canvas.Print("lightAndCharge_%s_lin.pdf" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

# try to draw lightEnergy with x axis in number of PEs
npeHist = ROOT.TH1D("npeHist","",n_bins, 10, 300)
npeHist.SetLineWidth(2)
npeHist.SetLineColor(ROOT.kBlue)
npeHist.GetYaxis().SetTitleOffset(1.3)
npeHist.SetXTitle("Number of photoelectrons")
npeHist.SetYTitle("Counts / %.1f PE" % npeHist.GetBinWidth(1))
draw_cmd = "lightEnergy*%f/calibration[%i]/%f >> npeHist" % (
        lightEnergy_multiplier, 
        struck_analysis_parameters.pmt_channel,
        adc_counts_per_spe,
    )
print "draw_cmd:", draw_cmd
npeHist.SetTitle("%s {%s}" % (draw_cmd, selection))
tree.Draw(draw_cmd, selection)

canvas.SetLogy(1)
canvas.Update()
canvas.Print("npe_%s_log.pdf" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

canvas.SetLogy(0)
canvas.Update()
canvas.Print("npe_%s_lin.pdf" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")

npeHist.Rebin(2)
npeHist.SetYTitle("Counts / %.1f PE" % npeHist.GetBinWidth(1))
max_bin_center = npeHist.GetBinCenter(npeHist.GetMaximumBin())
print "max bin center:", max_bin_center 
title = "max bin center: %.1f #pm %.1f, %.2f ADC counts per PE" % (
    max_bin_center,
    npeHist.GetBinWidth(1),
    adc_counts_per_spe,
    )

npeHist.SetTitle(title)
canvas.SetLogy(0)
canvas.Update()
canvas.Print("npe_%s_lin_rebin.pdf" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue... ")



