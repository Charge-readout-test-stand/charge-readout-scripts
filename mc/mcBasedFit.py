"""
to do:
* add some energy scaling/calibration
* make rise-time cuts
* select individual channels
* add goodness of fit info
* fix MC histpdf binning for plots?

notes:
* sigma seems to be working

starting from these old files:

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
struck_name = "~/9thLXe/red_overnight_9thLXe_v1.root" # LLNL
#struck_name = "~/9thLXe/red_overnight_9thLXe_v2.root" # LLNL
#struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_20160919225337_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root" # LLNL

#mc_name = "/p/lscratchd/alexiss/mc_slac/red_jobs_0_to_3399.root" # LLNL, white noise
mc_name = "/p/lscratchd/alexiss/mc_slac/no_noise_hadd_0_to_3999.root" # LLNL, no added noise

use_rise_time = False
sigma_guess_keV = 32.0

energy_var_name = "SignalEnergy"
rise_time_name = "rise_time_stop95_sum"
fit_window_min = 200.0
fit_window_max = 1500.0
bin_width = 10.0
#n_bins = int((fit_window_max - fit_window_min)/bin_width)
#print "n_bins", n_bins

trigger_time = 8.0
max_drift_time = 9.0

#----------------------------------------------------------


# make the energy variable
energy_var = ROOT.RooRealVar(
    energy_var_name,
    'Energy [keV]',
    0.0,
    3000.0,
    #fit_window_min,
    #fit_window_max,
)
energy_var.Print()
if use_rise_time:
    arg_set = ROOT.RooArgSet(energy_var, rise_time_var)

    # make the rise time variable
    rise_time_var = ROOT.RooRealVar(
        rise_time_name,
        'Rise time [#us]',
        trigger_time + struck_analysis_parameters.drift_time_threshold,
        trigger_time + max_drift_time,
    )
    rise_time_var.Print()
else:
    arg_set = ROOT.RooArgSet(energy_var)

#----------------------------------------------------------
# set up Struck Data
#----------------------------------------------------------

struck_file = ROOT.TFile(struck_name)
struck_tree = struck_file.Get("tree")
print "%i entries in struck tree" % struck_tree.GetEntries()
print "--> creating unbinned data set"
# make only the energy branch active:
struck_tree.SetBranchStatus('*',0)
struck_tree.SetBranchStatus(energy_var_name, 1)
if use_rise_time:
    struck_tree.SetBranchStatus(rise_time_name, 1)
struck_data = ROOT.RooDataSet(
    "struck_data",
    "Struck SignalEnergy",
    arg_set,
    ROOT.RooFit.Import(struck_tree),
)
struck_data.Print()
print "--> done creating unbinned data set"

#----------------------------------------------------------
# set up MC
#----------------------------------------------------------

mc_file = ROOT.TFile(mc_name)
mc_tree = mc_file.Get("tree")
print "%i entries in MC tree" % mc_tree.GetEntries()
print "--> creating unbinned data set"
# make only the energy branch active:
mc_tree.SetBranchStatus('*',0)
mc_tree.SetBranchStatus(energy_var_name, 1)
if use_rise_time:
    mc_tree.SetBranchStatus(rise_time_name, 1)
mc_data = ROOT.RooDataSet(
    "mc_data",
    "MC SignalEnergy",
    arg_set,
    ROOT.RooFit.Import(mc_tree),
)
mc_data.Print()
print "--> done creating unbinned data set"
n_range_bins = int((energy_var.getMax() - energy_var.getMin())/bin_width)
print "n_range_bins", n_range_bins
energy_var.setBins(int((energy_var.getMax() - energy_var.getMin())/bin_width)) # ok?
mc_hist = mc_data.binnedClone() # roohist
mc_hist_pdf = ROOT.RooHistPdf(
    "mc_hist_pdf", 
    "mc_hist_pdf", 
    arg_set,
    mc_hist, 
    0,
    )
#mc_pdf = mc_hist_pdf

#----------------------------------------------------------
# attempts at convolution
#----------------------------------------------------------

# https://root.cern.ch/phpBB3/viewtopic.php?t=10980
# from RooFit_Users_Manual_2.91-33.pdf, p. 47
# Create Gaussian resolution model
mean = ROOT.RooRealVar("mean","mean",0.0) #, -1, 1) # energy shift
sigma = ROOT.RooRealVar("sigma","sigma",sigma_guess_keV, 20, 200.0)
gaussm = ROOT.RooGaussModel("gaussm","gaussm",energy_var,mean,sigma) 
#gaussm = ROOT.RooGaussian("gaussm","gaussm",energy_var,mean,sigma) 


# from RooFit_Users_Manual_2.91-33.pdf, p. 44:
#gaussm.setConvolutionWindow(mean, sigma, 5.0) # doesn't work with RooGaussian or RooGaussModel

print "--> performing convolution"
#conv_pdf = ROOT.RooNumConvPdf ("mc_NumConv_pdf","MC  (X) Gaussian",energy_var,gaussm,mc_hist_pdf);
conv_pdf = ROOT.RooFFTConvPdf ("mc_FFTConv_pdf","MC  (X) Gaussian",energy_var,gaussm,mc_hist_pdf);
mc_pdf = conv_pdf
print "--> done performing convolution"

print "--> performing product"

# make the calibration  variable
calibration_var = ROOT.RooRealVar(
    "scaling",
    'scaling',
    1.0,
    0.0,
    2.0,
)
# not working:
#mc_pdf = ROOT.RooProdPdf("mc_conv_x_mult","prod pdf", ROOT.RooArgList(mc_pdf,calibration_var))

#----------------------------------------------------------
# plotting
#----------------------------------------------------------

print "--> plotting"
energy_var.setRange(fit_window_min, fit_window_max)
frame = energy_var.frame()
frame.SetTitle('')
frame.SetTitleOffset(1.4, 'y')
frame.SetYTitle('Counts / %.2f keV' % bin_width)

legend = ROOT.TLegend(0.1, 0.1, 0.9, 0.9)
legend.SetNColumns(2)

struck_data.plotOn(
    frame,
    RooFit.DrawOption('pz'),
    RooFit.MarkerSize(0.8),
    RooFit.Binning(int((fit_window_max - fit_window_min)/bin_width)),
)
legend.AddEntry(struck_data, struck_data.GetTitle(), "pl")

#mc_hist_pdf.plotOn(
#    frame,
#    RooFit.Binning(int((fit_window_max - fit_window_min)/bin_width), fit_window_min, fit_window_max),
#    RooFit.Range(fit_window_min, fit_window_max),
#    RooFit.DrawOption("plz"),
#    RooFit.LineStyle(ROOT.kDashed),
#    RooFit.LineColor(ROOT.kGreen+2),
#    #RooFit.Binning(n_bins),
#)

mc_pdf.plotOn(
    frame,
    RooFit.Range(fit_window_min, fit_window_max),
    RooFit.DrawOption("pzl"),
    RooFit.LineStyle(ROOT.kDashed),
    RooFit.LineColor(ROOT.kRed),
    #RooFit.MarkerColor(ROOT.kRed),
)
legend.AddEntry(mc_pdf, mc_pdf.GetTitle(), "pl")

canvas = ROOT.TCanvas('canvas', 'canvas')
canvas.SetGrid()
frame.Draw()
#legend.Draw()
canvas.Update()
canvas.Print('test.pdf')
if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

#----------------------------------------------------------------
# attempt fits
#----------------------------------------------------------------

print "\n\n\n--> attempting fitting..."
mc_pdf.fitTo(
    struck_data,
    #RooFit.Extended(),
    RooFit.Range(fit_window_min, fit_window_max),
    )

sigma.Print()
mean.Print()
calibration_var.Print()

print "--> done fitting"

struck_data.plotOn(
    frame,
    RooFit.DrawOption('pz'),
    RooFit.MarkerSize(0.8),
    RooFit.Binning(int((fit_window_max - fit_window_min)/bin_width)),
)

mc_pdf.plotOn(
    frame,
    RooFit.Range(fit_window_min, fit_window_max),
    RooFit.DrawOption("pzl"),
    #RooFit.LineStyle(ROOT.kDashed),
    RooFit.LineColor(ROOT.kBlue),
    #RooFit.MarkerColor(ROOT.kRed),
)


frame.Draw()
#legend.Draw()
canvas.Update()
canvas.Print('test_fit.pdf')

if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

