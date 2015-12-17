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
import datetime
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

    # whether to run in debug mode (draw wfms):
    do_debug = not gROOT.IsBatch()
    do_draw_extra = not gROOT.IsBatch()

    reporting_period = 1000

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    pmt_channel = struck_analysis_parameters.pmt_channel
    #n_channels = struck_analysis_parameters.n_channels

    # this is the number of channels per event (1 if we are processing tier1
    # data, len(channels) if we are processing tier2 data
    #n_channels_in_event = n_channels

    #---------------------------------------------------------------

    print "processing file: ", filename

    # keep track of how long it takes to process file:
    start_time = time.clock()
    last_time = start_time
    prev_time_stamp = 0.0

    # make a basename for names of output file, plots, etc:
    basename = create_basename(filename)

    # calculate file start time, in POSIX time, from filename suffix
    # date and time are the last two parts of filename separated with "_":
    try:
        file_start = "_".join(basename.split("_")[-2:])
        file_start = datetime.datetime.strptime(file_start, "%Y-%m-%d_%H-%M-%S")
        posix_start_time = int(time.mktime(file_start.timetuple()))
    except:
        posix_start_time = 0

    # a canvas for drawing, if debugging:
    canvas = TCanvas()
    canvas.SetGrid(1,1)

    # open the root file 
    root_file = TFile(filename, "READ")

    # open output file and tree
    out_filename = create_outfile_name(filename)
    if not do_overwrite:
        if os.path.isfile(out_filename):
            print "file exists!"
            return 0
    out_file = TFile(out_filename, "RECREATE")
    
    # initialize the trees; only saving nonempty trees
    tree = []
    n_entries = []
    channels = [] # saves the channels of the trees
    for i in xrange(16): 
        tree.append(root_file.Get("tree%i" % i))
        try: # see if tree exists
            tree[-1].GetEntries() 
        except AttributeError:
            print "problem accessing tree%i -- skipping this file" % i
            return 0
        if tree[-1].GetEntries() == 0: # if tree is empty
            tree.pop()
            continue
        n_entries.append(tree[-1].GetEntries())
        channels.append(i)

    if len(channels) == 0:
        print "==> all trees are empty! -- skipping this file"
        return 0
    n_channels = len(channels) # this saves the number of channels in this file

    out_tree = TTree("tree", "%s processed wfm tree" % basename)
    run_tree = TTree("run_tree", "%s run tree" % basename)

    ## set up global parameter branches
    channels = array('B', channels) # unsigned char # note that name of branch is different from variable
    out_tree.Branch('channel', channels, 'channel[%i]/b' % n_channels)

    is_external = array('B', [0]) # unsigned char
    out_tree.Branch('is_external', is_external, 'is_external/b')

    is_2Vinput = array('B', [0]*n_channels) # unsigned char
    out_tree.Branch('is_2Vinput', is_2Vinput, 'is_2Vinput[%i]/b' % n_channels)

    is_50ohm = array('B', [0]*n_channels) # unsigned char 
    out_tree.Branch('is_50ohm', is_50ohm, 'is_50ohm[%i]/b' % n_channels)

    is_pospolarity = array('B', [0]*n_channels) # unsigned char
    out_tree.Branch('is_pospolarity', is_pospolarity, 'is_pospolarity[%i]/b' % n_channels)

    sampling_freq_Hz = array('d', [0]) # double
    out_tree.Branch('sampling_freq_Hz', sampling_freq_Hz, 'sampling_freq_Hz/D')

    trigger_time = array('d', [0.0]) # double
    out_tree.Branch('trigger_time', trigger_time, 'trigger_time/D')
    run_tree.Branch('trigger_time', trigger_time, 'trigger_time/D')

    wfm_length = array('I', [0]) # unsigned int
    out_tree.Branch('wfm_length', wfm_length, 'wfm_length/i')

    for i in xrange(n_channels): ## set the global parameter values
        tree[i].GetEntry(0)
        is_2Vinput[i] = tree[i].is_2Vinput
        is_50ohm[i] = tree[i].is_50ohm
        is_pospolarity[i] = tree[i].is_pospolarity
    is_external[0] = tree[0].is_external
    if not is_external[0]: # FIXME--now skipping internally triggered files
        print "skipping internally triggered files"
        return 0
    sampling_freq_Hz[0] = tree[0].sampling_freq
    trigger_time[0] = tree[0].wfm_delay / sampling_freq_Hz[0] * 1e6  ## in microseconds
    wfm_length[0] = tree[0].wfm_length

    #store some processing parameters:
    n_baseline_samples = array('I', [0]) # double
    out_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')
    n_baseline_samples[0] = tree[0].wfm_delay / 4

    decay_time = array('d', [0]*n_channels) # double
    out_tree.Branch('decay_time', decay_time, 'decay_time[%i]/D' % n_channels)
    decay_time_values = struck_analysis_parameters.decay_time_values
    decay_time_values[pmt_channel] = 1e9*CLHEP.microsecond
    for (i, channel) in enumerate(channels):
        try:
            decay_time[i] = decay_time_values[channel]
        except KeyError:
            print "no decay info for channel %i" % channel
            decay_time[i] = 1e9*CLHEP.microsecond

    calibration = array('d', [0.0]*n_channels) # double
    out_tree.Branch('calibration', calibration, 'calibration[%i]/D' % n_channels)
    for (i, channel) in enumerate(channels):
        try:
            calibration[i] = struck_analysis_parameters.calibration_values[channel]
        except KeyError:
            print "no calibration info for channel %i" % channel
            calibration[i] = 1.0
        if is_2Vinput[i]:
            calibration[i] /= 2.5

    # file parameters
    file_start_time = array('I', [0]) # unsigned int
    file_start_time[0] = posix_start_time
    out_tree.Branch('file_start_time', file_start_time, 'file_start_time/i')
    run_tree.Branch('file_start_time', file_start_time, 'file_start_time/i')

    n_entries_array = array('I', [min(n_entries)]) # unsigned int
    out_tree.Branch('n_entries', n_entries_array, 'n_entries/i')
    run_tree.Branch('n_entries', n_entries_array, 'n_entries/i')

   # run_time = array('d', [0]) # estimate run time by subtracting last time stamp from first time stamp
   # out_tree.Branch('run_time', run_time, 'run_time/D')
   # run_time[0] = (tree[0].GetMaximum("timestampDouble") -
   #                tree[0].GetMinimum("timestampDouble"))/sampling_freq_Hz
   # print "run time: %.2f seconds" % run_time[0]

    ## event-specific parameters
    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    timestamp = array('L', [0]) # timestamp for each event, unsigned long
    out_tree.Branch('timestamp', timestamp, 'timestamp/l')

    timestampDouble = array('d', [0]) # double
    out_tree.Branch('timestampDouble', timestampDouble, 'timestampDouble/D')

    time_since_last = array('d', [0]) # double
    out_tree.Branch('time_since_last', time_since_last, 'time_since_last/D')

    rise_time_stop10 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop10', rise_time_stop10, 'rise_time_stop10[%i]/D' % n_channels)

    rise_time_stop20 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop20', rise_time_stop20, 'rise_time_stop20[%i]/D' % n_channels)

    rise_time_stop30 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop30', rise_time_stop30, 'rise_time_stop30[%i]/D' % n_channels)

    rise_time_stop40 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop40', rise_time_stop40, 'rise_time_stop40[%i]/D' % n_channels)

    rise_time_stop50 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop50', rise_time_stop50, 'rise_time_stop50[%i]/D' % n_channels)

    rise_time_stop60 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop60', rise_time_stop60, 'rise_time_stop60[%i]/D' % n_channels)

    rise_time_stop70 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop70', rise_time_stop70, 'rise_time_stop70[%i]/D' % n_channels)

    rise_time_stop80 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop80', rise_time_stop80, 'rise_time_stop80[%i]/D' % n_channels)

    rise_time_stop90 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop90', rise_time_stop90, 'rise_time_stop90[%i]/D' % n_channels)

    rise_time_stop95 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop95', rise_time_stop95, 'rise_time_stop95[%i]/D' % n_channels)

    rise_time_stop99 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop99', rise_time_stop99, 'rise_time_stop99[%i]/D' % n_channels)

    smoothed_max = array('d', [0]*n_channels) # double
    out_tree.Branch('smoothed_max', smoothed_max, 'smoothed_max[%i]/D' % n_channels)

    baseline_mean = array('d', [0]*n_channels) # double
    out_tree.Branch('baseline_mean', baseline_mean, 'baseline_mean[%i]/D' % n_channels)

    baseline_rms = array('d', [0]*n_channels) # double
    out_tree.Branch('baseline_rms', baseline_rms, 'baseline_rms[%i]/D' % n_channels)

    # energy & rms before processing 
    energy = array('d', [0]*n_channels) # double
    out_tree.Branch('energy', energy, 'energy[%i]/D' % n_channels)
    energy_rms = array('d', [0]*n_channels) # double
    out_tree.Branch('energy_rms', energy_rms, 'energy_rms[%i]/D' % n_channels)

    # energy & rms before processing, using 2x sample length
    energy1 = array('d', [0]*n_channels) # double
    out_tree.Branch('energy1', energy1, 'energy1[%i]/D' % n_channels)
    energy_rms1 = array('d', [0]*n_channels) # double
    out_tree.Branch('energy_rms1', energy_rms1, 'energy_rms1[%i]/D' % n_channels)

    # energy & rms after PZ
    energy_pz = array('d', [0]*n_channels) # double
    out_tree.Branch('energy_pz', energy_pz, 'energy_pz[%i]/D' % n_channels)
    energy_rms_pz = array('d', [0]*n_channels) # double
    out_tree.Branch('energy_rms_pz', energy_rms_pz, 'energy_rms_pz[%i]/D' % n_channels)

    # energy & rms after PZ, using 2x sample length
    energy1_pz = array('d', [0]*n_channels) # double
    out_tree.Branch('energy1_pz', energy1_pz, 'energy1_pz[%i]/D' % n_channels)
    energy_rms1_pz = array('d', [0]*n_channels) # double
    out_tree.Branch('energy_rms1_pz', energy_rms1_pz, 'energy_rms1_pz[%i]/D' % n_channels)
 
    # charge & light energy
    chargeEnergy = array('d', [0.0]) # double
    out_tree.Branch('chargeEnergy', chargeEnergy, 'chargeEnergy/D')

    lightEnergy = array('d', [0.0]) # double
    out_tree.Branch('lightEnergy', lightEnergy, 'lightEnergy/D')

   # #some file-averaged parameters
   # baseline_mean_file = array('d', [0]*n_channels) # double
   # out_tree.Branch('baseline_mean_file', baseline_mean_file, 'baseline_mean_file[%i]/D' % n_channels)
   # run_tree.Branch('baseline_mean_file', baseline_mean_file, 'baseline_mean_file[%i]/D' % n_channels)

   # baseline_rms_file = array('d', [0]*n_channels) # double
   # out_tree.Branch('baseline_rms_file', baseline_rms_file, 'baseline_rms_file[%i]/D' % n_channels)
   # run_tree.Branch('baseline_rms_file', baseline_rms_file, 'baseline_rms_file[%i]/D' % n_channels)

    #parameters coming from sum waveform
    rise_time_stop10_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop10_sum', rise_time_stop10_sum, 'rise_time_stop10_sum/D')

    rise_time_stop20_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop20_sum', rise_time_stop20_sum, 'rise_time_stop20_sum/D')

    rise_time_stop30_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop30_sum', rise_time_stop30_sum, 'rise_time_stop30_sum/D')

    rise_time_stop40_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop40_sum', rise_time_stop40_sum, 'rise_time_stop40_sum/D')

    rise_time_stop50_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop50_sum', rise_time_stop50_sum, 'rise_time_stop50_sum/D')

    rise_time_stop60_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop60_sum', rise_time_stop60_sum, 'rise_time_stop60_sum/D')

    rise_time_stop70_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop70_sum', rise_time_stop70_sum, 'rise_time_stop70_sum/D')

    rise_time_stop80_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop80_sum', rise_time_stop80_sum, 'rise_time_stop80_sum/D')

    rise_time_stop90_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop90_sum', rise_time_stop90_sum, 'rise_time_stop90_sum/D')

    rise_time_stop95_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop95_sum', rise_time_stop95_sum, 'rise_time_stop95_sum/D')

    rise_time_stop99_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop99_sum', rise_time_stop99_sum, 'rise_time_stop99_sum/D')

    smoothed_max_sum = array('d', [0.0]) # double
    out_tree.Branch('smoothed_max_sum', smoothed_max_sum, 'smoothed_max_sum/D')

    energy_sum = array('d', [0.0])
    out_tree.Branch('energy_sum', energy_sum, 'energy_sum/D')

    energy_rms_sum = array('d', [0.0])
    out_tree.Branch('energy_rms_sum', energy_rms_sum, 'energy_rms_sum/D')
   
    # file name branch
    fname = TObjString(os.path.abspath(filename))
    out_tree.Branch("filename",fname)
    run_tree.Branch("filename",fname)

    if do_debug:
        reporting_period = 1

    print "%i entries" % min(n_entries)


    run_tree.Fill() # this tree only has one entry with run-level entries 



    last_timestamp = 0.0 # used to save timestamp of last event

    for i_entry in xrange(min(n_entries)):
        event[0] = i_entry
        # print periodic output message
        if i_entry % reporting_period == 0:
            now = time.clock()
            print "----> entry %i of %i (%.2f percent in %.1f seconds, %.1f seconds total)" % (
                i_entry, min(n_entries), 100.0*i_entry/min(n_entries), now - last_time, now -
                start_time)
            last_time = now

        # initialize some values
        chargeEnergy[0] = 0.0
        lightEnergy[0] = 0.0

        # loop over channels
        for (i, channel) in enumerate(channels):
            tree[i].GetEntry(i_entry)
            
            # save and check timestamps
            if i == 0:
                timestamp[0] = tree[i].timestamp
                timestampDouble[0] = tree[i].timestampDouble
                time_since_last[0] = timestampDouble[0] - last_timestamp
                last_timestamp = timestampDouble[0]
            else:
                if timestamp[0] != tree[i].timestamp: ## if the timestamps does not agree
                    print "==> timestamps do not agree; stop processing ..."
                    return 0

       ## make a hist for calculating some averages
       # hist = TH1D("hist","",100, 0, pow(2,14))
       # print "calculating mean baseline & baseline RMS for each channel in this file..."
       # for (i, i_channel) in enumerate(channels):
       #     print "%i: ch %i" % (i, i_channel)
       #     selection = "Iteration$<%i && channel==%i" % (n_baseline_samples[0], i_channel)

       #     if do_debug: continue
       #         
       #     # calculate avg baseline:
       #     draw_command = "wfm >> hist"
       #     if not is_tier1:
       #         draw_command = "wfm%i >> hist" % i_channel
       #     tree.Draw(
       #         draw_command,
       #         selection,
       #         "goff"
       #     )
       #     baseline_mean_file[i] = hist.GetMean()
       #     print "\t draw command: %s | selection %s" % (draw_command, selection)
       #     print "\t file baseline mean:", baseline_mean_file[i]

       #     # calculate baseline RMS:
       #     # this is an appxorimation -- we can't calculate the real RMS until we
       #     # know the baseline average for each wfm -- it would be better to do
       #     # this in the loop over events
       #     draw_command = "wfm-wfm[0] >> hist"
       #     if not is_tier1:
       #         draw_command = "wfm%i-wfm%i[0] >> hist" % (i_channel, i_channel)
       #     tree.Draw(
       #         draw_command,
       #         selection,
       #         "goff"
       #     )
       #     baseline_rms_file[i] = hist.GetRMS()
       #     print "\t draw command: %s | selection %s" % (draw_command, selection)
       #     print "\t file baseline rms:", baseline_rms_file[i]

       # print "\t done"

       # # decide whether 2V input was used for the digitizer or not. The
       # # file-averaged baseline mean for channel 0 seems like a good indicator of
       # # this -- we should also figure out if any channels are shaped...

       # calibration_values = struck_analysis_parameters.calibration_values

       # print "choosing calibration values..."
       # for (i, i_channel) in enumerate(channels):
       #     print "channel %i" % i_channel

       #     try:
       #         print "\t original calibration value %.4e" % calibration_values[i_channel]
       #     except KeyError:
       #         print "\t no calibration data for ch %i" % i_channel
       #         continue

       #     is_2Vinput[i] = struck_analysis_parameters.is_2Vinput(baseline_mean_file[i])
       #     if is_2Vinput[i]:
       #         print "\t channel %i used 2V input range" % i_channel
       #         print "\t dividing calibration by 2.5"
       #         calibration_values[i_channel] /= 2.5

       #     # this doesn't seem very reliable
       #     #is_amplified[i] = struck_analysis_parameters.is_amplified(
       #     #    baseline_mean_file[i], baseline_rms_file[i])


       #     if is_amplified[i] == 0:
       #         if i_channel != pmt_channel:
       #             calibration_values[i_channel] *= 4.0
       #             print "\t multiplying calibration by 4"
       #             print "\t channel %i is unamplified" % i_channel
       #     print "\t channel %i calibration: %.4e" % (i_channel, calibration_values[i_channel])

       # # PMT threshold
       # pmt_threshold = array('d', [0]) # double
       # out_tree.Branch('pmt_threshold', pmt_threshold, 'pmt_threshold/D')
       # run_tree.Branch('pmt_threshold', pmt_threshold, 'pmt_threshold/D')

       # # calculate PMT threshold...
       # draw_command = "wfm_max-wfm[0] >> hist"
       # if not is_tier1:
       #     draw_command = "wfm_max-wfm%i[0] >> hist" % pmt_channel

       # tree.Draw(draw_command,"channel==%i" % pmt_channel,"goff")
       # pmt_threshold[0] = hist.GetBinLowEdge(hist.FindFirstBinAbove(0))*calibration_values[pmt_channel]
       # print "pmt_threshold:", pmt_threshold[0]

            wfm = tree[i].wfm

            exo_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[0])
            new_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[0])
            energy_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[0])

            exo_wfm.SetSamplingFreq(sampling_freq_Hz[0]/CLHEP.second)
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

            # measure energy before PZ correction
            baseline_remover.SetStartSample(wfm_length[0] - n_baseline_samples[0] - 1)
            baseline_remover.Transform(exo_wfm, energy_wfm)

            energy[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms[i] = baseline_remover.GetBaselineRMS()*calibration[i]
            if channel == pmt_channel: # for PMT channel, use GetMaxValue()
                energy[i] = exo_wfm.GetMaxValue()*calibration[i]
                lightEnergy[0] = energy[i]

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
            baseline_remover.SetStartSample(wfm_length[0] - 2*n_baseline_samples[0] - 1)
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
            pole_zero.SetDecayConstant(decay_time[i])
            pole_zero.Transform(exo_wfm, energy_wfm)

            # measure energy after PZ correction
            baseline_remover.SetBaselineSamples(n_baseline_samples[0])
            baseline_remover.SetStartSample(wfm_length[0] - n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm)
            energy_pz[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms_pz[i] = baseline_remover.GetBaselineRMS()*calibration[i]

                
           # # perform a fit to pz-corrected waveform:
           # wfm_hist = energy_wfm.GimmeHist()
           # # wfm times are in ns, wfm hist x-axis is in microseconds:
           # fit_min = (energy_wfm.GetMaxTime()-n_baseline_samples[0]*period)/CLHEP.microsecond # x min
           # fit_max = (energy_wfm.GetMaxTime())/CLHEP.microsecond  # x max
           # #print fit_min, fit_max
           # fit_result = wfm_hist.Fit(
           #     "pol1", # fit function
           #     "SQ", # fit options: S=save result, Q=quiet mode
           #     "L", # graphing options
           #     fit_min, # x min
           #     fit_max  # x max
           # )
           # try:
           #     pz_p1[i] = fit_result.Get().Parameter(1)
           #     pz_p1_err[i] = fit_result.Get().ParError(1)
           # except ReferenceError:
           #     # if wfm is zeroes,  fit ptr is null:
           #     pz_p1[i] = 0.0
           #     pz_p1_err[i] = 0.0

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

            pole_zero.Transform(exo_wfm, energy_wfm)

            # adding to sum wfm
            calibrated_wfm = EXODoubleWaveform(energy_wfm)
            calibrated_wfm *= calibration[i]
            if struck_analysis_parameters.charge_channels_to_use[channel]:
                if i == 0:
                    sum_wfm = EXODoubleWaveform(calibrated_wfm)
                else:
                    sum_wfm += calibrated_wfm

            if do_debug:
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                print "PZ transform"
                val = raw_input("enter to continue")

            baseline_remover.SetStartSample(wfm_length[0] - 2*n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm)
            energy1_pz[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms1_pz[i] = baseline_remover.GetBaselineRMS()*calibration[i]

            if struck_analysis_parameters.charge_channels_to_use[channel]:
                chargeEnergy[0] += energy1_pz[i]

            if do_debug:
                print "energy measurement after PZ with %i samples: %.2f" % (
                    2*n_baseline_samples[0], energy1_pz[i])
                energy_wfm.GimmeHist("").Draw()
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

            # rise time calculator thresholds are called precentage, but they
            # are really fractions...
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

              #  # pause & draw
              #  #if not gROOT.IsBatch() and channel[i] == 4:
              #  #if not gROOT.IsBatch() and smoothed_max[i] > 60 and channel[i] != pmt_channel:
              #  #if not gROOT.IsBatch() and i_entry > 176:
              #  #if not gROOT.IsBatch():
              #  if not gROOT.IsBatch() and do_debug:

              #      print "--> entry %i | channel %i" % (i_entry, channel[i])
              #      print "\t n samples: %i" % wfm_length[i]
              #      print "\t max %.2f" % wfm_max[i]
              #      print "\t min %.2f" % wfm_min[i]
              #      print "\t smoothed max %.2f" % smoothed_max[i]
              #      #print "\t rise time [microsecond]: %.3f" % (rise_time[i])
              #      print "\t rise stop 50 [microsecond]: %.2f" % (rise_time_stop50[i])
              #      print "\t rise stop 90 [microsecond]: %.2f" % (rise_time_stop90[i])
              #      print "\t rise stop 95 [microsecond]: %.2f" % (rise_time_stop95[i])
              #      print "\t rise stop 99 [microsecond]: %.2f" % (rise_time_stop99[i])
              #      print "\t baseline mean: %.3f" % baseline_mean[i]
              #      print "\t baseline RMS: %.3f" % baseline_rms[i]
              #      print "\t energy: %.3f" % energy[i]
              #      print "\t energy RMS: %.3f" % energy_rms[i]
              #      print "\t energy1: %.3f" % energy1[i]
              #      print "\t energy RMS1: %.3f" % energy_rms1[i]
              #      print "\t energy_pz: %.3f" % energy_pz[i]
              #      print "\t energy RMS pz: %.3f" % energy_rms_pz[i]
              #      print "\t energy1 pz: %.3f" % energy1_pz[i]
              #      print "\t energy1 RMS pz: %.3f" % energy_rms1_pz[i]


              #      hist = exo_wfm.GimmeHist("hist")
              #      hist.SetLineWidth(2)
              #      #hist.SetAxisRange(4,6)
              #      hist.Draw()

              #      hist1 = new_wfm.GimmeHist("hist1")
              #      hist1.SetLineWidth(2)
              #      hist1.SetLineColor(TColor.kBlue)
              #      hist1.Draw("same")
            if do_debug:
                canvas.Update()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

                print val
                if (val == 'q' or val == 'Q'): sys.exit(1) 
                if val == 'b': gROOT.SetBatch(True)
                if val == 'p': canvas.Print("entry_%i_proc_wfm_%s.png" % (i_entry, basename))
            
            # end loop over channels

        ##### processing sum waveform
        new_wfm = EXODoubleWaveform(sum_wfm)
        smoother = EXOSmoother()
        smoother.SetSmoothSize(5)
        smoother.Transform(sum_wfm,new_wfm) 

        smoothed_max_sum[0] = new_wfm.GetMaxValue()
        if do_debug:
            print "smoothed_max", smoothed_max

        # used smoothed max val to calculate rise time
        # FIXME -- maybe we should think about this...
        max_val = new_wfm.GetMaxValue() # smoothed max

        rise_time_calculator = EXORisetimeCalculation()
        rise_time_calculator.SetPulsePeakHeight(max_val)

        # rise time calculator thresholds are called precentage, but they
        # are really fractions...
        rise_time_calculator.SetFinalThresholdPercentage(0.1)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop10_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.2)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop20_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.3)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop30_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.4)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop40_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.5)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop50_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.6)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop60_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.7)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop70_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.8)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
        rise_time_stop80_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.90)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
            #print rise_time_calculator.GetInitialThresholdCrossing()
            #print rise_time_calculator.GetFinalThresholdCrossing()
        rise_time_stop90_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond
        #rise_time[i] = rise_time_calculator.GetRiseTime()/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.95)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
            #print rise_time_calculator.GetInitialThresholdCrossing()
            #print rise_time_calculator.GetFinalThresholdCrossing()
        rise_time_stop95_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond

        rise_time_calculator.SetFinalThresholdPercentage(0.99)
        rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
        rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
        if max_val > 0.0: # throws an alert if max_val is 0
            rise_time_calculator.Transform(sum_wfm, sum_wfm)
            #print rise_time_calculator.GetInitialThresholdCrossing()
            #print rise_time_calculator.GetFinalThresholdCrossing()
        rise_time_stop99_sum[0] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond
        
        baseline_remover = EXOBaselineRemover()
        baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
        baseline_remover.SetStartSample(wfm_length[0] - 2*n_baseline_samples[0] - 1)
        baseline_remover.Transform(sum_wfm)
        energy_sum[0] = baseline_remover.GetBaselineMean()
        energy_rms_sum[0] = baseline_remover.GetBaselineRMS()

        out_tree.Fill()
        #end event loop


   # print "energy histograms:"
    
    run_tree.Write()
   # for channel in channels:
   #     
   #     hist = energy_hists[channel]
   #     print "\t channel %i : %i counts" % (channel, hist.GetEntries())
   #     hist.Write()

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





