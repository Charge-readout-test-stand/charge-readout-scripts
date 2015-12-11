#!/usr/bin/env python

"""
Do some waveform processing to extract energies, etc. 

EXO class index, with waveform transformers: 
http://exo-data.slac.stanford.edu/exodoc/ClassIndex.html

to do:
  * ID wfms with multiple PMT signals?
  * ID noise bursts?
  * add timestamp info for each wfm?
  * fix decay time and calibration to work for tier 1 files
  * FIXME -- ID of amplified/unamplified and 5V/2V input doesn't work on pulser files...

available CLHEP units are in 
http://java.freehep.org/svn/repos/exo/show/offline/trunk/utilities/misc/EXOUtilities/SystemOfUnits.hh?revision=HEAD

--------------------------------------------------------------------
Notes from 5th LXe:
Use on tier 1 or tier2 files:
    *NotShaped_Amplified*DT*.root

Submit batch jobs:
python /afs/slac.stanford.edu/u/xo/alexis4/alexis-exo/testScripts/submitPythonJobsSLAC.py generateTier3Files.py ../tier2/tier2_LXe_Run1_1700VC*NotShaped_Amplified*DT*.root

Can combine files later:
hadd -O good_tier3.root tier3_LXe_Run1_1700VC*.root
hadd -O all_tier3.root tier3*.root

01 Nov 2015: 
    1225546 tier3 entries in *NotShaped_Amplified_*DT*.root
    1225546 tier2 entries in *NotShaped_Amplified_*DT*.root
    7392227/6 = 1.478445e+06 tier0 *NotShaped_Amplified_*DT*.dat entries
"""


import os
import sys
import time
from optparse import OptionParser


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
#from ROOT import EXOTrapezoidalFilter
from ROOT import EXOBaselineRemover
from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother
from ROOT import EXOPoleZeroCorrection
from ROOT import TObjString

from array import array

# definition of calibration constants, decay times, channels
import struck_analysis_parameters

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


def process_file(filename, verbose=True, do_overwrite=True):

    #---------------------------------------------------------------
    # options
    #---------------------------------------------------------------

    #print "verbose:", verbose
    #print "do_overwrite:", do_overwrite
    #return # debugging

    # whether to run in debug mode (draw wfms):
    do_debug = not gROOT.IsBatch()
    do_draw_extra = not gROOT.IsBatch()

    reporting_period = 1000

    # samples at wfm start and end to use for energy calc:
    n_baseline_samples_to_use = 50

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz

    channels = struck_analysis_parameters.channels
    n_chargechannels = struck_analysis_parameters.n_chargechannels
    pmt_channel = struck_analysis_parameters.pmt_channel
    n_channels = struck_analysis_parameters.n_channels

    # this is the number of channels per event (1 if we are processing tier1
    # data, len(channels) if we are processing tier2 data
    n_channels_in_event = n_channels

    #---------------------------------------------------------------

    print "processing file: ", filename

    basename = create_basename(filename)

    canvas = TCanvas()
    canvas.SetGrid(1,1)

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    try:
        n_entries = tree.GetEntries()
    except AttributeError:
        print "==> problem accessing tree -- skipping this file"
        return 0

    # decide if this is a tier1 or tier2 file
    is_tier1 = False
    try:
        tree.GetEntry(0)
        tree.wfm0
        print "this is a tier2 file"
    except AttributeError:
        print "this is a tier1 file"
        n_channels_in_event = 1
        is_tier1 = True

    # open output file and tree
    out_filename = create_outfile_name(filename)
    if not do_overwrite:
        if os.path.isfile(out_filename):
            print "file exists!"
            return 0
    out_file = TFile(out_filename, "recreate")
    out_tree = TTree("tree", "%s processed wfm tree" % basename)
    out_tree.SetLineColor(TColor.kBlue)
    out_tree.SetLineWidth(2)
    out_tree.SetMarkerColor(TColor.kRed)
    out_tree.SetMarkerStyle(8)
    out_tree.SetMarkerSize(0.5)
    run_tree = TTree("run_tree", "run-level data")

    
    # set up some energy spectra hists here:
    # tried drawing the output tree to these, but kept getting weird errors, so
    # filling with TTree:Fill() instead
    energy_hists = {}
    for channel in channels:
        
        n_bins = 2000
        bin_width = 8 # keV

        hist = TH1D(
            "hist%i" % channel, 
            "energy spectrum for channel %i" % channel,
            n_bins,
            0,
            n_bins*bin_width
        )
        energy_hists[channel] = hist
        #hist.SetDirectory(0)
        hist.SetXTitle("Energy [keV]")
        hist.SetYTitle("Counts / %i keV / second" % bin_width)
        hist.SetLineWidth(2)
        hist.SetLineColor(TColor.kBlue)

    # Writing trees in pyroot is clunky... need to use python arrays to provide
    # branch addresses, see:
    # http://wlav.web.cern.ch/wlav/pyroot/tpytree.html

    is_2Vinput = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('is_2Vinput', is_2Vinput, 'is_2Vinput[%i]/i' % n_channels)

    is_amplified = array('I', [1]*n_channels) # unsigned int
    out_tree.Branch('is_amplified', is_amplified, 'is_amplified[%i]/i' % n_channels)

    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    time_stamp = array('L', [0]) # unsigned long
    out_tree.Branch('time_stamp', time_stamp, 'time_stamp/l')

    sampling_frequency_Hz = array('d', [0]) # double
    out_tree.Branch('sampling_freq_Hz', sampling_frequency_Hz, 'sampling_freq_Hz/D')
    sampling_frequency_Hz[0] = sampling_freq_Hz

    time_stampDouble = array('d', [0]) # double
    out_tree.Branch('time_stampDouble', time_stampDouble, 'time_stampDouble/D')

    time_since_last = array('d', [0]) # double
    out_tree.Branch('time_since_last', time_since_last, 'time_since_last/D')

    n_entries_array = array('I', [0]) # unsigned int
    out_tree.Branch('n_entries', n_entries_array, 'n_entries/i')
    run_tree.Branch('n_entries', n_entries_array, 'n_entries/i')
    n_entries_array[0] = n_entries

    # estimate run time by subtracting last time stamp from first time stamp
    run_time = array('d', [0]) # double
    out_tree.Branch('run_time', run_time, 'run_time/D')
    run_tree.Branch('run_time', run_time, 'run_time/D')
    if is_tier1:
        run_time[0] = (tree.GetMaximum("timestampDouble") -
            tree.GetMinimum("timestampDouble"))/sampling_freq_Hz
    else:
        run_time[0] = (tree.GetMaximum("time_stampDouble") -
            tree.GetMinimum("time_stampDouble"))/sampling_freq_Hz
    print "run time: %.2f seconds" % run_time[0]

    channel = array('I', [0]*n_channels_in_event) # unsigned int
    out_tree.Branch('channel', channel, 'channel[%i]/i' % n_channels_in_event)

    trigger_time = array('d', [0.0]) # double
    out_tree.Branch('trigger_time', trigger_time, 'trigger_time/D')
    run_tree.Branch('trigger_time', trigger_time, 'trigger_time/D')

    # estimate trigger time, in microseconds
    trigger_hist = TH1D("trigger_hist","",5000,0,5000)
    selection = "channel==%i && wfm_max - wfm%i[0] > 20" % (pmt_channel, pmt_channel)
    if is_tier1:
        selection = "channel==%i && wfm_max - wfm[0] > 20" % pmt_channel
        
    n_trigger_entries = tree.Draw(
        "wfm_max_time >> trigger_hist",
        selection,
        "goff"
    )
    if n_trigger_entries > 0:
        trigger_time[0] = (trigger_hist.GetMaximumBin() - 22)/sampling_freq_Hz*1e6
        print "trigger time is approximately %.3f microseconds" % trigger_time[0]
    else:
        print "--> Not enough PMT entries to determine trigger time"

    if trigger_time[0] < 10:
        "--> forcing trigger time to 200 samples = 8 microseconds (ok for 5th LXe)"
        trigger_time[0] = 200/sampling_freq_Hz*1e6

    # store some processing parameters:
    n_baseline_samples = array('I', [0]) # double
    out_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')
    n_baseline_samples[0] = n_baseline_samples_to_use

    decay_time = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('decay_time', decay_time, 'decay_time[%i]/D' % n_channels_in_event)

    decay_time_values = struck_analysis_parameters.decay_time_values
    decay_time_values[pmt_channel] = 1e9*CLHEP.microsecond

    # energy calibration, keV:
    calibration = array('d', [0.0]*n_channels_in_event) # double
    out_tree.Branch('calibration', calibration, 'calibration[%i]/D' % n_channels_in_event)

    rise_time_stop10 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop10', rise_time_stop10, 'rise_time_stop10[%i]/D' % n_channels_in_event)

    rise_time_stop20 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop20', rise_time_stop20, 'rise_time_stop20[%i]/D' % n_channels_in_event)

    rise_time_stop30 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop30', rise_time_stop30, 'rise_time_stop30[%i]/D' % n_channels_in_event)

    rise_time_stop40 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop40', rise_time_stop40, 'rise_time_stop40[%i]/D' % n_channels_in_event)

    rise_time_stop50 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop50', rise_time_stop50, 'rise_time_stop50[%i]/D' % n_channels_in_event)

    rise_time_stop60 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop60', rise_time_stop60, 'rise_time_stop60[%i]/D' % n_channels_in_event)

    rise_time_stop70 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop70', rise_time_stop70, 'rise_time_stop70[%i]/D' % n_channels_in_event)

    rise_time_stop80 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop80', rise_time_stop80, 'rise_time_stop80[%i]/D' % n_channels_in_event)

    rise_time_stop90 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop90', rise_time_stop90, 'rise_time_stop90[%i]/D' % n_channels_in_event)

    rise_time_stop95 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop95', rise_time_stop95, 'rise_time_stop95[%i]/D' % n_channels_in_event)

    rise_time_stop99 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('rise_time_stop99', rise_time_stop99, 'rise_time_stop99[%i]/D' % n_channels_in_event)

    smoothed_max = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('smoothed_max', smoothed_max, 'smoothed_max[%i]/D' % n_channels_in_event)

    wfm_length = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('wfm_length', wfm_length, 'wfm_length[%i]/i' % n_channels)

    wfm_max = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('wfm_max', wfm_max, 'wfm_max[%i]/D' % n_channels_in_event)

    wfm_max_time = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('wfm_max_time', wfm_max_time, 'wfm_max_time[%i]/D' % n_channels_in_event)

    wfm_min = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('wfm_min', wfm_min, 'wfm_min[%i]/D' % n_channels_in_event)

    baseline_mean = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('baseline_mean', baseline_mean, 'baseline_mean[%i]/D' % n_channels_in_event)

    baseline_rms = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('baseline_rms', baseline_rms, 'baseline_rms[%i]/D' % n_channels_in_event)

    # some file-averaged parameters
    baseline_mean_file = array('d', [0]*n_channels) # double
    out_tree.Branch('baseline_mean_file', baseline_mean_file, 'baseline_mean_file[%i]/D' % n_channels)
    run_tree.Branch('baseline_mean_file', baseline_mean_file, 'baseline_mean_file[%i]/D' % n_channels)

    baseline_rms_file = array('d', [0]*n_channels) # double
    out_tree.Branch('baseline_rms_file', baseline_rms_file, 'baseline_rms_file[%i]/D' % n_channels)
    run_tree.Branch('baseline_rms_file', baseline_rms_file, 'baseline_rms_file[%i]/D' % n_channels)

    # make a hist for calculating some averages
    hist = TH1D("hist","",100, 0, pow(2,14))
    print "calculating mean baseline & baseline RMS for each channel in this file..."
    for (i, i_channel) in enumerate(channels):
        print "%i: ch %i" % (i, i_channel)
        selection = "Iteration$<%i && channel==%i" % (n_baseline_samples[0], i_channel)

        if do_debug: continue
            
        # calculate avg baseline:
        draw_command = "wfm >> hist"
        if not is_tier1:
            draw_command = "wfm%i >> hist" % i_channel
        tree.Draw(
            draw_command,
            selection,
            "goff"
        )
        baseline_mean_file[i] = hist.GetMean()
        print "\t draw command: %s | selection %s" % (draw_command, selection)
        print "\t file baseline mean:", baseline_mean_file[i]

        # calculate baseline RMS:
        draw_command = "wfm-wfm[0] >> hist"
        if not is_tier1:
            draw_command = "wfm%i-wfm%i[0] >> hist" % (i_channel, i_channel)
        tree.Draw(
            draw_command,
            selection,
            "goff"
        )
        baseline_rms_file[i] = hist.GetRMS()
        print "\t draw command: %s | selection %s" % (draw_command, selection)
        print "\t file baseline rms:", baseline_rms_file[i]

    print "\t done"

    # decide whether 2V input was used for the digitizer or not. The
    # file-averaged baseline mean for channel 0 seems like a good indicator of
    # this -- we should also figure out if any channels are shaped...

    calibration_values = struck_analysis_parameters.calibration_values

    print "choosing calibration values..."
    for (i, i_channel) in enumerate(channels):
        print "channel %i" % i_channel

        try:
            print "\t original calibration value %.4e" % calibration_values[i_channel]
        except KeyError:
            print "\t no calibration data for ch %i" % i_channel
            continue

        is_2Vinput[i] = struck_analysis_parameters.is_2Vinput(baseline_mean_file[i])
        if is_2Vinput[i]:
            print "\t channel %i used 2V input range" % i_channel
            print "\t dividing calibration by 2.5"
            calibration_values[i_channel] /= 2.5

        # this doesn't seem very reliable
        #is_amplified[i] = struck_analysis_parameters.is_amplified(
        #    baseline_mean_file[i], baseline_rms_file[i])


        if is_amplified[i] == 0:
            if i_channel != pmt_channel:
                calibration_values[i_channel] *= 4.0
                print "\t multiplying calibration by 4"
                print "\t channel %i is unamplified" % i_channel
        print "\t channel %i calibration: %.4e" % (i_channel, calibration_values[i_channel])

    # PMT threshold
    pmt_threshold = array('d', [0]) # double
    out_tree.Branch('pmt_threshold', pmt_threshold, 'pmt_threshold/D')
    run_tree.Branch('pmt_threshold', pmt_threshold, 'pmt_threshold/D')

    # calculate PMT threshold...
    draw_command = "wfm_max-wfm[0] >> hist"
    if not is_tier1:
        draw_command = "wfm_max-wfm%i[0] >> hist" % pmt_channel

    tree.Draw(draw_command,"channel==%i" % pmt_channel,"goff")
    pmt_threshold[0] = hist.GetBinLowEdge(hist.FindFirstBinAbove(0))*calibration_values[pmt_channel]
    print "pmt_threshold:", pmt_threshold[0]

    # energy & rms before any processing
    energy = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy', energy, 'energy[%i]/D' % n_channels_in_event)
    energy_rms = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy_rms', energy_rms, 'energy_rms[%i]/D' % n_channels_in_event)

    chargeEnergy = array('d', [0.0]) # double
    out_tree.Branch('chargeEnergy', chargeEnergy, 'chargeEnergy/D')

    lightEnergy = array('d', [0.0]) # double
    out_tree.Branch('lightEnergy', lightEnergy, 'lightEnergy/D')

    # energy & rms before processing, using 2x sample length
    energy1 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy1', energy1, 'energy1[%i]/D' % n_channels_in_event)
    energy_rms1 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy_rms1', energy_rms1, 'energy_rms1[%i]/D' % n_channels_in_event)

    # energy & rms after PZ
    energy_pz = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy_pz', energy_pz, 'energy_pz[%i]/D' % n_channels_in_event)
    energy_rms_pz = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy_rms_pz', energy_rms_pz, 'energy_rms_pz[%i]/D' % n_channels_in_event)

    # energy & rms after PZ, using 2x sample length
    energy1_pz = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy1_pz', energy1_pz, 'energy1_pz[%i]/D' % n_channels_in_event)
    energy_rms1_pz = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy_rms1_pz', energy_rms1_pz, 'energy_rms1_pz[%i]/D' % n_channels_in_event)
    
    # save slope of linear fit after PZ correction:
    pz_p1 = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('pz_p1', pz_p1, 'pz_p1[%i]/D' % n_channels_in_event)
    pz_p1_err = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('pz_p1_err', pz_p1_err, 'pz_p1_err[%i]/D' % n_channels_in_event)

    fname = TObjString(os.path.abspath(filename))
    out_tree.Branch("filename",fname)
    run_tree.Branch("filename",fname)

    start_time = time.clock()
    last_time = start_time
    prev_time_stamp = 0.0

    if do_debug:
        reporting_period = 1

    print "%i entries" % n_entries


    run_tree.Fill() # this tree only has one entry with run-level entries

    # loop over all entries in tree
    for i_entry in xrange(n_entries):
        tree.GetEntry(i_entry)


        #if i_entry > 1000: break # debugging

        # print periodic output message
        if i_entry % reporting_period == 0:
            now = time.clock()
            print "----> entry %i of %i (%.2f percent in %.1f seconds, %.1f seconds total)" % (
                i_entry, n_entries, 100.0*i_entry/n_entries, now - last_time, now -
                start_time)
            last_time = now


        # set event-level output tree variables
        event[0] = tree.event

        if is_tier1:
            time_stamp[0] = tree.timestamp
            time_stampDouble[0] = tree.timestampDouble
            
        else:
            time_stamp[0] = tree.time_stamp
            time_stampDouble[0] = tree.time_stampDouble

        # calculate time since previous event
        if prev_time_stamp > 0:
            time_since_last[0] = time_stampDouble[0] - prev_time_stamp
        else:
            time_since_last[0] = -1.0
        prev_time_stamp = time_stampDouble[0]

        # initialize these two to zero
        chargeEnergy[0] = 0.0
        lightEnergy[0] = 0.0

        for i in xrange(n_channels_in_event):

            if is_tier1:
                wfm = tree.wfm
                channel[i] = tree.channel
                wfm_max_time[i] = tree.wfm_max_time

            else:
                channel[i] = tree.channel[i]
                if i == 0: 
                    wfm = tree.wfm0
                elif i == 1: 
                    wfm = tree.wfm1
                elif i == 2: 
                    wfm = tree.wfm2
                elif i == 3: 
                    wfm = tree.wfm3
                elif i == 4: 
                    wfm = tree.wfm4
                elif i == 5: 
                    wfm = tree.wfm5
                elif i == 6:
                    wfm = tree.wfm8
                wfm_max_time[i] = tree.wfm_max_time[i]

            wfm_length[i] = len(wfm)


            exo_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[i])
            wfm_max[i] = exo_wfm.GetMaxValue()
            wfm_min[i] = exo_wfm.GetMinValue()

            new_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[i])
            energy_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[i])

            exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
            #print exo_wfm.GetSamplingFreq()
            period =  exo_wfm.GetSamplingPeriod()
            
            # remove the baseline
            baseline_remover = EXOBaselineRemover()
            baseline_remover.SetBaselineSamples(n_baseline_samples[0])
            baseline_remover.Transform(exo_wfm)
            baseline_mean[i] = baseline_remover.GetBaselineMean()
            baseline_rms[i] = baseline_remover.GetBaselineRMS()

            if do_debug:
                print "channel %i" % channel[i]
                print wfm_length[i]
                #if exo_wfm.GetMaxValue() < 50: continue # skip low energy wfms
                #if i == 5: continue # skip PMT

            try:
                calibration[i] = calibration_values[channel[i]]
            except KeyError:
                #print channel[i]
                calibration[i] = 1.0
                
            # build sum waveform from calibrated waveforms
            # FIXME -- need to finish sum_wfm work and extract parameters from
            # the sum wfm
            if channel[i] != pmt_channel:
                if do_debug:
                    print "adding wfm from ch %i" % channel[i]
                temp_wfm = EXODoubleWaveform(exo_wfm)
                temp_wfm *= calibration[i]
                if i == 0:
                    exo_sum_wfm = temp_wfm
                    sum_energy = 0
                else:
                    exo_sum_wfm += temp_wfm

            # measure energy before PZ correction
            baseline_remover.SetStartSample(wfm_length[i] - n_baseline_samples[0] - 1)
            baseline_remover.Transform(exo_wfm, energy_wfm)

            energy[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms[i] = baseline_remover.GetBaselineRMS()*calibration[i]
            if channel[i] == pmt_channel:
                energy[i] = exo_wfm.GetMaxValue()*calibration_values[channel[i]]
                lightEnergy[0] = energy[i]
            else:
                if struck_analysis_parameters.charge_channels_to_use[channel[i]]:
                    chargeEnergy[0] += energy[i]


            if do_debug and i == 4 and chargeEnergy[0] > 100:
                print "chargeEnergy", chargeEnergy[0]
                exo_sum_wfm.GimmeHist().Draw()
                canvas.Update()
                val = raw_input("sum wfm")


            if do_debug:
                if do_draw_extra:
                    print "energy measurement with %i samples: %.2f" % (
                        n_baseline_samples[0], energy[i])
                    energy_wfm.GimmeHist().Draw()
                    canvas.Update()
                    val = raw_input("press enter ")

            # measure energy before PZ correction, use 2x n_baseline_samples
            baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(exo_wfm)
            baseline_remover.SetStartSample(wfm_length[i] - 2*n_baseline_samples[0] - 1)
            baseline_remover.Transform(exo_wfm,energy_wfm)
            energy1[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms1[i] = baseline_remover.GetBaselineRMS()*calibration[i]

            if do_debug:
                if do_draw_extra:
                    print "energy measurement with %i samples: %.2f" % (
                        2*n_baseline_samples[0], energy1[i])
                    energy_wfm.GimmeHist().Draw()
                    canvas.Update()
                    val = raw_input("press enter ")

            # correct for exponential decay
            pole_zero = EXOPoleZeroCorrection()
            
            try:
                decay_time[i] = decay_time_values[channel[i]]
            except KeyError:
                print "no decay info for channel %i" % channel[i]
                decay_time[i] = 1e9*CLHEP.microsecond

            pole_zero.SetDecayConstant(decay_time[i])
            pole_zero.Transform(exo_wfm,energy_wfm)

            # measure energy after PZ correction
            baseline_remover.SetBaselineSamples(n_baseline_samples[0])
            baseline_remover.SetStartSample(wfm_length[i] - n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm)
            energy_pz[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms_pz[i] = baseline_remover.GetBaselineRMS()*calibration[i]

                
            # perform a fit to pz-corrected waveform:
            wfm_hist = energy_wfm.GimmeHist()
            # wfm times are in ns, wfm hist x-axis is in microseconds:
            fit_min = (energy_wfm.GetMaxTime()-n_baseline_samples[0]*period)/CLHEP.microsecond # x min
            fit_max = (energy_wfm.GetMaxTime())/CLHEP.microsecond  # x max
            #print fit_min, fit_max
            fit_result = wfm_hist.Fit(
                "pol1", # fit function
                "SQ", # fit options: S=save result, Q=quiet mode
                "L", # graphing options
                fit_min, # x min
                fit_max  # x max
            )
            try:
                pz_p1[i] = fit_result.Get().Parameter(1)
                pz_p1_err[i] = fit_result.Get().ParError(1)
            except ReferenceError:
                # if wfm is zeroes,  fit ptr is null:
                pz_p1[i] = 0.0
                pz_p1_err[i] = 0.0

            if do_debug:
                print "energy measurement after PZ with %i samples: %.2f" % (
                    n_baseline_samples[0], energy_pz[i])
                print fit_result
                #print pz_p1[i], pz_p1_err[i]
                wfm_hist.Draw()
                canvas.Update()
                val = raw_input("press enter ")


            # measure energy after PZ correction, use 2x n_baseline_samples
            baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(exo_wfm)

            if do_debug:
                exo_wfm.GimmeHist().Draw()
                canvas.Update()
                print "removed baseline before 2x PZ energy"
                val = raw_input("press enter ")

            # FIXME -- having trouble doing PZ transform in place!!
            #pole_zero.Transform(energy_wfm, energy_wfm)
            pole_zero.Transform(exo_wfm, energy_wfm)
            #print pole_zero.GetDecayConstant()

            if do_debug:
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                print "PZ transform"
                val = raw_input("enter to continue")

            baseline_remover.SetStartSample(wfm_length[i] - 2*n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm)
            energy1_pz[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms1_pz[i] = baseline_remover.GetBaselineRMS()*calibration[i]

            hist = energy_hists[channel[i]]
            if channel[i] == 8:
                hist.Fill(energy[i])
            else:
                hist.Fill(energy1_pz[i])


            if do_debug:
                print "energy measurement after PZ with %i samples: %.2f" % (
                    2*n_baseline_samples[0], energy1_pz[i])
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                print "energy calc"
                val = raw_input("enter to continue")


            # perform some smoothing -- be careful because this changes the rise
            # time
            smoother = EXOSmoother()
            smoother.SetSmoothSize(5)
            #smoother.SetSmoothSize(50)
            smoother.Transform(exo_wfm,new_wfm) #FIXME

            #pole_zero.Transform(new_wfm, new_wfm) # FIXME -- just for drawing

            smoothed_max[i] = new_wfm.GetMaxValue()
            if do_debug:
                print "smoothed_max", smoothed_max

            # used smoothed max val to calculate rise time
            # FIXME -- maybe we should think about this...
            #max_val = exo_wfm.GetMaxValue()
            max_val = new_wfm.GetMaxValue() # smoothed max
            #print max_val

            rise_time_calculator = EXORisetimeCalculation()
            rise_time_calculator.SetPulsePeakHeight(max_val)

            rise_time_calculator.SetFinalThresholdPercentage(0.1)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop10[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.2)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop20[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.3)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop30[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.4)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop40[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.5)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop50[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.6)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop60[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.7)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop70[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.8)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
            rise_time_stop80[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.90)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
                #print rise_time_calculator.GetInitialThresholdCrossing()
                #print rise_time_calculator.GetFinalThresholdCrossing()
            rise_time_stop90[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond
            #rise_time[i] = rise_time_calculator.GetRiseTime()/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.95)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
                #print rise_time_calculator.GetInitialThresholdCrossing()
                #print rise_time_calculator.GetFinalThresholdCrossing()
            rise_time_stop95[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

            rise_time_calculator.SetFinalThresholdPercentage(0.99)
            rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
            rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
            if max_val > 0.0: # throws an alert if max_val is 0
                rise_time_calculator.Transform(exo_wfm, exo_wfm)
                #print rise_time_calculator.GetInitialThresholdCrossing()
                #print rise_time_calculator.GetFinalThresholdCrossing()
            rise_time_stop99[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond


            """
            trap_filter = EXOTrapezoidalFilter()
            trap_filter.SetFlatTime(1.0*CLHEP.microsecond)
            trap_filter.SetRampTime(1.0*CLHEP.microsecond)
            trap_filter.Transform(exo_wfm, new_wfm)
            """
         

            # pause & draw
            #if not gROOT.IsBatch() and channel[i] == 4:
            #if not gROOT.IsBatch() and smoothed_max[i] > 60 and channel[i] != pmt_channel:
            #if not gROOT.IsBatch() and i_entry > 176:
            #if not gROOT.IsBatch():
            if not gROOT.IsBatch() and do_debug:

                print "--> entry %i | channel %i" % (i_entry, channel[i])
                print "\t n samples: %i" % wfm_length[i]
                print "\t max %.2f" % wfm_max[i]
                print "\t min %.2f" % wfm_min[i]
                print "\t smoothed max %.2f" % smoothed_max[i]
                #print "\t rise time [microsecond]: %.3f" % (rise_time[i])
                print "\t rise stop 50 [microsecond]: %.2f" % (rise_time_stop50[i])
                print "\t rise stop 90 [microsecond]: %.2f" % (rise_time_stop90[i])
                print "\t rise stop 95 [microsecond]: %.2f" % (rise_time_stop95[i])
                print "\t rise stop 99 [microsecond]: %.2f" % (rise_time_stop99[i])
                print "\t baseline mean: %.3f" % baseline_mean[i]
                print "\t baseline RMS: %.3f" % baseline_rms[i]
                print "\t energy: %.3f" % energy[i]
                print "\t energy RMS: %.3f" % energy_rms[i]
                print "\t energy1: %.3f" % energy1[i]
                print "\t energy RMS1: %.3f" % energy_rms1[i]
                print "\t energy_pz: %.3f" % energy_pz[i]
                print "\t energy RMS pz: %.3f" % energy_rms_pz[i]
                print "\t energy1 pz: %.3f" % energy1_pz[i]
                print "\t energy1 RMS pz: %.3f" % energy_rms1_pz[i]


                hist = exo_wfm.GimmeHist("hist")
                hist.SetLineWidth(2)
                #hist.SetAxisRange(4,6)
                hist.Draw()

                hist1 = new_wfm.GimmeHist("hist1")
                hist1.SetLineWidth(2)
                hist1.SetLineColor(TColor.kBlue)
                hist1.Draw("same")

                canvas.Update()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

                print val
                if (val == 'q' or val == 'Q'): sys.exit(1) 
                if val == 'b': gROOT.SetBatch(True)
                if val == 'p': canvas.Print("entry_%i_proc_wfm_%s.png" % (i_entry, basename,))
                
            # end loop over channels

        out_tree.Fill()


    print "energy histograms:"
    
    run_tree.Write()
    for channel in channels:
        
        hist = energy_hists[channel]
        print "\t channel %i : %i counts" % (channel, hist.GetEntries())
        hist.Write()

    print "done processing"
    print "writing", out_filename
    out_tree.Write()


if __name__ == "__main__":


    parser = OptionParser()
    parser.add_option("--no-overwrite", dest="do_overwrite", default=True,
                      action="store_false", help="whether to overwrite files")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")

    (options, filenames) = parser.parse_args()

    if len(filenames) < 1:
        print "arguments: [sis root files]"
        sys.exit(1)

    print "%i files to process" % len(filenames)

    for filename in filenames:
        process_file(filename, verbose=options.verbose, do_overwrite=options.do_overwrite)





