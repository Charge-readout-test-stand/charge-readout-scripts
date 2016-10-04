"""


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

from ROOT import RooFit
from ROOT import RooDataSet
from ROOT import RooArgSet

from struck import struck_analysis_parameters


#----------------------------------------------------------
# options
#----------------------------------------------------------

#struck_name = "~/9th_LXe/red_red_overnight_9thLXe_v1.root" # Ubuntu DAQ
#struck_name = "~/9thLXe/red_red_overnight_9thLXe_v1.root" # LLNL
#struck_name = "~/9thLXe/red_overnight_9thLXe_v1.root" # LLNL
struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_20160919225337_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root" # LLNL
mc_name = "/p/lscratchd/alexiss/mc_slac/red_jobs_0_to_3399.root" # LLNL

energy_var_name = "SignalEnergy"
rise_time_name = "rise_time_stop95_sum"
fit_window_min = 200.0
fit_window_max = 1500.0
bin_width = 10.0
n_bins = int((fit_window_max - fit_window_min)/bin_width)

trigger_time = 8.0
max_drift_time = 9.0
selection = "%s > %f && %s < %f" % (
    rise_time_name,
    struck_analysis_parameters.drift_time_threshold + trigger_time,
    rise_time_name,
    max_drift_time + trigger_time,
)
print selection

#----------------------------------------------------------

sigma_guess_keV = 32.0
# Per IEEE standard 325-1996, use 5 to 10 bins per FWHM.
# Use floor and +0.5 to round to nearest integer.
#n_bins = int( math.floor(
#    5.0 * (fit_window_max - fit_window_min) / (sigma_guess_keV * 2.3548)
#    + 0.5
#) )
#bin_width = (fit_window_max - fit_window_min)/n_bins

# make the energy variable
energy_var = ROOT.RooRealVar(
    energy_var_name,
    'Energy [keV]',
    fit_window_min,
    fit_window_max,
)
energy_var.Print()

# make the rise time variable
rise_time_var = ROOT.RooRealVar(
    rise_time_name,
    'Rise time [#us]',
    trigger_time + struck_analysis_parameters.drift_time_threshold,
    trigger_time + max_drift_time,
)
rise_time_var.Print()


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
struck_tree.SetBranchStatus(rise_time_name, 1)
struck_data = ROOT.RooDataSet(
    "struck_data",
    "Struck SignalEnergy",
    #ROOT.RooArgSet(energy_var),
    ROOT.RooArgSet(energy_var, rise_time_var),
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
mc_tree.SetBranchStatus(rise_time_name, 1)
mc_data = ROOT.RooDataSet(
    "mc_data",
    "MC SignalEnergy",
    #ROOT.RooArgSet(energy_var),
    ROOT.RooArgSet(energy_var, rise_time_var),
    ROOT.RooFit.Import(mc_tree),
)
mc_data.Print()
print "--> done creating unbinned data set"
mc_hist = mc_data.binnedClone()
mc_pdf = ROOT.RooHistPdf(
    "mc_pdf", 
    "mc_pdf", 
    RooArgSet(energy_var, rise_time_var),
    mc_hist, 
    0,
    )

frame = energy_var.frame()
frame.SetTitle('')
frame.SetTitleOffset(1.4, 'y')
frame.SetYTitle('Counts / %.2f keV' % bin_width)

# from RooFit_Users_Manual_2.91-33.pdf, p. 47
# Create Gaussian resolution model
mean = ROOT.RooRealVar("mean","mean",0)
sigma = ROOT.RooRealVar("sigma","sigma",sigma_guess_keV, 0, 100)
gaussm = ROOT.RooGaussModel("gaussm","gaussm",energy_var,mean,sigma) 
gaussm.Print()

#----------------------------------------------------------
# plotting
#----------------------------------------------------------

legend = ROOT.TLegend(0.1, 0.1, 0.9, 0.9)
legend.SetNColumns(2)

struck_data.plotOn(
    frame,
    RooFit.DrawOption('pz'),
    RooFit.MarkerSize(0.8),
    RooFit.Binning(n_bins),
)
legend.AddEntry(struck_data, struck_data.GetTitle(), "pl")

#mc_data.plotOn(
#    frame,
#    RooFit.DrawOption('pzl'),
#    RooFit.MarkerSize(1.0),
#    RooFit.Binning(n_bins),
#    RooFit.LineStyle(ROOT.kDashed),
#    RooFit.LineColor(ROOT.kRed+2),
#    RooFit.MarkerColor(ROOT.kRed),
#)

mc_pdf.plotOn(
    frame,
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

raw_input("enter to continue ")

