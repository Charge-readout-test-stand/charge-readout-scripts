#!/usr/bin/env python

"""
Extract parameters (energy, risetime, etc.) from a waveform. 
"""


import os
import sys

from ROOT import gROOT
from ROOT import TFile
from ROOT import TTree
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TH1D
from ROOT import gSystem


gSystem.Load("$EXOLIB/lib/libEXOROOT")
from ROOT import CLHEP
from ROOT import EXODoubleWaveform
from ROOT import EXOBaselineRemover
from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother
from ROOT import EXOPoleZeroCorrection

import struck_analysis_parameters


def do_draw(exo_wfm,title=""):
    
    if gROOT.IsBatch(): return
    # a canvas for drawing, if debugging:
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    canvas.cd()
    hist = exo_wfm.GimmeHist("hist")
    hist.SetTitle(title)
    hist.SetLineWidth(2)
    #hist.SetAxisRange(4,6)
    hist.Draw()

    canvas.Update()
    val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

    print val
    if (val == 'q' or val == 'Q'): sys.exit(1) 
    if val == 'b': gROOT.SetBatch(True)
    #if val == 'p': canvas.Print("entry_%i_proc_wfm_%s.png" % (i_entry, basename,))
    


def create_basename(filename):

    # construct a basename to use as output file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    basename = "_".join(basename.split("_")[1:])
    return basename


def create_outfile_name(filename):

    basename = create_basename(filename)
    out_filename = "tier3_%s.root" % basename
    return out_filename


def get_wfmparams(
    exo_wfm, 
    wfm_length, 
    sampling_freq_Hz, 
    n_baseline_samples, 
    calibration, 
    decay_time, 
    is_pmtchannel
):
    exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
    energy_wfm = EXODoubleWaveform(exo_wfm)

    # calculate wfm max and min:
    wfm_max = exo_wfm.GetMaxValue()
    wfm_min = exo_wfm.GetMinValue()

    # remove the baseline
    baseline_remover = EXOBaselineRemover()
    baseline_remover.SetBaselineSamples(n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)
    baseline_mean = baseline_remover.GetBaselineMean()
    baseline_rms = baseline_remover.GetBaselineRMS()

    # measure energy before PZ correction
    baseline_remover.SetStartSample(wfm_length - n_baseline_samples - 1)
    baseline_remover.Transform(exo_wfm, energy_wfm)
    energy = baseline_remover.GetBaselineMean()*calibration
    energy_rms = baseline_remover.GetBaselineRMS()*calibration
    if is_pmtchannel: # for PMT channel, use GetMaxValue()
        energy = exo_wfm.GetMaxValue()*calibration
    do_draw(energy_wfm, "after baseline_remover")

    # measure energy before PZ correction, use 2x n_baseline_samples
    baseline_remover.SetBaselineSamples(2*n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)
    baseline_remover.SetStartSample(wfm_length - 2*n_baseline_samples - 1)
    baseline_remover.Transform(exo_wfm, energy_wfm)
    energy1 = baseline_remover.GetBaselineMean()*calibration
    energy_rms1 = baseline_remover.GetBaselineRMS()*calibration

    # correct for exponential decay
    pole_zero = EXOPoleZeroCorrection()
    pole_zero.SetDecayConstant(decay_time)
    pole_zero.Transform(exo_wfm, energy_wfm)
    do_draw(energy_wfm, "after PZ correction")

    # measure energy after PZ correction
    baseline_remover.SetBaselineSamples(n_baseline_samples)
    baseline_remover.SetStartSample(wfm_length - n_baseline_samples - 1)
    baseline_remover.Transform(energy_wfm)
    energy_pz = baseline_remover.GetBaselineMean()*calibration
    energy_rms_pz = baseline_remover.GetBaselineRMS()*calibration
 
    # measure energy after PZ correction, use 2x n_baseline_samples
    baseline_remover.SetBaselineSamples(2*n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)

    pole_zero.Transform(exo_wfm, energy_wfm)

    # create calibrated wfm to be added to sum wfm
    calibrated_wfm = EXODoubleWaveform(energy_wfm)
    calibrated_wfm *= calibration

    baseline_remover.SetStartSample(wfm_length - 2*n_baseline_samples - 1)
    baseline_remover.Transform(energy_wfm)
    energy1_pz = baseline_remover.GetBaselineMean()*calibration
    energy_rms1_pz = baseline_remover.GetBaselineRMS()*calibration

    return (
        baseline_mean, 
        baseline_rms,
        energy, 
        energy_rms, 
        energy1, 
        energy_rms1, 
        energy_pz, 
        energy_rms_pz, 
        energy1_pz, 
        energy_rms1_pz,
        calibrated_wfm,
        wfm_max,
        wfm_min,
    )

def do_risetime_calc(rise_time_calculator, threshold_percent, wfm, max_val, period):
    rise_time_calculator.SetFinalThresholdPercentage(threshold_percent)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(wfm, wfm)
    return rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond




def get_risetimes(exo_wfm, wfm_length, sampling_freq_Hz):
    exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
    new_wfm = EXODoubleWaveform(exo_wfm)

    period = exo_wfm.GetSamplingPeriod()

    # perform some smoothing -- be careful because this changes the rise time
    smoother = EXOSmoother()
    smoother.SetSmoothSize(5)
    #smoother.SetSmoothSize(50)
    smoother.Transform(exo_wfm, new_wfm) 

    smoothed_max = new_wfm.GetMaxValue()
    max_val = new_wfm.GetMaxValue() # smoothed max

    rise_time_calculator = EXORisetimeCalculation()
    rise_time_calculator.SetPulsePeakHeight(max_val)

    # rise time calculator thresholds are called percentage, but they
    # are really fractions...
    rise_time_stop10 = do_risetime_calc(rise_time_calculator, 0.10, exo_wfm, max_val, period)
    rise_time_stop20 = do_risetime_calc(rise_time_calculator, 0.20, exo_wfm, max_val, period)
    rise_time_stop30 = do_risetime_calc(rise_time_calculator, 0.30, exo_wfm, max_val, period)
    rise_time_stop40 = do_risetime_calc(rise_time_calculator, 0.40, exo_wfm, max_val, period)
    rise_time_stop50 = do_risetime_calc(rise_time_calculator, 0.50, exo_wfm, max_val, period)
    rise_time_stop60 = do_risetime_calc(rise_time_calculator, 0.60, exo_wfm, max_val, period)
    rise_time_stop70 = do_risetime_calc(rise_time_calculator, 0.70, exo_wfm, max_val, period)
    rise_time_stop80 = do_risetime_calc(rise_time_calculator, 0.80, exo_wfm, max_val, period)
    rise_time_stop90 = do_risetime_calc(rise_time_calculator, 0.90, exo_wfm, max_val, period)
    rise_time_stop95 = do_risetime_calc(rise_time_calculator, 0.95, exo_wfm, max_val, period)
    rise_time_stop99 = do_risetime_calc(rise_time_calculator, 0.99, exo_wfm, max_val, period)

    return (smoothed_max, rise_time_stop10, rise_time_stop20, rise_time_stop30,
            rise_time_stop40, rise_time_stop50, rise_time_stop60, rise_time_stop70,
            rise_time_stop80, rise_time_stop90, rise_time_stop95, rise_time_stop99)


