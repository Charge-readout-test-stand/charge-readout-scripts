#!/usr/bin/env python

"""
"""


import os
import sys

from ROOT import gROOT
# run in batch mode:
gROOT.SetBatch(True)
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

from array import array

import struck_analysis_parameters

def get_wfmparams(exo_wfm, wfm_length, sampling_freq_Hz, n_baseline_samples, calibration, decay_time, is_pmtchannel):
    exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
    energy_wfm = EXODoubleWaveform(exo_wfm)

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

    return (baseline_mean, baseline_rms,
            energy, energy_rms, energy1, energy_rms1, energy_pz, energy_rms_pz, energy1_pz, energy_rms1_pz,
            calibrated_wfm)




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

    # rise time calculator thresholds are called precentage, but they
    # are really fractions...
    rise_time_calculator.SetFinalThresholdPercentage(0.1)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop10 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.2)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop20 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.3)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop30 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.4)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop40 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.5)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop50 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.6)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop60 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.7)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop70 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.8)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
    rise_time_stop80 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.90)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
        #print rise_time_calculator.GetInitialThresholdCrossing()
        #print rise_time_calculator.GetFinalThresholdCrossing()
    rise_time_stop90 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond
    #rise_time[i] = rise_time_calculator.GetRiseTime()/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.95)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
        #print rise_time_calculator.GetInitialThresholdCrossing()
        #print rise_time_calculator.GetFinalThresholdCrossing()
    rise_time_stop95 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    rise_time_calculator.SetFinalThresholdPercentage(0.99)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(exo_wfm, exo_wfm)
        #print rise_time_calculator.GetInitialThresholdCrossing()
        #print rise_time_calculator.GetFinalThresholdCrossing()
    rise_time_stop99 = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

    return (smoothed_max, rise_time_stop10, rise_time_stop20, rise_time_stop30,
            rise_time_stop40, rise_time_stop50, rise_time_stop60, rise_time_stop70,
            rise_time_stop80, rise_time_stop90, rise_time_stop95, rise_time_stop99)
