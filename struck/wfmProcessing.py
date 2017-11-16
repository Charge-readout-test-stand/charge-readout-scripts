#!/usr/bin/env python

"""
Extract parameters (energy, risetime, etc.) from a waveform. 
"""


import os
import sys
import math

# somehow these 2 are important?!
from ROOT import TH1D
from ROOT import TLine
from ROOT import *

# workaround for systems without EXO offline / CLHEP
microsecond = 1.0e3
second = 1.0e9

import subprocess
root_version = subprocess.check_output(['root-config --version'], shell=True)
isROOT6 = False
if '6.1.0' in root_version or '6.04/06' in root_version:
    print "Found ROOT 6"
    isROOT6 = True

if os.getenv("EXOLIB") is not None and not isROOT6:
    try:
        gSystem.Load("$EXOLIB/lib/libEXOROOT")
        from ROOT import CLHEP
        microsecond = CLHEP.microsecond
        second = CLHEP.second
        print "imported CLHEP/ROOT"
    except (ImportError, AttributeError) as e:
        print "couldn't import CLHEP/ROOT"

from ROOT import EXODoubleWaveform
from ROOT import EXOBaselineRemover
from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother
from ROOT import EXOPoleZeroCorrection
from ROOT import EXOExtremumFinder
from ROOT import EXOTrapezoidalFilter
from ROOT import EXOMatchedFilter

do_decay_time_fit = True
try:
    from ROOT import EXODecayTimeFit
except ImportError:
    do_decay_time_fit = False
    print "wfmProcessing.py : couldn't import EXODecayTimeFit so not doing it (not an error)"

#from struck import struck_analysis_parameters # testing
import struck_analysis_parameters


def do_draw(
    exo_wfm,
    title="", 
    extra_wfm=None, 
    extra_wfm2=None,
    vlines=None, # vertical lines
    ):
    
    if gROOT.IsBatch(): return
    # a canvas for drawing, if debugging:
    canvas = TCanvas("canvas","do_draw canvas")
    canvas.SetGrid(1,1)
    canvas.cd()
    hist = exo_wfm.GimmeHist("hist")
    hist.SetTitle(title)
    hist.SetLineWidth(2)
    #hist.SetAxisRange(6.0,19.0) # zoom to interesting times
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


def ApplyFilter(exowfm, channel, wfm_length, filter_type="deriv"):

    # Load the derivative template.
    # function is the deriv of gaussian x*exp(-x^2/2*sigma^2)
    # sigma is the width and sets the 
    directory = os.path.dirname(struck_analysis_parameters.__file__)
    tfile = TFile("%s/templateWF_MatchedFilter.root" % directory)
    template = None
    #print tfile.ls()
    if filter_type == "matched":
        template = tfile.Get("CollectionTemplate")
    elif filter_type == "deriv":
        template = tfile.Get("DerivTemplate")
    else:
        print "Not valid type"
        return 0.0, 0.0

    template.SetSamplingFreq(exowfm.GetSamplingFreq())
    NoisePSFile = TFile("%s/AvgNoisePS.root" % directory)
    
    #Bad channels
    if channel == 16 or channel == 27:
        return 0.0, 0.0
 
    avg_noise = NoisePSFile.Get("PSwfm%i" % channel)
    avg_noise.SetSamplingFreq(exowfm.GetSamplingFreq())
    

    matched_result = exowfm.Clone() #create shell for the result
    temp_offset = 0 #no offseet
 
    #print exowfm.GetLength() , template.GetLength(), wfm_length
    #print exowfm.GetSamplingFreq(), template.GetSamplingFreq()

    #Apply the filter which is just a convolution
    match_filter = EXOMatchedFilter()
    match_filter.SetNoisePowerSqrMag(avg_noise)
    match_filter.SetTemplateToMatch(template, int(wfm_length), temp_offset)
    match_filter.Transform(matched_result)
    
    baseline_remover = EXOBaselineRemover()
    baseline_remover.SetBaselineSamples(150)
    baseline_remover.SetStartSample(50)
    baseline_remover.Transform(matched_result)
    baseline_rms = baseline_remover.GetBaselineRMS()

    #Need max/min, sigma, sign
    #print "Max", matched_result.GetMaxValue()/baseline_rms, matched_result.GetMaxTime()
    #print "Min", matched_result.GetMinValue()/baseline_rms, matched_result.GetMinTime()
    
    #The WF is padded on the sides so it gets negative sometimes
    #only care about the center
    matched_result_trim = matched_result.SubWaveform(50,750)
    ratio_max = matched_result_trim.GetMaxValue()/baseline_rms
    time_max  = matched_result_trim.GetMaxTime()
    if abs(matched_result_trim.GetMinValue()) > matched_result_trim.GetMaxValue():
        ratio_max = matched_result_trim.GetMinValue()/baseline_rms
        time_max =  matched_result_trim.GetMinTime()

    #if not gROOT.IsBatch():
    if False:
    #if True and filter_type=="deriv" and abs(ratio_max) > 10.0:
        #Gets negative on hits since the edges are negtive
        gROOT.SetBatch(False)
        print ratio_max, matched_result_trim.GetMinValue()/baseline_rms, matched_result_trim.GetMaxValue()/baseline_rms 
        c2 = TCanvas("can","can")
        exowfm.GimmeHist().Draw("L")
        c2.Update()
        raw_input()

        matched_result_trim.SubWaveform(50,750).GimmeHist().Draw("L")
        c2.Update()
        raw_input()
        gROOT.SetBatch(True)
    
    tfile.Close()
    NoisePSFile.Close()

    matched_result.IsA().Destructor(matched_result)

    return ratio_max, time_max
    


def get_wfmparams(
    exo_wfm, 
    wfm_length, 
    sampling_freq_Hz, 
    n_baseline_samples, 
    calibration, 
    decay_time, 
    is_pmtchannel,
    is_sipmchannel,
    channel,
    isMC=False,
    label="",
):
    if False:
        gROOT.SetBatch(False)
        print "exo_wfm:", exo_wfm
        print "wfm_length:", wfm_length
        print "sampling_freq_Hz:", sampling_freq_Hz
        print "n_baseline_samples:", n_baseline_samples
        print "calibration:", calibration
        print "decay_time:", decay_time
        print "is_pmtchannel:", is_pmtchannel
        print "is_sipmchannel", is_sipmchannel
        print "channel #:", channel
        #raw_input("Pause")

    #Intitially not a signal
    isSignal = 0

    #Setup WF and copy into energy_wfm for Transformations
    exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)
    energy_wfm = EXODoubleWaveform(exo_wfm)
    
    # Get Sample and Time for when to start doing Energy Calculation
    energy_start_time_microseconds = struck_analysis_parameters.energy_start_time_microseconds
    energy_start_sample = int(energy_start_time_microseconds*microsecond*sampling_freq_Hz/second)

    # calculate wfm max and min:
    wfm_max = exo_wfm.GetMaxValue()
    wfm_min = exo_wfm.GetMinValue()

    # remove the baseline using 1/2 the standard # of baseline samples
    baseline_remover = EXOBaselineRemover()
    baseline_remover.SetBaselineSamples(n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)
    baseline_mean = baseline_remover.GetBaselineMean()
    #do_draw(energy_wfm, "channel %i %s after %i-sample baseline_remover" % (channel, label, n_baseline_samples))

    # measure energy before PZ correction -- use baseline_remover for this
    # saves to the enrgy_wfm when transform is performed
    baseline_remover.SetStartSample(energy_start_sample)
    baseline_remover.Transform(exo_wfm, energy_wfm)
    energy = baseline_remover.GetBaselineMean()*calibration
    energy_rms = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms = 0.0

    # remove baseline using 2x n_baseline_samples
    # this is because n_baseline_samples is 1/2 the pretrigger delay
    baseline_remover.SetBaselineSamples(2*n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)
    baseline_rms = baseline_remover.GetBaselineRMS()
    if math.isnan(baseline_rms): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        baseline_rms = 0.0
    
    # measure energy1 before PZ correction, use 2x n_baseline_samples for baseline 
    # energy starts same place
    baseline_remover.SetStartSample(energy_start_sample)
    baseline_remover.Transform(exo_wfm, energy_wfm)
    energy1 = baseline_remover.GetBaselineMean()*calibration
    energy_rms1 = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms1): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms1 = 0.0
    
    #measure Decay Time for this WF
    #Only measure if there is a signal which we define as 10 times above the noise
    #otherwise fill with default negative numbers
    decay_fit = -999.0
    decay_chi2 = -999.0
    decay_error = -999.0
    if do_decay_time_fit and not isMC and energy_rms1 > 0.0 and energy1/energy_rms1 > 10.0:
        decay_fitter = EXODecayTimeFit()
        # start and end sample need to be size_t; after sampling freq is set exo_wfm.GimmeHist() x-axis ranges from 0 to max time, in microseconds
        decay_fitter.SetStartSample(int(struck_analysis_parameters.decay_start_time_microseconds))
        decay_fitter.SetEndSample(int(struck_analysis_parameters.decay_end_time_microseconds))
        # estimate the exp parameters; compensate for the decay that has already happened
        max_val_guess = energy1/calibration
        max_val_guess *= 2.0-math.exp(-struck_analysis_parameters.decay_start_time_microseconds/struck_analysis_parameters.decay_tau_guess)
        decay_fitter.SetMaxValGuess(max_val_guess)
        decay_fitter.SetTauGuess(struck_analysis_parameters.decay_tau_guess)
        decay_fitter.Transform(exo_wfm, exo_wfm)
        decay_fit = decay_fitter.GetDecayTime()
        # decay_chi2 is the reduced chi^2. Divide by baseline_rms^2, since this
        # is the error on the wfm, except if baseline_rms is zero, which
        # happens sometimes but rarely. 
        try:
            decay_chi2 = decay_fitter.GetDecayTimeChi2()/baseline_rms**2
        except ZeroDivisionError:
            decay_chi2 = decay_fitter.GetDecayTimeChi2()
        decay_error = decay_fitter.GetDecayTimeError()

        if not gROOT.IsBatch() and False:

            # reproduce what happens in EXODecayTimeFit and draw result, for debugging:
            print "decay_fit:", decay_fit
            print "decay_start_time_microseconds:", struck_analysis_parameters.decay_start_time_microseconds
            print "decay_end_time_microseconds:", struck_analysis_parameters.decay_end_time_microseconds

            canvas = TCanvas("decay_canvas","decay_canvas")
            canvas.SetGrid()
            hist = exo_wfm.GimmeHist()
            exp_decay = TF1("exp_decay_test","[0]*exp(-x/[1])", 
                    struck_analysis_parameters.decay_start_time_microseconds, 
                    struck_analysis_parameters.decay_end_time_microseconds)
            exp_decay.SetParameters(
                    max_val_guess,
                    struck_analysis_parameters.decay_tau_guess)
            print "[0]:", exp_decay.GetParameter(0)
            print "[1]:", exp_decay.GetParameter(1)
            if False: # draw before fit:
                exp_decay.SetLineColor(kRed)
                hist.Draw("l")
                exp_decay.Draw("l same")
                canvas.Update()
                raw_input("before fit -- press enter")
            fit_result = hist.Fit(exp_decay, "WBRS")
            print "energy1/calibration:", energy1/calibration
            print "[0]:", exp_decay.GetParameter(0)
            print "[1]:", exp_decay.GetParameter(1)
            print "chi2:", exp_decay.GetChisquare()
            print "ndf:", exp_decay.GetNDF()
            print "chi2/ndf:", exp_decay.GetChisquare()/exp_decay.GetNDF()
            hist.Draw("l")
            exp_decay.SetLineColor(kBlue)
            exp_decay.Draw("l same")
            canvas.Update()
            val = raw_input("press enter (or q to quit) ")
            if val == 'q': sys.exit()


    # correct for exponential decay
    # save the transformed WF into the energy_wfm
    pole_zero = EXOPoleZeroCorrection()
    pole_zero.SetDecayConstant(decay_time)
    if not is_pmtchannel or not is_simpchannel: #Skip correction for Light Channels
        pole_zero.Transform(exo_wfm, energy_wfm)

    # measure energy after PZ correction -- use baseline remover
    baseline_remover.SetBaselineSamples(n_baseline_samples) # remove baseline
    baseline_remover.SetStartSample(energy_start_sample)
    baseline_remover.Transform(energy_wfm)
    energy_pz = baseline_remover.GetBaselineMean()*calibration
    energy_rms_pz = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms_pz): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms_pz = 0.0
 

    # measure energy after PZ correction, first remove baseline with 2x n_baseline_samples
    baseline_remover.SetBaselineSamples(2*n_baseline_samples)
    baseline_remover.SetStartSample(0)
    baseline_remover.Transform(exo_wfm)

#----------------------------------------------------------------------------------------------------
#-----------------------------------------------Do We Need?------------------------------------------
#----------------------------------------------------------------------------------------------------
    baseline_slope = 0.0
    if False: # skip baseline_slope for now
        last_time = n_baseline_samples*2.0/sampling_freq_Hz*1e6
        fcn = TF1("fcn","pol1(0)",0.0, wfm_length/sampling_freq_Hz*1e6)
        fcn.SetParameter(0,0.0) # offset
        fcn.SetParameter(1,0.0) # slope
        hist = exo_wfm.GimmeHist()
        #print "last time:", last_time
        fit_options = "WWBQCN"
        if not gROOT.IsBatch(): 
            fit_options = "WWBVC"
            fcn.SetLineColor(kRed)
        # Fit options:
        # "WW" Set all weights to 1 including empty bins; ignore error bars
        # "N"  Do not store the graphics function, do not draw
        # "B"  User defined parameter settings are used for predefined functions like "gaus", "expo", "poln", "landau".
        # "C"  In case of linear fitting, don't calculate the chisquare (saves time)
        #"Q"  Quiet mode (minimum printing)
        # "V"  Verbose mode (default is between Q and V)
        hist.Fit(fcn, fit_options, "", 0.0, last_time) 
        baseline_slope = fcn.GetParameter(1)

        # draw baseline fit result:
        if not gROOT.IsBatch() and energy1 > 200:
            print "last time:", last_time
            print "%i baseline samples" %  n_baseline_samples
            print "%.1f energy_start_sample" %  energy_start_sample
            print "baseline_slope slope: keV/microseconds", baseline_slope*calibration
            print "p0 keV", (fcn.GetParameter(0) + baseline_slope*last_time/2.0)*calibration
            can = TCanvas("testcanvas","test canvas")
            can.SetGrid()
            hist.Draw()
            can.Update()
            raw_input("press enter ")
        hist.IsA().Destructor(hist)
        # end of baseline_slope calc
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

    # correct for exponential decay
    if not is_pmtchannel or not is_sipmchannel:
        pole_zero.Transform(exo_wfm, energy_wfm)
        if False and energy1 > 200:
            print "decay_time:", decay_time
            do_draw(energy_wfm, "%s after PZ" % label, exo_wfm)

    # create calibrated wfm to be added to sum wfm
    calibrated_wfm = EXODoubleWaveform(energy_wfm)
    calibrated_wfm *= calibration

    # Get the energy using same number of energy averages but 2x the number of baseline
    # averages 
    baseline_remover.SetStartSample(energy_start_sample)
    baseline_remover.Transform(energy_wfm)
    energy1_pz = baseline_remover.GetBaselineMean()*calibration
    energy_rms1_pz = baseline_remover.GetBaselineRMS()*calibration
    if math.isnan(energy_rms1_pz): # for events with 0 noise, RMS is sometimes NaN
        if not isMC: print "WARNING: setting RMS from nan to 0"
        energy_rms1_pz = 0.0

#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
    energy1_pz_slope = 0.0
    if False: # skip energy1_pz_slope for now
        # fit to PZ-corrected slope:
        last_time = energy_start_time_microseconds + n_baseline_samples*2.0/sampling_freq_Hz*1e6
        fcn.SetParameter(0,0.0) # offset
        fcn.SetParameter(1,0.0) # slope
        hist = energy_wfm.GimmeHist()
        hist.Fit(fcn, fit_options, "", energy_start_time_microseconds, last_time)
        energy1_pz_slope = fcn.GetParameter(1)*calibration

        if gROOT.IsBatch() and energy1 > 200:
            print "last time:", last_time
            print "energy_start_time_microseconds:", energy_start_time_microseconds
            print "energy_start_sample:", energy_start_sample
            print "%i baseline samples" %  n_baseline_samples
            print "%.1f energy_start_sample" %  energy_start_sample
            print "energy1_pz_slope slope: keV/microseconds", energy1_pz_slope*calibration
            #print "p0", fcn.GetParameter(0) + energy1_pz_slope*(energy_start_time_microseconds+n_baseline_samples*2.0/sampling_freq_Hz*1e6/2.0)
            print "p0 keV", fcn.GetParameter(0)*calibration + energy1_pz_slope*last_time/2.0
            can = TCanvas("testcanvas","test canvas")
            can.SetGrid()
            hist.Draw()
            can.Update()
            #raw_input("press enter ")
            do_draw(energy_wfm, "%s after energy meas: energy1=%i keV, energy1_pz=%i keV" % (label, energy1, energy1_pz))
        hist.IsA().Destructor(hist)
        fcn.IsA().Destructor(fcn)
        # end of energy1_pz_slope calc
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
    
    #Apply threshold -- we really use 2*n_baseline_samples, so 2.0/2.0 cancels
    if energy1_pz > struck_analysis_parameters.rms_threshold*energy_rms1_pz*math.sqrt(1.0/n_baseline_samples):
        #SiPM check too
        if not is_pmtchannel and not is_sipmchannel:
            #PMT can't be a signal because by default it has to have triggered
            isSignal = 1
    
    #Apply Matched Filter currently in testing
    #if not is_pmtchannel:
    if False:
        dfilter_max, dfilter_time = ApplyFilter(energy_wfm, channel, wfm_length, filter_type="deriv")
        mfilter_max, mfilter_time = ApplyFilter(energy_wfm, channel, wfm_length, filter_type="matched")
    else:
        dfilter_max  =  0.0 
        dfilter_time = 0.0
        mfilter_max  =  0.0
        mfilter_time = 0.0

    if is_pmtchannel or is_sipmchannel: # for PMT channel, use GetMaxValue()
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
        energy = exo_wfm.GetMaxValue()*calibration # used for lightEnergy
        energy1 = avg*calibration # average using n_points

        if not gROOT.IsBatch() and False:
            print "is PMT"
            print "index_of_max:", index_of_max
            print "max_val", avg*calibration
            print "energy:", energy 
            print "decay_time:", decay_time

        pz_wfm = EXODoubleWaveform(exo_wfm)
        pole_zero.SetDecayConstant(decay_time)
        pole_zero.Transform(exo_wfm, pz_wfm)
        
        # is this for when we used the Ortec preamp?
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

        if energy1_pz > 100 and False: do_draw(
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

        # end is_pmtchannel check

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
        isSignal,
        dfilter_max,
        dfilter_time,
        mfilter_max,
        mfilter_time,
        baseline_slope,
        energy1_pz_slope,
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

    if max_val > 100 and not "PMT" in label and False: do_draw(exo_wfm, "%s after rise-time calc" % label, new_wfm, maw_wfm, vlines=[
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



