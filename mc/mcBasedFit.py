"""

to do:
* add some energy scaling/calibration

done:
* selecting individual channels; had to switch to binned struck & MC to use channels
* sigma seems to be working
* rise-time cuts are working
* add goodness of fit info
* fix MC hist pdf binning for plots

RooFit manual:
It is not possible to import data from array branches such as Double_t[10]. 

Alexis started from these old files:
  /Users/alexis/software/mjSW/MJOrcaAnalysis/MalbekAnalysis/scripts/BkgModelTools/
      fitPeaks.py
      fitTests/rooFit.py
  /Users/alexis/ewi/malbekWork/bkgSpectrumPrediction/rooFitHistsFits/
      performFit.py
      fitHists.py
"""

import os
import sys
import math
import ROOT
ROOT.gROOT.SetBatch(True)

from ROOT import RooFit

from struck import struck_analysis_parameters


#----------------------------------------------------------
# options
#----------------------------------------------------------

#struck_name = "~/9th_LXe/red_red_overnight_9thLXe_v1.root" # Ubuntu DAQ
#struck_name = "~/9thLXe/red_red_overnight_9thLXe_v1.root" # LLNL
#struck_name = "~/9thLXe/red_overnight_9thLXe_v1.root" # LLNL
#struck_name = "~/9thLXe/overnight_9thLXe_v2.root" # LLNL
#struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_20160919225337_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root" # LLNL
#struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_2016091922*.root" # 4 files, LLNL
#struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_201609192*.root" # 33 files, LLNL
struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_201609200*.root" # 298 files, LLNL

mc_name = "/p/lscratchd/alexiss/mc_slac/red_jobs_0_to_3399.root" # LLNL, white noise
#mc_name = "/p/lscratchd/alexiss/mc_slac/no_noise_hadd_0_to_3999.root" # LLNL, no added noise

use_rise_time = True
sigma_guess_keV = 32.0

energy_var_name = "SignalEnergy"
rise_time_name = "rise_time_stop95_sum"
fit_window_min = 300.0
fit_window_max = 1300.0
hist_min = 0.0
hist_max = 3000.0
bin_width = 10.0
#n_bins = int((fit_window_max - fit_window_min)/bin_width)
#print "n_bins", n_bins

trigger_time = 8.0
#max_drift_time = 9.0
max_drift_time = 8.5
max_drift_time = 8.0

#----------------------------------------------------------
# variables
#----------------------------------------------------------


selection = []
selection.append("nsignals==1")
selection.append("(%s >= %f && %s <= %f)" % (
    rise_time_name,
    trigger_time + struck_analysis_parameters.drift_time_threshold,
    rise_time_name,
    trigger_time + max_drift_time,
))
selection = " && ".join(selection)
print "selection", selection

ch_selection = "channel==7"
mc_ch_selection = "(%s || channel==21)" % ch_selection # X17 & Y17 are symmetric in MC

# make the energy variable
energy_var = ROOT.RooRealVar(
    energy_var_name,
    "%s [keV]" % energy_var_name,
    hist_min,
    hist_max,
)
energy_var.Print()
arg_set = ROOT.RooArgSet(energy_var)
arg_set.Print()

n_range_bins = int((energy_var.getMax() - energy_var.getMin())/bin_width)

#----------------------------------------------------------
# set up Struck Data
#----------------------------------------------------------

#struck_file = ROOT.TFile(struck_name)
#struck_tree = struck_file.Get("tree")
print "\n\n--> creating Struck data set"
struck_tree = ROOT.TChain("tree")
print "n struck files:", struck_tree.Add(struck_name)
# make only some branches active:
struck_tree.SetBranchStatus('*',0)
struck_tree.SetBranchStatus(energy_var_name, 1)
struck_tree.SetBranchStatus(rise_time_name, 1)
struck_tree.SetBranchStatus("channel", 1)
struck_tree.SetBranchStatus("nsignals", 1)
struck_tree.SetBranchStatus("is_bad", 1)
struck_tree.SetBranchStatus("is_pulser", 1)
print "%i entries in struck tree" % struck_tree.GetEntries()

struck_th1d = ROOT.TH1D("struck_th1d","",n_range_bins, hist_min, hist_max)
struck_th1d.GetDirectory().cd()
draw_cmd = "%s >> %s" % (energy_var_name, struck_th1d.GetName())
print "draw_cmd", draw_cmd
struck_tree.Draw(
    draw_cmd, 
    "%s && %s && !is_bad && !is_pulser" % (ch_selection, selection),
    "goff"
)
print "%i entries in hist" % struck_th1d.GetEntries()

struck_hist = ROOT.RooDataHist("struck_hist", "Struck data", ROOT.RooArgList(energy_var), struck_th1d)
#struck_hist.Print("v")
struck_data = struck_hist

print "--> done creating Struck data set\n\n"


#----------------------------------------------------------
# set up MC
#----------------------------------------------------------

print "--> creating unbinned data set"
mc_file = ROOT.TFile(mc_name)
mc_tree = mc_file.Get("tree")
print "%i entries in MC tree" % mc_tree.GetEntries()
# make only some branches active:
struck_tree.SetBranchStatus('*',0)
mc_tree.SetBranchStatus('*',0)
mc_tree.SetBranchStatus(energy_var_name, 1)
mc_tree.SetBranchStatus(rise_time_name, 1)
mc_tree.SetBranchStatus("channel", 1)
mc_tree.SetBranchStatus("nsignals", 1)

#print "n_range_bins", n_range_bins
#energy_var.setBins(n_range_bins) # ok?

# make energy calibration variable
calibration_var = ROOT.RooRealVar(
    "calibration",
    "calibration",
    1.0,
    0.0,
    20.0,
)

# make energy calibration formula
cal_energy = ROOT.RooFormulaVar(
    "cal_energy",
    "%s*calibration" % energy_var_name,
    ROOT.RooArgList(energy_var,calibration_var)
)

mc_th1d = ROOT.TH1D("mc_th1d","",n_range_bins, hist_min, hist_max)
mc_th1d.GetDirectory().cd()
draw_cmd = "%s*1.04 >> %s" % (energy_var_name, mc_th1d.GetName())
print "draw_cmd", draw_cmd
mc_selection = "%s && %s" % (mc_ch_selection, selection)
print "mc_selection", mc_selection
mc_tree.Draw(
    draw_cmd, 
    mc_selection,
    "goff"
)
print "%i entries in hist" % mc_th1d.GetEntries()

mc_hist = ROOT.RooDataHist("mc_hist", "", ROOT.RooArgList(energy_var), mc_th1d)
#mc_hist.Print("v")

mc_hist_pdf = ROOT.RooHistPdf(
    "mc_hist_pdf", 
    "mc_hist_pdf", 
    #ROOT.RooArgSet(cal_energy), # doesn't work?
    ROOT.RooArgSet(energy_var),
    mc_hist, 
    0,
    )
#mc_hist_pdf.Print("v")


#----------------------------------------------------------
# attempts at convolution
#----------------------------------------------------------

# https://root.cern.ch/phpBB3/viewtopic.php?t=10980
# from RooFit_Users_Manual_2.91-33.pdf, p. 47
# Create Gaussian resolution model
mean = ROOT.RooRealVar("mean","mean", 0.0) #, -100, 100) # energy shift

scaling = ROOT.RooRealVar(
    "scaling",
    "scaling",
    20.0,
    0.0,
    200.0,
)

# doesn't seem to work...
mean_shifted = ROOT.RooFormulaVar(
    "mean_shifted",
    #"%s*(scaling-1.0)" % energy_var_name,
    #ROOT.RooArgList(energy_var,scaling)
    "scaling",
    ROOT.RooArgList(scaling)
)

sigma = ROOT.RooRealVar("sigma","sigma",sigma_guess_keV*0.5, 0.0, 200.0)
gaussm = ROOT.RooGaussModel("gaussm","gaussm",energy_var,mean,sigma) 
#gaussm = ROOT.RooGaussian("gaussm","gaussm",energy_var,mean_shifted,sigma) 


# from RooFit_Users_Manual_2.91-33.pdf, p. 44:
#gaussm.setConvolutionWindow(mean, sigma, 5.0) # doesn't work with RooGaussian or RooGaussModel

print "\n\n--> performing convolution"
#conv_pdf = ROOT.RooNumConvPdf ("mc_NumConv_pdf","MC (X) Gaussian",energy_var,gaussm,mc_hist_pdf);
conv_pdf = ROOT.RooFFTConvPdf ("mc_FFTConv_pdf","MC (X) Gaussian",energy_var,gaussm,mc_hist_pdf);
mc_pdf = conv_pdf
print "--> done performing convolution\n\n"

#----------------------------------------------------------
# plotting
#----------------------------------------------------------

print "--> plotting"
energy_var.setRange(fit_window_min, fit_window_max)
frame = energy_var.frame()
frame.SetTitle('')
frame.SetTitleOffset(1.4, 'y')
frame.SetYTitle('Counts / %.2f keV' % bin_width)

legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
legend.SetNColumns(2)

struck_data.plotOn(
    frame,
    RooFit.DrawOption('pz'),
    RooFit.MarkerSize(0.8),
)
entry = legend.AddEntry(frame.getHist(struck_data.GetName()), struck_data.GetTitle(), "p")


#mc_hist_pdf.plotOn(
#    frame,
#    RooFit.DrawOption("l"),
#    #RooFit.LineStyle(ROOT.kDashed),
#    RooFit.LineColor(ROOT.kGreen+2),
#)

mc_pdf.plotOn(
    frame,
    RooFit.Range(fit_window_min, fit_window_max),
    RooFit.DrawOption("l"),
    RooFit.LineColor(ROOT.kRed),
)
entry = legend.AddEntry(mc_pdf, mc_pdf.GetTitle(), "l")
entry.SetLineColor(ROOT.kRed)
entry.SetLineWidth(2)

struck_th1d.SetAxisRange(fit_window_min, fit_window_max)
struck_max = struck_th1d.GetMaximum()*1.1
frame.SetMaximum(struck_max)
canvas = ROOT.TCanvas('canvas', 'canvas')
canvas.SetGrid()
frame.Draw()
legend.Draw()
canvas.Update()
canvas.Print('test.pdf')
if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

#----------------------------------------------------------------
# attempt fits
#----------------------------------------------------------------

print "\n\n\n--> attempting fitting..."

# RooFitResult
# $ROOTSYS/tutorials/roofit/rf607_fitresult.C
fit_result = mc_pdf.fitTo(
    struck_data,
    RooFit.Range(fit_window_min, fit_window_max),
    RooFit.Save(),
    )

sigma.Print()
mean.Print()
scaling.Print()

calibration_var.Print()
cal_energy.Print()

fit_result.Print()
fit_result.Print("v")

print "--> done fitting"

mc_pdf.plotOn(
    frame,
    RooFit.Range(fit_window_min, fit_window_max),
    RooFit.DrawOption("l"),
    RooFit.LineColor(ROOT.kBlue),
)
legend.SetNColumns(3)
entry = legend.AddEntry(mc_pdf, mc_pdf.GetTitle(), "l")
entry.SetLineColor(ROOT.kBlue)
entry.SetLineWidth(2)

struck_th1d.SetAxisRange(fit_window_min, fit_window_max)
frame.SetMaximum(struck_max)
frame.Draw()
legend.Draw()
canvas.Update()
canvas.Print('test_fit.pdf')

frame = energy_var.frame()
frame.SetTitle(mc_selection)
frame.SetTitleOffset(1.4, 'y')
frame.SetYTitle('Counts / %.2f keV' % bin_width)

struck_data.plotOn(
    frame,
    RooFit.DrawOption('pz'),
    RooFit.MarkerSize(0.8),
    #RooFit.Binning(int((fit_window_max - fit_window_min)/bin_width)),
)

mc_pdf.plotOn(
    frame,
    RooFit.Range(fit_window_min, fit_window_max),
    RooFit.DrawOption("l"),
    RooFit.LineColor(ROOT.kBlue),
)

struck_th1d.SetAxisRange(fit_window_min, fit_window_max)
struck_max = struck_th1d.GetMaximum()
frame.SetMaximum(struck_max)

# $ROOTSYS/tutorials/roofit/rf109_chi2residpull.C
chi2 = frame.chiSquare()
print "chi2", chi2

hresid = frame.residHist()
hpull = frame.pullHist()
status = fit_result.status()
n_bins = frame.GetNbinsX()
title = "Residual Distribution: #chi^{2}=%.2f | %i bins | status=%i" % (
    chi2, 
    n_bins,
    status,
)
frame2 = energy_var.frame(RooFit.Title(title))
#frame2.addPlotable(hresid, "P")
frame2.addPlotable(hpull, "P")

canvas.Clear()
canvas.Divide(1,2)
pad = canvas.cd(1)
pad.SetGrid()
frame.Draw()
pad = canvas.cd(2)
pad.SetGrid()
frame2.Draw()
canvas.Update()
canvas.Print('test_fit_resid.pdf')

if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

