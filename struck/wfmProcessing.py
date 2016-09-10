#!/usr/bin/env python

"""
Extract parameters (energy, risetime, etc.) from a waveform. 
"""


import os
import sys
import math

from ROOT import gROOT
from ROOT import TFile
from ROOT import TTree
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TH1D
from ROOT import TLine
from ROOT import gSystem
from ROOT import *

# workaround for systems without EXO offline / CLHEP
microsecond = 1.0e3
second = 1.0e9
if os.getenv("EXOLIB") is not None:
    try:
        gSystem.Load("$EXOLIB/lib/libEXOROOT")
        from ROOT import CLHEP
        microsecond = CLHEP.microsecond
        second = CLHEP.second
    except ImportError:
        print "couldn't import CLHEP/ROOT"


from ROOT import EXODoubleWaveform
from ROOT import EXOBaselineRemover
from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother
from ROOT import EXOPoleZeroCorrection
from ROOT import EXOExtremumFinder
from ROOT import EXOTrapezoidalFilter

do_decay_time_fit = True
try:
    from ROOT import EXODecayTimeFit
except ImportError:
    do_decay_time_fit = False
    print "wfmProcessing.py : couldn't import EXODecayTimeFit"

#import struck_analysis_parameters
from struck import struck_analysis_parameters # testing



def do_draw(
    exo_wfm,
    title="", 
    extra_wfm=None, 
    extra_wfm2=None,
    vlines=None, # vertical lines
    ):
    
    if gROOT.IsBatch(): return
    # a canvas for drawing, if debugging:
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    canvas.cd()
    hist = exo_wfm.GimmeHist("hist")
    hist.SetTitle(title)
    hist.SetLineWidth(2)
    hist.SetAxisRange(6.0,19.0) # zoom to interesting times
    if vlines != None:
        #hist.SetAxisRange(vlines[1]-2.0,vlines[-1]+2.0) # zoom to interesting times
        pass
    hist.SetMarkerStyle(8)
    hist.SetMarkerSize(0.7)
    hist.Draw()
    hist_max = hist.GetMaximum()
    hist_min = hist.GetMinimum()
    hist.Draw("p same")
    if extra_wfm:
        hist2 = extra_wfm.GimmeHist("hist2")
        hist2.SetLineColor(kBlue)
        hist2.Draw("l same")
        if hist2.GetMaximum() > hist_max:
            hist_max = hist2.GetMaximum()
        if hist2.GetMinimum() < hist_min:
            hist_min = hist2.GetMinimum()

    if extra_wfm2:
        hist3 = extra_wfm2.GimmeHist("hist3")
        hist3.SetLineColor(kRed)
        hist3.Draw("l same")
        if hist3.GetMaximum() > hist_max:
            hist_max = hist3.GetMaximum()
        if hist3.GetMinimum() < hist_min:
            hist_min = hist3.GetMinimum()
    hist_max = hist_max*1.1
    hist_min = hist_min - hist_max*0.1
    if vlines:
        lines = []
        for vline in vlines:
            line = TLine(vline, hist_min, vline, hist_max)
            line.SetLineStyle(2)
            line.SetLineWidth(2)
            line.Draw()
            lines.append(line)
    hist.SetMaximum(hist_max)
    hist.SetMinimum(hist_min)


    canvas.Update()
    plot_name = "_".join(title.split(" "))
    print plot_name
    val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

    print val
    if (val == 'q' or val == 'Q'): sys.exit(1) 
    if val == 'b': gROOT.SetBatch(True)
    if val == 'p': canvas.Print("%s.pdf" % plot_name)
    


def create_basename(filename, isMC=False):

    # construct a basename to use as output file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    if not isMC:
        # get rid of first underscore stuff:
        basename = "_".join(basename.split("_")[1:])
    return basename


def create_outfile_name(filename, isMC=False):

    basename = create_basename(filename, isMC)
    out_filename = "tier3_%s.root" % basename
    return out_filename


def get_wfmparams(
    exo_wfm, 
    wfm_length, 
    sampling_freq_Hz, 
    n_baseline_samples, 
    calibration, 
    decay_time, 
    is_pmtchannel,
    isMC=False,
    label="",
):
    if False:
        print "exo_wfm:", exo_wfm
        print "wfm_length:", wfm_length
        print "sampling_freq_Hz:", sampling_freq_Hz
        print "n_baseline_samples:", n_baseline_samples
        print "calibration:", calibration
        print "decay_time:", decay_time
        print "is_pmtchannel:", is_pmtchannel

    #Intitially not a signal
    isSignal = 0

    exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)
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
    #do_draw(energy_wfm, "after baseline_remover")

    # measure energy before PZ correction -- use baseline_remover for this
    baseline_remover.SetStartSample(wfm_length - n_baseline_samples - 1)
    baseline_remover.Transform(exo_wfm, energy_wfm)
    energy = baseline_remover.GetBaselineMean()*calibration
    energy_rms = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms = 0.0

    # remove baseline using 2x n_baseline_samples
    baseline_remover.SetBaselineSamples(2*n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)
    baseline_rms = baseline_remover.GetBaselineRMS()
    if math.isnan(baseline_rms): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        baseline_rms = 0.0

    # measure energy before PZ correction, use 2x n_baseline_samples
    baseline_remover.SetStartSample(wfm_length - 2*n_baseline_samples - 1)
    baseline_remover.Transform(exo_wfm, energy_wfm)
    energy1 = baseline_remover.GetBaselineMean()*calibration
    energy_rms1 = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms1): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms1 = 0.0
    
    #measure Decay Time for this WF
    #Only measure if there is a signal which we defice as 10 times above the noise
    #otherwise fill with default negative numbers

    decay_fit = -999.0
    decay_chi2 = -999.0
    decay_error = -999.0
    if do_decay_time_fit and energy_rms1 > 0.0 and energy1/energy_rms1 > 10.0:
        decay_fitter = EXODecayTimeFit()
        decay_fitter.SetStartSample(struck_analysis_parameters.decay_start_time)
        decay_fitter.SetEndSample(struck_analysis_parameters.decay_end_time)
        decay_fitter.SetMaxValGuess(energy1/calibration)
        decay_fitter.SetTauGuess(struck_analysis_parameters.decay_tau_guess)
        decay_fitter.Transform(exo_wfm, exo_wfm)
        decay_fit = decay_fitter.GetDecayTime()
        decay_chi2 = decay_fitter.GetDecayTimeChi2()/baseline_rms**2
        decay_error = decay_fitter.GetDecayTimeError()
    

    # correct for exponential decay
    pole_zero = EXOPoleZeroCorrection()
    pole_zero.SetDecayConstant(decay_time)
    if not is_pmtchannel and energy1>100:
        pole_zero.Transform(exo_wfm, energy_wfm)
        #do_draw(energy_wfm, "%s after PZ correction" % label)

    # measure energy after PZ correction -- use baseline remover
    baseline_remover.SetBaselineSamples(n_baseline_samples) # remove baseline
    baseline_remover.SetStartSample(wfm_length - n_baseline_samples - 1)
    baseline_remover.Transform(energy_wfm)
    energy_pz = baseline_remover.GetBaselineMean()*calibration
    energy_rms_pz = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms_pz): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms_pz = 0.0
 
    # measure energy after PZ correction, use 2x n_baseline_samples
    baseline_remover.SetBaselineSamples(2*n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)

    # correct for exponential decay
    if not is_pmtchannel:
        pole_zero.Transform(exo_wfm, energy_wfm)

    # create calibrated wfm to be added to sum wfm
    calibrated_wfm = EXODoubleWaveform(energy_wfm)
    calibrated_wfm *= calibration

    baseline_remover.SetStartSample(wfm_length - 2*n_baseline_samples - 1)
    baseline_remover.Transform(energy_wfm)
    energy1_pz = baseline_remover.GetBaselineMean()*calibration
    energy_rms1_pz = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms1_pz): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms1_pz = 0.0
    
    #Apply threshold
    if energy1_pz > struck_analysis_parameters.rms_threshold*energy_rms1_pz*math.sqrt(2.0/n_baseline_samples):
        if isMC:
            if energy_rms1_pz <= 0.1 and energy1_pz > 10.0: # for MC with no noise, only consider events above 10 keV
                isSignal = 1
        elif not is_pmtchannel:
            #PMT can't be a signal because by default it has to have triggered
            isSignal = 1

    if is_pmtchannel: # for PMT channel, use GetMaxValue()
        extremum_finder = EXOExtremumFinder()
        extremum_finder.SetFindMaximum(True)
        extremum_finder.Transform(exo_wfm)
        index_of_max = extremum_finder.GetTheExtremumPoint()
        n_points = 9
        avg = 0.0
        n_used_points = 0
        # average a few points around the maximum
        for i in xrange(n_points):
            index = i - n_points/2 + index_of_max

            # handle max at early times:
            if index < 0:
                continue
            n_used_points += 1

            #print "i:", i
            #print "index:", index
            #print "wfm:", exo_wfm[index]
            avg += exo_wfm[index]
        avg /= n_used_points
        energy = exo_wfm.GetMaxValue()*calibration
        energy1 = avg*calibration

        if not gROOT.IsBatch() and False:
            print "is PMT"
            print "index_of_max:", index_of_max
            print "max_val", avg*calibration
            print "energy:", energy
            print "decay_time:", decay_time

        pz_wfm = EXODoubleWaveform(exo_wfm)
        pole_zero.SetDecayConstant(decay_time)
        pole_zero.Transform(exo_wfm, pz_wfm)
        
        trap_wfm = EXODoubleWaveform(exo_wfm)
        trap_filter = EXOTrapezoidalFilter()
        trap_filter.SetFlatTime(2.0*microsecond)
        trap_filter.SetRampTime(4.0*microsecond)
        trap_filter.Transform(pz_wfm, trap_wfm)
        #trap_filter.Transform(exo_wfm, trap_wfm)
        #trap_wfm /= 20.0
        energy_pz = trap_wfm.GetMaxValue()

        trap_filter.SetRampTime(2.0*microsecond)
        trap_filter.Transform(pz_wfm, trap_wfm)
        energy1_pz = trap_wfm.GetMaxValue()

        if False: do_draw(
            #exo_wfm, 
            #pz_wfm,
            trap_wfm,
            "%s after %i-sample baseline_remover" % (
                label,
                baseline_remover.GetBaselineSamples(), ),
            #extra_wfm=trap_wfm,
            extra_wfm=exo_wfm,
            extra_wfm2=pz_wfm,
            vlines=[index_of_max*exo_wfm.GetSamplingPeriod()/microsecond],
        )
        pz_wfm.IsA().Destructor(pz_wfm)
        trap_wfm.IsA().Destructor(trap_wfm)

    energy_wfm.IsA().Destructor(energy_wfm)
    
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
        decay_fit,
        decay_error,
        decay_chi2,
        isSignal
    )

def do_risetime_calc(rise_time_calculator, threshold_percent, wfm, max_val, period):
    rise_time_calculator.SetFinalThresholdPercentage(threshold_percent)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
        rise_time_calculator.Transform(wfm, wfm)
    return rise_time_calculator.GetFinalThresholdCrossing()*period/microsecond




def get_risetimes(
    exo_wfm, 
    wfm_length, 
    sampling_freq_Hz,
    skip_short_risetimes=True, # whether to skip risetimes < 80%
    label="", # a name for plots, used for debugging
):

    exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)
    new_wfm = EXODoubleWaveform(exo_wfm)
    maw_wfm = EXODoubleWaveform(exo_wfm)

    # 20 May 2016 testing alternate smoothing
    if not gROOT.IsBatch():

        n_to_average = 5
        #for i in xrange(exo_wfm.size()):
        for i in xrange(wfm_length):
            #print "exo_wfm[",i,"]=", exo_wfm[i]  #, maw_data
            n_avg = n_to_average if i + n_to_average < wfm_length else wfm_length-i
            stop = int(n_to_average*1.0/2.0)
            start = stop - n_to_average+1
            stop = stop if i + stop < wfm_length else wfm_length-i
            start = start if i+start > 0 else -i
            sum_val = 0.0
            for j in xrange(start,stop+1,1):
                #print "i,j:", i, j, exo_wfm[i+j]
                sum_val += exo_wfm[i+j]
            maw_wfm[i] = sum_val/(stop-start+1)
            #print "maw_wfm[",i,"]=", maw_wfm[i], start, stop  #, maw_data

            #np.convolve(x, np.ones((N,))/N, mode='valid')
            

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
    if skip_short_risetimes:
        rise_time_stop10 = 0.0
    else:
        rise_time_stop10 = do_risetime_calc(rise_time_calculator, 0.10, exo_wfm, max_val, period)

    if skip_short_risetimes:
        rise_time_stop20 = 0.0
    else:
        rise_time_stop20 = do_risetime_calc(rise_time_calculator, 0.20, exo_wfm, max_val, period)

    if skip_short_risetimes:
        rise_time_stop30 = 0.0
    else:
        rise_time_stop30 = do_risetime_calc(rise_time_calculator, 0.30, exo_wfm, max_val, period)

    if skip_short_risetimes:
        rise_time_stop40 = 0.0
    else:
        rise_time_stop40 = do_risetime_calc(rise_time_calculator, 0.40, exo_wfm, max_val, period)

    if skip_short_risetimes:
        rise_time_stop50 = 0.0
    else:
        rise_time_stop50 = do_risetime_calc(rise_time_calculator, 0.50, exo_wfm, max_val, period)

    if skip_short_risetimes:
        rise_time_stop60 = 0.0
    else:
        rise_time_stop60 = do_risetime_calc(rise_time_calculator, 0.60, exo_wfm, max_val, period)

    if skip_short_risetimes:
        rise_time_stop70 = 0.0
    else:
        rise_time_stop70 = do_risetime_calc(rise_time_calculator, 0.70, exo_wfm, max_val, period)

    if skip_short_risetimes:
        rise_time_stop80 = 0.0
    else:
        rise_time_stop80 = do_risetime_calc(rise_time_calculator, 0.80, exo_wfm, max_val, period)

    rise_time_stop90 = do_risetime_calc(rise_time_calculator, 0.90, exo_wfm, max_val, period)
    rise_time_stop95 = do_risetime_calc(rise_time_calculator, 0.95, exo_wfm, max_val, period)
    rise_time_stop99 = do_risetime_calc(rise_time_calculator, 0.99, exo_wfm, max_val, period)


    if not gROOT.IsBatch():
        print "rise times:"
        print "\tmax_val:", max_val
        print "\trise_time_stop10:", rise_time_stop10
        print "\trise_time_stop20:", rise_time_stop20
        print "\trise_time_stop30:", rise_time_stop30
        print "\trise_time_stop40:", rise_time_stop40
        print "\trise_time_stop50:", rise_time_stop50
        print "\trise_time_stop60:", rise_time_stop60
        print "\trise_time_stop70:", rise_time_stop70
        print "\trise_time_stop80:", rise_time_stop80
        print "\trise_time_stop90:", rise_time_stop90
        print "\trise_time_stop95:", rise_time_stop95
        print "\trise_time_stop99:", rise_time_stop99

    if max_val > 100 and not "PMT" in label: do_draw(exo_wfm, "%s after rise-time calc" % label, new_wfm, maw_wfm, vlines=[
        rise_time_stop10,
        rise_time_stop20,
        rise_time_stop30,
        rise_time_stop40,
        rise_time_stop50,
        rise_time_stop60,
        rise_time_stop70,
        rise_time_stop80,
        rise_time_stop90,
        rise_time_stop95,
        rise_time_stop99,
    ])
    
    maw_wfm.IsA().Destructor(maw_wfm)
    new_wfm.IsA().Destructor(new_wfm)

    return [smoothed_max, rise_time_stop10, rise_time_stop20, rise_time_stop30,
            rise_time_stop40, rise_time_stop50, rise_time_stop60, rise_time_stop70,
            rise_time_stop80, rise_time_stop90, rise_time_stop95,
            rise_time_stop99]



