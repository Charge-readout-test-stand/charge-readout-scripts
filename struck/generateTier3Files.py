#!/usr/bin/env python

"""
Do some waveform processing to extract energies, etc. 

EXO class index, with waveform transformers: 
http://exo-data.slac.stanford.edu/exodoc/ClassIndex.html

NGM to do list:
* add time stamp for each channel?

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

For MC:
    python generateTier3Files.py --MC -D [output_directory] [MCFile_name]  
Testing:
    python generateTier3Files.py --MC -D /nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207/Tier3/ /nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207/Digi/Test_Bi207_Ralph_Full_X27.root
    python submitPythonJobsSLAC.py "generateTier3Files.py --MC -D /nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/electron/Tier3/ " /nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/electron/Digi/digi*.root


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
import math
import datetime
import commands
import numpy as np
import copy
from optparse import OptionParser

import ROOT

ROOT.gROOT.SetBatch(True) # run in batch mode

import subprocess
root_version = subprocess.check_output(['root-config --version'], shell=True)

#Works sometimes other times gives 8.0.0????
#root_version = ROOT.module.__version__

print "ROOT Version is", root_version

#print type(root_version)
#print "Current ROOT Version is", root_version

isROOT6 = False
if '6.1.0' in root_version or '6.04/06' in root_version:
    print "Found ROOT 6"
    isROOT6 = True

if os.getenv("EXOLIB") is not None and not isROOT6:
    try:
        print "loading libEXOROOT"
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
    except:
        pass

microsecond = 1.0e3
second = 1.0e9

from ROOT import EXOTrapezoidalFilter
from ROOT import EXOBaselineRemover
from ROOT import EXODoubleWaveform
from ROOT import TObjString

from array import array

# definition of calibration constants, decay times, channels
import struck_analysis_parameters
import struck_analysis_cuts
import wfmProcessing
import BundleSignals

def process_file(filename, dir_name= "", verbose=True, do_overwrite=True, isMC=False, isMakeNoise=False, noise_file=None):

    #---------------------------------------------------------------
    # options
    #---------------------------------------------------------------

    #print "verbose:", verbose
    #print "do_overwrite:", do_overwrite

    # whether to run in debug mode (draw wfms):
    do_debug = not ROOT.gROOT.IsBatch()
    do_draw_extra = not ROOT.gROOT.IsBatch()
    skip_short_risetimes = False # reduce file size
    # samples at wfm start and end to use for energy calc:

    baseline_average_time_microseconds = struck_analysis_parameters.baseline_average_time_microseconds
    # this is just the default; overwritten for NGM files:
    sampling_freq_Hz        = struck_analysis_parameters.sampling_freq_Hz
    channels                = struck_analysis_parameters.channels
    channel_map             = struck_analysis_parameters.channel_map
    n_chargechannels        = struck_analysis_parameters.n_chargechannels
    pmt_channel             = struck_analysis_parameters.pmt_channel
    pulser_channel          = struck_analysis_parameters.pulser_channel
    n_channels              = struck_analysis_parameters.n_channels
    charge_channels_to_use  = struck_analysis_parameters.charge_channels_to_use
    rms_keV                 = struck_analysis_parameters.rms_keV
    sipm_channels_to_use    = struck_analysis_parameters.sipm_channels_to_use
    dead_channels           = struck_analysis_parameters.dead_channels
    n_channels_good         = n_channels - sum(dead_channels)

    # this is the number of channels per event (1 if we are processing tier1
    # data, len(channels) if we are processing tier2 data
    n_channels_in_event = n_channels

    #---------------------------------------------------------------

    print "processing file: ", filename

    # keep track of how long it takes to process file:
    start_time = time.time()
    last_time = start_time
    prev_time_stamp = 0.0
    run_number = 0

    # a canvas for drawing, if debugging:
    if not ROOT.gROOT.IsBatch():
        canvas = ROOT.TCanvas("tier3_canvas","tier3_canvas")
        canvas.SetGrid(1,1)

    # open the root file and grab the tree
    root_file = ROOT.TFile(filename)
    isNGM = False # flag for Jason Newby's NGM code
    tree = None
    if isMC:
        tree = root_file.Get("evtTree") # MC
    else:
        tree = root_file.Get("tree") # struck root gui tier1
    
    try:
        n_entries = tree.GetEntries()
    except AttributeError:
        tree = root_file.Get("evtTree") # MC
        try:
            n_entries = tree.GetEntries()
            isMC = True
        except AttributeError:
            tree = root_file.Get("HitTree") # NGM tier1
            try:
                n_entries = tree.GetEntries()
                isNGM = True
                print "==> This is an NGM tree!"
            except AttributeError:
                print "==> problem accessing tree -- skipping this file"
                return

    print "%i entries in input tree" % n_entries
    reporting_period = 1000
    if isMC:
        reporting_period = 100
    if isNGM:
        reporting_period = 32*100 # 100 32-channel events


    if isMC:
        #MC has different structure so use MC channels
        #After the 8th LXe not sure we need alot of this
        #channels = struck_analysis_parameters.MCchannels
        #n_chargechannels = struck_analysis_parameters.n_MCchargechannels
        #pmt_channel = None #No PMT in MC
        #n_channels = struck_analysis_parameters.MCn_channels
        #charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
        generator = ROOT.TRandom3(0) # random number generator, initialized with TUUID object
        struck_to_mc_channel_map = struck_analysis_parameters.struck_to_mc_channel_map
        if noise_file is not None:
            noise_file_root = ROOT.TFile(noise_file)
            noise_tree = noise_file_root.Get("tree")
    if isMakeNoise:
        noise_length = struck_analysis_parameters.noise_length
        noiseLightCut = struck_analysis_parameters.noiseLightCut
        
    basename = wfmProcessing.create_basename(filename, isMC)

    # calculate file start time, in POSIX time, from filename suffix
    # date and time are last two parts of filename separated with "_":
    if isNGM:
        try:
            file_start = basename.split("_")[1]
            run_number = int(file_start)
            print "run_number:", run_number
            #print file_start
            # create datetime object from relevant parts of filename:
            file_start  = datetime.datetime.strptime(file_start, "%Y%m%d%H%M%S")
            print "File Start",file_start
            # get the POSIX timestamp, in seconds:
            posix_start_time = int(time.mktime(file_start.timetuple()))
            print posix_start_time
            print "this NGM file was started at: %s GMT" % file_start
            #raw_input()
        except: 
            print "couldn't calculate file start time"
            posix_start_time = 0
    elif isMC:
        posix_start_time = 0
    else:
        try:
            file_start = "_".join(basename.split("_")[-2:])
            #print file_start
            # create datetime object from relevant parts of filename:
            file_start  = datetime.datetime.strptime(file_start, "%Y-%m-%d_%H-%M-%S")
            # get the POSIX timestamp, in seconds:
            posix_start_time = int(time.mktime(file_start.timetuple()))
            #print posix_start_time
            #print "this file was started at:", file_start
        except:
            pass

    # decide if this is a tier1 or tier2 file
    is_tier1 = False
    if isMC is False and isNGM is False:
        try:
            tree.GetEntry(0)
            tree.wfm0
            print "this is a tier2 file"
        except AttributeError:
            print "this is a tier1 file"
            n_channels_in_event = 1
            is_tier1 = True
        
    if isMC:
        n_channels_in_event = n_channels
        is_tier1 = False

    # open output file and tree
    out_filename = wfmProcessing.create_outfile_name(filename, isMC)
    if isNGM:
        out_filename = "tier3_%s.root" % basename
    out_filename = dir_name + out_filename
    if not do_overwrite:
        if os.path.isfile(out_filename):
            print "file exists!"
            return 0
    out_file = ROOT.TFile(out_filename, "recreate")
    gout = out_file.GetDirectory("")
    out_tree = ROOT.TTree("tree", "%s processed wfm tree" % basename)
    out_tree.SetLineColor(ROOT.kBlue)
    out_tree.SetLineWidth(2)
    out_tree.SetMarkerColor(ROOT.kRed)
    out_tree.SetMarkerStyle(8)
    out_tree.SetMarkerSize(0.5)
    run_tree = ROOT.TTree("run_tree", "run-level data")

    # Writing trees in pyroot is clunky... need to use python arrays to provide
    # branch addresses, see:
    # http://wlav.web.cern.ch/wlav/pyroot/tpytree.html

    is_bad = array("I", [0]) # unsigned int, 0 if event is good
    out_tree.Branch('is_bad', is_bad, 'is_bad/i')
    # is_bad bits: 
    # 0: pmt shape chi^2 above threshold (2^0=1)
    # 1: RMS noise too high (2^1=2)
    # 2: energy1_pz noise too high (2^2=4)
    # 3: wfm min is at ADC min (2^3=8)
    # 4: wfm max is at ADC max (2^4=16)
    # 5: event doesn't contain correct number of channels (2^5=32)
    # 6: RMS noise too low (2^6=64)
    # 7: energy1_pz noise too low (2^7=128)

    is_2Vinput = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('is_2Vinput', is_2Vinput, 'is_2Vinput[%i]/i' % n_channels)

    is_amplified = array('I', [1]*n_channels) # unsigned int
    out_tree.Branch('is_amplified', is_amplified, 'is_amplified[%i]/i' % n_channels)

    run = array('L', [run_number]) # unsigned int
    out_tree.Branch('run', run, 'run/l')
    run_tree.Branch('run', run, 'run/l')

    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    if isMC:

        sub_event = array('I', [0]) # unsigned int
        out_tree.Branch('sub_event', sub_event, 'sub_event/i')

        GenX = array("d", [0])
        out_tree.Branch('GenX', GenX, 'GenX/D')

        GenY = array("d", [0])
        out_tree.Branch('GenY', GenY, 'GenY/D')

        GenZ = array("d", [0])
        out_tree.Branch('GenZ', GenZ, 'GenZ/D')

        NOP = array("I", [0])
        out_tree.Branch('NOP', NOP, 'NOP/i')

        NOPactive = array("I", [0])
        out_tree.Branch('NOPactive', NOPactive, 'NOPactive/i')

        NPE = array("d", [0])
        out_tree.Branch('NPE', NPE, 'NPE/D')

        NPEactive = array("d", [0])
        out_tree.Branch('NPEactive', NPEactive, 'NPEactive/D')

        noise_val = array("d", [0]*n_channels)
        out_tree.Branch('noise', noise_val, 'noise[%i]/D' % n_channels)

    else:
        pmt_chi2 = array("d", [0.0])
        out_tree.Branch('pmt_chi2', pmt_chi2, 'pmt_chi2/D')

    file_start_time = array('I', [0]) # unsigned int
    file_start_time[0] = posix_start_time
    out_tree.Branch('file_start_time', file_start_time, 'file_start_time/i')
    run_tree.Branch('file_start_time', file_start_time, 'file_start_time/i')

    sampling_frequency_Hz = array('d', [0]) # double
    out_tree.Branch('sampling_freq_Hz', sampling_frequency_Hz, 'sampling_freq_Hz/D')
    sampling_frequency_Hz[0] = sampling_freq_Hz
    if isNGM:
        sys_config = root_file.Get("NGMSystemConfiguration")
        card = sys_config.GetSlotParameters().GetParValueO("card",0)
        sampling_frequency_Hz[0] = struck_analysis_parameters.get_clock_frequency_Hz_ngm(card.clock_source_choice)
        sampling_freq_Hz = sampling_frequency_Hz[0]
        print "sampling frequency [MHz]:", sampling_frequency_Hz[0]/1e6

    #Time stamp in clock ticks (conversion factor is the sampling frequency)
    time_stamp = array('L', [0]) # timestamp for each event, unsigned long
    out_tree.Branch('time_stamp', time_stamp, 'time_stamp/l')
    time_stampDouble = array('d', [0]) # double
    out_tree.Branch('time_stampDouble', time_stampDouble, 'time_stampDouble/D')

    if isNGM: # keep time stamp info for individual channels
        time_stamp_diff = array('l', [0]*n_channels) # timestamp for each event, unsigned long
        out_tree.Branch('time_stamp_diff', time_stamp_diff, 'time_stamp_diff[%i]/L' % n_channels)

        time_stampDouble_diff = array('d', [0]*n_channels) # double
        out_tree.Branch('time_stampDouble_diff', time_stampDouble_diff, 'time_stampDouble_diff[%i]/D' % n_channels)

        time_stamp_msec = array('d', [0]) # double
        out_tree.Branch('time_stamp_msec', time_stamp_msec, 'time_stamp_msec/D')

        time_stamp_diff_msec = array('d', [0]*n_channels) # timestamp for each event, unsigned long
        out_tree.Branch('time_stamp_diff_msec', time_stamp_diff_msec, 'time_stamp_diff_msec[%i]/D' % n_channels)

    time_since_last = array('d', [0]) # double
    out_tree.Branch('time_since_last', time_since_last, 'time_since_last/D')

    time_since_last_msec = array('d', [0]) # double
    out_tree.Branch('time_since_last_msec', time_since_last_msec, 'time_since_last_msec/D')

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
    elif isMC:
        #MC so this doesn't exist
        run_time[0] = 0
    elif isNGM:
        run_time[0] = (tree.GetMaximum("_rawclock") -
            tree.GetMinimum("_rawclock"))/sampling_freq_Hz
    else:
        run_time[0] = (tree.GetMaximum("time_stampDouble") -
            tree.GetMinimum("time_stampDouble"))/sampling_freq_Hz
    print "run duration: %.2f seconds" % run_time[0]

    channel = array('I', [0]*n_channels_in_event) # unsigned int
    out_tree.Branch('channel', channel, 'channel[%i]/i' % n_channels_in_event)
    
    nfound_channels = array('I', [0])
    out_tree.Branch('nfound_channels', nfound_channels, 'nfound_channels/i') #Total # of found channels. For accounting for dead or bad channels

    trigger_time = array('d', [0.0]) # double
    out_tree.Branch('trigger_time', trigger_time, 'trigger_time/D')
    run_tree.Branch('trigger_time', trigger_time, 'trigger_time/D')

    # estimate trigger time, in microseconds
    if isMC:
        #MC this is also hardcoded into nEXO_Analysis
        #trigger_time[0] = 200/sampling_freq_Hz*1e6
        trigger_time[0] = 275/sampling_freq_Hz*1e6 # run 11+

    elif isNGM:
        ngm_config = root_file.Get("NGMSystemConfiguration")
        card = sys_config.GetSlotParameters().GetParValueO("card",0)
        trigger_time[0] = card.pretriggerdelay_block[0]/sampling_freq_Hz*1e6 
        gate_window_length_block = card.gate_window_length_block[0]
        pmt_hist = None
        if trigger_time[0] == 11.0:
            import pmt_reference_signal_11th_LXe
            pmt_hist = pmt_reference_signal_11th_LXe.hist
            print "using PMT reference signal from 11th LXe"
        elif trigger_time[0] == 8.0:
            import pmt_reference_signal
            pmt_hist = pmt_reference_signal.hist
            print "using PMT reference signal from 9th LXe"
        else:
            print "WARNING: no pmt reference signal found for trigger_time of %i!!" % trigger_time[0]

        print "NGM trigger_time [microseconds]:", trigger_time[0]
    elif do_debug:
        print "--> debugging -- skipping trigger_time calc"
    else:
        trigger_hist = ROOT.TH1D("trigger_hist","",5000,0,5000)
        selection = "channel==%i && wfm_max - wfm%i[0] > 20" % (pmt_channel, pmt_channel)
        if is_tier1:
            selection = "channel==%i && wfm_max - wfm[0] > 20" % pmt_channel

        n_trigger_entries = 0
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

        if trigger_time[0] < 0.4:
            "--> forcing trigger time to 200 samples = 8 microseconds (ok for 5th LXe)"
            trigger_time[0] = 200/sampling_freq_Hz*1e6

    # store some processing parameters:
    n_baseline_samples = array('I', [0]) # double
    out_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')
    run_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')
    n_baseline_samples[0] = int(baseline_average_time_microseconds*sampling_freq_Hz/1e6)
    print "n_baseline_samples:", n_baseline_samples[0]
    baseline_remover = EXOBaselineRemover()
    baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])

    trap_filter = EXOTrapezoidalFilter()
    trap_filter.SetFlatTime(0.0)

    decay_time = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('decay_time', decay_time, 'decay_time[%i]/D' % n_channels_in_event)

    decay_time_values = struck_analysis_parameters.decay_time_values
    decay_time_values[pmt_channel] = 1e9*microsecond
    
    if isMC:
        #No decay in MC so set to infinite
        decay_time_values = [1e9*microsecond]*n_channels


    for (i, i_channel) in enumerate(channels):
        try:
            decay_time[i] = decay_time_values[i_channel]
        except KeyError:
            print "no decay info for channel %i" % i_channel
            decay_time[i] = 1e9*microsecond


    # energy calibration, keV:
    calibration = array('d', [0.0]*n_channels_in_event) # double
    out_tree.Branch('calibration', calibration, 'calibration[%i]/D' % n_channels_in_event)


    rise_time_stop10 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop10', rise_time_stop10, 'rise_time_stop10[%i]/D' % n_channels_in_event)

    rise_time_stop20 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop20', rise_time_stop20, 'rise_time_stop20[%i]/D' % n_channels_in_event)

    rise_time_stop30 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop30', rise_time_stop30, 'rise_time_stop30[%i]/D' % n_channels_in_event)

    rise_time_stop40 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop40', rise_time_stop40, 'rise_time_stop40[%i]/D' % n_channels_in_event)

    rise_time_stop50 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop50', rise_time_stop50, 'rise_time_stop50[%i]/D' % n_channels_in_event)

    rise_time_stop60 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop60', rise_time_stop60, 'rise_time_stop60[%i]/D' % n_channels_in_event)

    rise_time_stop70 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop70', rise_time_stop70, 'rise_time_stop70[%i]/D' % n_channels_in_event)

    rise_time_stop80 = array('d', [0]*n_channels_in_event) # double
    if not skip_short_risetimes:
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

    wfm_min_time = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('wfm_min_time', wfm_min_time, 'wfm_min_time[%i]/D' % n_channels_in_event)

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

    
    # info for saving the WFMs if we are making a noise library
    noisewfm = None
    if isMakeNoise:
        # Not sure you can do double arrays in a TTree Branch in pyROOT without making a C++ struct
        # Instead make one branch per WFM called wfm%i
        noisewfm = []
        for ichannel in channels:
            noisewfm.append(array('d', [0]*noise_length))
            out_tree.Branch('wfm%i' % ichannel, noisewfm[ichannel], 'wfm%i[%i]/D' % (ichannel, noise_length))

    #--------------------------------------Info For Multiplicity-------------------------------------
    #--------------------------------------and Signal holding----------------------------------------
    #Reocrd the channels which appear above the RMS noise threshold
    signal_threshold = array('d', [0])
    out_tree.Branch('signal_threshold', signal_threshold, 'signal_threshold/D')
    run_tree.Branch('signal_threshold', signal_threshold, 'signal_threshold/D')
    signal_threshold[0] = struck_analysis_parameters.rms_threshold

    signal_map = array('I', [0]*n_channels) 
    out_tree.Branch('signal_map', signal_map, 'signal_map[%i]/i' % n_channels_in_event) 
    
    nsignals = array('I', [0])
    out_tree.Branch('nsignals', nsignals, 'nsignals/i') #Total Signals above threshold

    nXsignals = array('I', [0])
    out_tree.Branch('nXsignals', nXsignals, 'nXsignals/i') #Total XSignals above threshold
    
    nYsignals = array('I', [0])
    out_tree.Branch('nYsignals', nYsignals, 'nYsignals/i') #Total YSignals above thresholdY
    
    SignalEnergy = array('d', [0])
    out_tree.Branch('SignalEnergy', SignalEnergy, 'SignalEnergy/D') #Sum Energy of Signals

    SignalEnergyX = array('d', [0])
    out_tree.Branch('SignalEnergyX', SignalEnergyX, 'SignalEnergyX/D') #Sum Energy of XSignals

    SignalEnergyY = array('d', [0])
    out_tree.Branch('SignalEnergyY', SignalEnergyY, 'SignalEnergyY/D') #Sum Energy of YSignals
    
    #Store the assosiated bundle of adjacent wires 
    #Map each bundle to set of channels
    signal_bundle_map = array('I', [0]*n_channels)
    out_tree.Branch('signal_bundle_map', signal_bundle_map, 'signal_bundle_map[%i]/i' % n_channels_in_event)
    
    nbundles = array('I', [0])
    out_tree.Branch('nbundles', nbundles, 'nbundles/i')
    
    nbundlesX = array('I', [0])
    out_tree.Branch('nbundlesX', nbundlesX, 'nbundlesX/i')

    nbundlesY = array('I', [0])
    out_tree.Branch('nbundlesY', nbundlesY, 'nbundlesY/i')

    #The most bundles ever is just 1 per channel
    bundle_type = array('I', [0]*n_channels)
    out_tree.Branch('bundle_type', bundle_type, 'bundle_type[nbundles]/i')

    bundle_energy = array('d', [0]*n_channels)
    out_tree.Branch('bundle_energy', bundle_energy, 'bundle_energy[nbundles]/D')
    
    bundle_nsigs = array('I', [0]*n_channels)
    out_tree.Branch('bundle_nsigs', bundle_nsigs, 'bundle_nsigs[nbundles]/i')
    #------------------------------------------------------------------------------------------------
    #------------------------------------------------------------------------------------------------
    #------------------------------------------------------------------------------------------------

    nsignal_strips = array('I', [0])
    out_tree.Branch('nsignal_strips', nsignal_strips, 'nsignal_strips/i') #Total Signals above threshold

    n_strips = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('n_strips', n_strips, 'n_strips[%i]/i' % n_channels)
    for ch, strips in struck_analysis_parameters.struck_to_mc_channel_map.items():
        try:
            n_strips[ch] = len(strips)
        except:
            print "n_strips calc failed for channel %i" % ch

    is_pulser = array('I', [0])
    out_tree.Branch('is_pulser', is_pulser, 'is_pulser/i')

    # parameters coming from sum waveform
    rise_time_stop10_sum = array('d', [0.0]) # double
    out_tree.Branch('rise_time_stop10_sum', rise_time_stop10_sum, 'rise_time_stop10_sum/D')

    rise_time_stop20_sum = array('d', [0.0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop20_sum', rise_time_stop20_sum, 'rise_time_stop20_sum/D')

    rise_time_stop30_sum = array('d', [0.0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop30_sum', rise_time_stop30_sum, 'rise_time_stop30_sum/D')

    rise_time_stop40_sum = array('d', [0.0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop40_sum', rise_time_stop40_sum, 'rise_time_stop40_sum/D')

    rise_time_stop50_sum = array('d', [0.0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop50_sum', rise_time_stop50_sum, 'rise_time_stop50_sum/D')

    rise_time_stop60_sum = array('d', [0.0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop60_sum', rise_time_stop60_sum, 'rise_time_stop60_sum/D')

    rise_time_stop70_sum = array('d', [0.0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop70_sum', rise_time_stop70_sum, 'rise_time_stop70_sum/D')

    rise_time_stop80_sum = array('d', [0.0]) # double
    if not skip_short_risetimes:
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

    maxCurrent = array('d', [0.0])
    out_tree.Branch('maxCurrent', maxCurrent, 'maxCurrent/D')
    maxCurrent1 = array('d', [0.0])
    out_tree.Branch('maxCurrent1', maxCurrent1, 'maxCurrent1/D')
    maxCurrent2 = array('d', [0.0])
    out_tree.Branch('maxCurrent2', maxCurrent2, 'maxCurrent2/D')
    maxCurrent3 = array('d', [0.0])
    out_tree.Branch('maxCurrent3', maxCurrent3, 'maxCurrent3/D')
    maxCurrent4 = array('d', [0.0])
    out_tree.Branch('maxCurrent4', maxCurrent4, 'maxCurrent4/D')

    #Store the total energy on all MC channels even ones that 
    #Are missing in real life
    #MCenergy_sum = array('d', [0.0])
    #out_tree.Branch('MCenergy_sum', MCenergy_sum, 'MCenergy_sum/D')

    energy_rms_sum = array('d', [0.0])
    out_tree.Branch('energy_rms_sum', energy_rms_sum, 'energy_rms_sum/D')
    
    #Sipm Specific Things
    baseline_rms_filter = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('baseline_rms_filter', baseline_rms_filter, 'baseline_rms_filter[%i]/D' % n_channels_in_event)

    sipm_max      = array('d', [0]*n_channels_in_event)
    out_tree.Branch('sipm_max', sipm_max, 'sipm_max[%i]/D' % n_channels_in_event)
    
    sipm_max_time = array('d', [0]*n_channels_in_event) #in us
    out_tree.Branch('sipm_max_time', sipm_max_time, 'sipm_max_time[%i]/D' % n_channels_in_event)
    
    sipm_min      = array('d', [0]*n_channels_in_event)
    out_tree.Branch('sipm_min', sipm_min, 'sipm_min[%i]/D' % n_channels_in_event)
            
    sipm_min_time = array('d', [0]*n_channels_in_event) #in us
    out_tree.Branch('sipm_min_time', sipm_min_time, 'sipm_min_time[%i]/D' % n_channels_in_event)
    
    SignalEnergyLight = array('d', [0])
    out_tree.Branch('SignalEnergyLight', SignalEnergyLight, 'SignalEnergyLight/D')
    #End Sipm shit

    # make a hist for calculating some averages
    hist = ROOT.TH1D("hist","",100, 0, pow(2,14))
    print "calculating mean baseline & baseline RMS for each channel in this file..."
    if isMC: 
        print "\t skipping MC for now..."
    elif isMakeNoise: 
        print "\t skipping for isMakeNoise"
    elif isNGM:
        print "\t skipping NGM for now..."
    else: 
        for (i, i_channel) in enumerate(channels):
            print "%i: ch %i" % (i, i_channel)
            
            #if True:
            if do_debug: 
                print "\t skipping for debugging"
                continue
                
            # calculate avg baseline:
            draw_command = "wfm >> hist"
            selection = "Iteration$<%i && channel==%i" % (n_baseline_samples[0], i_channel)
            if not is_tier1:
                draw_command = "wfm%i >> hist" % i_channel
            if isMC:
                #Command that worked
                #evtTree->Draw("ChannelWaveform[12]:Iteration$","Entry$==10 && Iteration$<300")
                draw_command = "ChannelWaveform[%i] >> hist" % (i_channel)
                selection = "Iteration$<%i" % (n_baseline_samples[0])
            if isNGM:
                draw_command = "_waveform >> hist"
                selection = "Iteration$<%i && _channel==%i && _slot==%i" % (n_baseline_samples[0], i_channel%16, i_channel/16)
            n_drawn = tree.Draw(
                draw_command,
                selection,
                "goff"
            )
            baseline_mean_file[i] = hist.GetMean()
            print "\t draw command: %s | selection: %s | n_drawn: %.2e" % (draw_command, selection, n_drawn)
            print "\t file baseline mean:", baseline_mean_file[i]

            # calculate baseline RMS:
            # this is an appxorimation -- we can't calculate the real RMS until we
            # know the baseline average for each wfm -- it would be better to do
            # this in the loop over events
            draw_command = "wfm-wfm[0] >> hist"
            if not is_tier1:
                draw_command = "wfm%i-wfm%i[0] >> hist" % (i_channel, i_channel)
            if isMC:
                #evtTree->Draw("(ChannelWaveform[12] - ChannelWaveform[12][300]):Iteration$",
                #                "Entry$==10 && Iteration$<300")
                draw_command = "(ChannelWaveform[%i] - ChannelWaveform[%i][0]):Iteration$" % (i_channel, i_channel)
            if isNGM:
                draw_command = "_waveform-_waveform[0] >> hist"
            n_drawn = tree.Draw(
                draw_command,
                selection,
                "goff"
            )
            baseline_rms_file[i] = hist.GetRMS()
            print "\t draw command: %s | selection: %s | n_drawn: %.2e" % (draw_command, selection,n_drawn)
            print "\t file baseline rms:", baseline_rms_file[i]

        print "\t done"

    # decide whether 2V input was used for the digitizer or not. The
    # file-averaged baseline mean for channel 0 seems like a good indicator of
    # this -- we should also figure out if any channels are shaped...

    calibration_values = struck_analysis_parameters.calibration_values
    data_calib = None
    if isMC:
        data_calib = copy.copy(struck_analysis_parameters.calibration_values)
        print "Test calib", data_calib[7]
        for n in np.arange(n_channels):
            #MC is given in number of e- so need to multiply by Wvalue to get eV
            #Need factor of 1e-3 to get keV
            calibration_values[int(n)] = struck_analysis_parameters.Wvalue*1e-3
        print "Test calib", data_calib[7]

    print "choosing calibration values..."
    for (i, i_channel) in enumerate(channels):

        try:
            original_calibration = calibration_values[i_channel]
        except KeyError:
            print "\t no calibration data for ch %i" % i_channel
            continue

        is_2Vinput[i] = struck_analysis_parameters.is_2Vinput(baseline_mean_file[i])
        if isMC:
            is_2Vinput[i] = False
        if isNGM:
            slot = 0
            if i_channel > 15: slot = 1
            card = sys_config.GetSlotParameters().GetParValueO("card",slot)
            gain = card.gain[i_channel-16*slot]
            voltage_range_mV = struck_analysis_parameters.get_voltage_range_mV_ngm(gain)
            is_2Vinput[i] = 1
            if voltage_range_mV == 5000.0:
                is_2Vinput[i] = 0
        elif is_2Vinput[i]: # don't do this for NGM -- seems like we treated is_2V differently in the past
            print "channel %i" % i_channel
            print "\t channel %i used 2V input range" % i_channel
            print "\t dividing calibration by 2.5"
            calibration_values[i_channel] /= 2.5

        # this doesn't seem very reliable
        #is_amplified[i] = struck_analysis_parameters.is_amplified(
        #    baseline_mean_file[i], baseline_rms_file[i])

        if is_amplified[i] == 0 and not isMC:
            if i_channel != pmt_channel:
                print "channel %i" % i_channel
                calibration_values[i_channel] *= 4.0
                print "\t multiplying calibration by 4"
                print "\t channel %i is unamplified" % i_channel
        if original_calibration != calibration_values[i_channel]:
            print "\t original calibration value %.4e" % calibration_values[i_channel]
            print "channel %i" % i_channel
            print "\t channel %i calibration: %.4e" % (i_channel, calibration_values[i_channel])
    print "\t done"
    
    for (i, i_channel) in enumerate(channels):
        calibration[i] = calibration_values[i_channel]

    # PMT threshold
    pmt_threshold = array('d', [0]) # double
    out_tree.Branch('pmt_threshold', pmt_threshold, 'pmt_threshold/D')
    run_tree.Branch('pmt_threshold', pmt_threshold, 'pmt_threshold/D')

    # calculate PMT threshold...
    #PMT doesn't exist in MC so skip if MC
    if isMC:
        pmt_threshold[0] = 0.0
    elif do_debug:
        print "--> debugging -- skipping PMT threshold calc"
    elif pulser_channel != None:
        print "skipping PMT threshold calc since pulser is channel %i" % pulser_channel
    elif pmt_channel == None:
        print "skipping PMT threshold calc since this is a SiPM run"
    else:
        draw_command = "wfm_max-wfm[0] >> hist"
        selection = "channel==%i" % pmt_channel
            
        if not is_tier1:
            draw_command = "wfm_max-wfm%i[0] >> hist" % pmt_channel
        if isNGM:
            draw_command = "Max$(_waveform)-_waveform[0] >> hist"
            selection = "_slot==%i && _channel==%i" % (pmt_channel/16, pmt_channel%16)

        tree.Draw(draw_command,selection,"goff")
        pmt_threshold[0] = hist.GetBinLowEdge(hist.FindFirstBinAbove(0))*calibration_values[pmt_channel]
        print "pmt threshold calc | draw_cmd: %s | selection: %s" % (draw_command, selection)
        print "pmt_threshold:", pmt_threshold[0]
        print "pmt_threshold hist mean, rms:", hist.GetMean(), hist.GetRMS()

    # energy & rms before any processing
    energy = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy', energy, 'energy[%i]/D' % n_channels_in_event)
    energy_rms = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('energy_rms', energy_rms, 'energy_rms[%i]/D' % n_channels_in_event)

    chargeEnergy = array('d', [0.0]) # double
    out_tree.Branch('chargeEnergy', chargeEnergy, 'chargeEnergy/D')
 
    lightEnergy = array('d', [0.0]) # double
    out_tree.Branch('lightEnergy', lightEnergy, 'lightEnergy/D')

    if isMC:
        #Total Energy in MC for all channels including not active channels
        MCchargeEnergy = array('d', [0.0])
        out_tree.Branch('MCchargeEnergy', MCchargeEnergy, 'MCchargeEnergy/D')

        # energy in active LXe:
        MCtotalEventEnergy = array('d',[0.0])
        out_tree.Branch("MCtotalEventEnergy",MCtotalEventEnergy,"MCtotalEventEnergy/D")

        # energy in all LXe:
        MCtotalEventLXeEnergy = array('d',[0.0])
        out_tree.Branch("MCtotalEventLXeEnergy",MCtotalEventLXeEnergy,"MCtotalEventLXeEnergy/D")

        # energy NEST processed:
        MCnestEventEnergy = array('d',[0.0])
        out_tree.Branch("MCnestEventEnergy",MCnestEventEnergy,"MCnestEventEnergy/D")

        MCEventNumber = array('i', [0]) # signed int
        out_tree.Branch('MCEventNumber', MCEventNumber, 'MCEventNumber/I')

        MCtrueEnergy = array('d', [0]*n_channels_in_event) # double
        out_tree.Branch('MCtrueEnergy', MCtrueEnergy, 'MCtrueEnergy[%i]/D' % n_channels_in_event)

        NumPCDs = array('i', [0]) # signed int
        out_tree.Branch('NumPCDs', NumPCDs, 'NumPCDs/I')
        max_n_PCDs = 300

        # PCDx:
        PCDx = array('d',[0.0]*max_n_PCDs)
        out_tree.Branch("PCDx",PCDx,"PCDx[NumPCDs]/D")

        # PCDy:
        PCDy = array('d',[0.0]*max_n_PCDs)
        out_tree.Branch("PCDy",PCDy,"PCDy[NumPCDs]/D")

        # PCDz:
        PCDz = array('d',[0.0]*max_n_PCDs)
        out_tree.Branch("PCDz",PCDz,"PCDz[NumPCDs]/D")

        # PCDq:
        PCDq = array('d',[0.0]*max_n_PCDs)
        out_tree.Branch("PCDq",PCDq,"PCDq[NumPCDs]/D")

        NumTE = array('i', [0]) # signed int
        out_tree.Branch('NumTE', NumTE, 'NumTE/I')

        NPrimaries = array('i', [0]) # signed int
        out_tree.Branch('NPrimaries', NPrimaries, 'NPrimaries/I')

        PdgCode = array('d', [0.0]*200) # double
        out_tree.Branch('PdgCode', PdgCode, 'PdgCode[NPrimaries]/D')

        KineticEnergy = array('d', [0.0]*200) # double
        out_tree.Branch('KineticEnergy', KineticEnergy, 'KineticEnergy[NPrimaries]/D')

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

    # slopes
    energy1_pz_slope = array('d', [0]*n_channels_in_event) # double, calibrated
    out_tree.Branch('energy1_pz_slope', energy1_pz_slope, 'energy1_pz_slope[%i]/D' % n_channels_in_event)
    baseline_slope = array('d', [0]*n_channels_in_event) # double, uncalibrated
    out_tree.Branch('baseline_slope', baseline_slope, 'baseline_slope[%i]/D' % n_channels_in_event)
    
    #matched filter and derivitive filter
    dfilter_max = array('d', [0]*n_channels_in_event)
    out_tree.Branch('dfilter_max', dfilter_max, 'dfilter_max[%i]/D' % n_channels_in_event)
    dfilter_time = array('d', [0]*n_channels_in_event)
    out_tree.Branch('dfilter_time', dfilter_time, 'dfilter_time[%i]/D' % n_channels_in_event)

    mfilter_max = array('d', [0]*n_channels_in_event)
    out_tree.Branch('mfilter_max', mfilter_max, 'mfilter_max[%i]/D' % n_channels_in_event)
    mfilter_time = array('d', [0]*n_channels_in_event)
    out_tree.Branch('mfilter_time', mfilter_time, 'mfilter_time[%i]/D' % n_channels_in_event)

    

    #Decay Constat Fit in WFM Processing
    decay_fit = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('decay_fit', decay_fit, 'decay_fit[%i]/D' % n_channels_in_event)
    decay_error = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('decay_error', decay_error, 'decay_error[%i]/D' % n_channels_in_event)
    decay_chi2 = array('d', [0]*n_channels_in_event) # double, this is the reduced chi^2
    out_tree.Branch('decay_chi2', decay_chi2, 'decay_chi2[%i]/D' % n_channels_in_event)

    fname = TObjString(os.path.abspath(filename))
    out_tree.Branch("filename",fname)
    run_tree.Branch("filename",fname)

    if do_debug:
        reporting_period = 1

    run_tree.Fill() # this tree only has one entry with run-level entries

    n_events = 0
    
    if isNGM:
        n_channels_in_this_event = 0

    # loop over all entries in tree
    i_entry = 0
    n_channels_in_this_event = 0
    while i_entry < n_entries:
    #while i_entry < 1000:
        tree.GetEntry(i_entry)
        #if isNGM and i_entry > 1e6: 
        #    print "<<<< DEBUGGING >>>>"
        #    break # debugging

        #For MC get a random entry in the noise tree if it exists
        if isMC and noise_file is not None:
            rndm_entry = int(generator.Rndm()*noise_tree.GetEntries())
            noise_tree.GetEntry(rndm_entry)

        # print periodic output message
        if i_entry % reporting_period == 0:
            now = time.time()
            print "----> entry %i of %i: %.2f percent done in %.1f seconds | %i entries in %.1f seconds (%.2f Hz)" % (
                i_entry, 
                n_entries, 
                100.0*i_entry/n_entries, 
                now - start_time,
                reporting_period,
                now - last_time, 
                reporting_period/(now-last_time),
            )
            last_time = now

        # set event-level output tree variables
        if isMC:
            #Event number
            event[0] = tree.EventNumber
            sub_event[0] = tree.SubEventNumber
            GenX[0] = tree.GenX
            GenY[0] = tree.GenY
            GenZ[0] = tree.GenZ

        elif isNGM:
            event[0] = n_events
        else:
            event[0] = tree.event

        if is_tier1:
            time_stamp[0] = tree.timestamp
            time_stampDouble[0] = tree.timestampDouble
        elif isMC:
            #No timestamp in MC 
            time_stamp[0] = int( tree.EventTime/sampling_freq_Hz ) 
            time_stampDouble[0] = tree.EventTime/sampling_freq_Hz
        elif isNGM:
            time_stamp[0] = int( tree.HitTree.GetRawClock() ) 
            time_stampDouble[0] = tree.HitTree.GetRawClock()
            #above are clock ticks. but also save a version in mili-seconds
            time_stamp_msec[0]  = (tree.HitTree.GetRawClock()/(sampling_freq_Hz))*1.e3
            n_channels_in_this_event = 0
        else:
            time_stamp[0] = tree.time_stamp
            time_stampDouble[0] = tree.time_stampDouble

        # calculate time since previous event
        if prev_time_stamp > 0:
            time_since_last[0] = time_stampDouble[0] - prev_time_stamp
            time_since_last_msec[0] = (time_stampDouble[0] - prev_time_stamp)*1.e3/sampling_freq_Hz
        else:
            time_since_last[0] = -1.0
            time_since_last_msec[0] = -1.0
        prev_time_stamp = time_stampDouble[0]
        if isMC: prev_time_stamp = 0

        #---------------------------INIT--------------------------
        # initialize things which track sums
        chargeEnergy[0] = 0.0
        lightEnergy[0] = 0.0
        nsignals[0] = 0
        nsignal_strips[0] = 0
        nXsignals[0] = 0
        nYsignals[0] = 0
        SignalEnergy[0] = 0.0
        SignalEnergyLight[0] = 0.0
        SignalEnergyX[0] = 0.0
        SignalEnergyY[0] = 0.0 
        for bundle_index in xrange(nbundles[0]):
            bundle_type[bundle_index] = 0
            bundle_nsigs[bundle_index] = 0
            bundle_energy[bundle_index] = 0.0
        for ch_index in xrange(n_channels_in_event):
            energy[ch_index] = 0
        nbundles[0] = 0
        nfound_channels[0] = 0
        is_pulser[0] = 0
        is_bad[0] = 0
        found_dead = False
        found_channels = []

        if isMC:
            MCchargeEnergy[0] = 0.0
            MCtotalEventEnergy[0] = tree.Energy
            MCtotalEventLXeEnergy[0] = tree.TotalEventLXeEnergy
            MCnestEventEnergy[0] = tree.NestEventEnergy
            MCEventNumber[0] = tree.EventNumber
            NumTE[0] = tree.NumTE
            # check for backwards compatibility...
            try:
                NOP[0] = tree.NOP
                NOPactive[0] = tree.NOPactive
                NPE[0] = tree.NPE
                NPEactive[0] = tree.NPEactive
            except AttributeError:
                pass

            NPrimaries[0] = tree.NPrimaries
            for i_primary in xrange(tree.NPrimaries):
                PdgCode[i_primary] = tree.PdgCode[i_primary]
                KineticEnergy[i_primary] = tree.KineticEnergy[i_primary]
            NumPCDs[0] = tree.NumPCDs
            #print NumPCDs[0]
            if NumPCDs[0] > max_n_PCDs:
                print "WARNING: %i PCDs and only space for %i" % (tree.NumPCDs, max_n_PCDs)
                NumPCDs[0] = max_n_PCDs
            for i_pcd in xrange(NumPCDs[0]):
                #print i_pcd
                PCDx[i_pcd] = tree.PCDx[i_pcd]
                PCDy[i_pcd] = tree.PCDy[i_pcd]
                PCDz[i_pcd] = tree.PCDz[i_pcd]
                PCDq[i_pcd] = tree.PCDq[i_pcd]

        else:
            pmt_chi2[0] = 0.0
        sum_wfm = None
        for i in xrange(n_channels_in_event):

            if is_tier1:
                wfm = tree.wfm
                channel[i] = tree.channel
            elif isMC:

                #Some channels are grouped together so for those sum each channel in the gropu
                #First always get the one channel that has to exist
                if i == pmt_channel or i == pulser_channel: 
                    #print "Skip pmt", i, pmt_channel
                    continue

                #print i, pmt_channel
                wfm = [wfmp for wfmp in tree.ChannelWaveform[struck_to_mc_channel_map[i][0]]]
                if not ROOT.gROOT.IsBatch(): print "channel %i %s -- adding MC ch %s" % (
                    i, 
                    channel_map[i],
                    struck_to_mc_channel_map[i][0],
                )
                
                #Now check if a multi strip and if it is loop over the channels and add
                #their wfms to the sum wfm
                if len(struck_to_mc_channel_map[i]) > 1.5:
                    for mcch in struck_to_mc_channel_map[i][1:]:
                        #print "MC=", i, mcch
                        if not ROOT.gROOT.IsBatch(): print "channel %i %s-- adding MC ch %s" % (
                            i, 
                            channel_map[i],
                            struck_to_mc_channel_map[i][0],
                        )
                        for index, wfmi in enumerate(tree.ChannelWaveform[mcch]):
                            wfm[index] += wfmi

                MCtrueEnergy[i] = wfm[-1]*calibration[i] # set true energy to last value of wfm
                channel[i] = i

            elif isNGM:
                if n_channels_in_this_event > 0: # For NGM, each wfm is its own tree entry
                    i_entry += 1
                    tree.GetEntry(i_entry)

                i = tree.HitTree.GetSlot()*16 + tree.HitTree.GetChannel()

                channel[i] = tree.HitTree.GetSlot()*16 + tree.HitTree.GetChannel()
                #First time stamp diff in clock ticks thans convert to ms 
                time_stamp_diff[i] = int( tree.HitTree.GetRawClock() ) - time_stamp[0]# time stamp for this channel
                time_stampDouble_diff[i] = tree.HitTree.GetRawClock() -time_stampDouble[0] # time stamp for this channel
                time_stamp_diff_msec[i] = ((tree.HitTree.GetRawClock() -time_stampDouble[0])/sampling_freq_Hz)*1.e3 #save in msec too

                if do_debug: # debugging
                #if True:
                    print "NGM event", n_events, \
                        "i", i, \
                        "channel", channel[i], \
                        "time stamp", tree.HitTree.GetRawClock(), \
                        "event_time_stamp:", time_stamp[0], \
                        "time diff:", tree.HitTree.GetRawClock() - time_stamp[0]

                # allowable number of clock ticks of difference: 80 ns 
                clock_tick_diff = sampling_frequency_Hz[0]*80.0/1e9
                if (abs( tree.HitTree.GetRawClock() - time_stamp[0] ) > clock_tick_diff):
                    #print ""
                    #print "===> end of event after %i channels: %i clock tick diff" % (
                    #    (n_channels_in_this_event),
                    #    abs( tree.HitTree.GetRawClock() - time_stamp[0] ),
                    #)
                    #print ""
                    i_entry -= 1
                    #n_events += 1
                    break # break from loop over events
                
                n_channels_in_this_event += 1
                if channel[i] in found_channels:
                    print ""
                    print "======> Found Duplicate Channel %i at entry %i.  Should this even be possible????" % (channel[i],i_entry)
                    print "This is entry %i out of %i entries." % (i_entry, n_entries)
                    print found_channels
                    print ""
                    sys.exit(1)

                found_channels.append(channel[i])

                if dead_channels[channel[i]] > 0:
                    found_dead = True
                    print ""
                    print "===> DEAD Channel Found: %i" % channel[i]
                    print ""
                    break

                wfm = tree._waveform
                
                if isMakeNoise:
                    for wfm_index in xrange(noise_length):
                        noisewfm[i][wfm_index] = wfm[wfm_index]

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

            # add noise to MC
            if isMC and channel[i] is not pmt_channel:
                if noise_file is None:
                    #No file use gaussian noise
                    if not ROOT.gROOT.IsBatch(): print "no noise file, using gaussian noise"
                    try:
                        sigma = rms_keV[i]/calibration[i] 
                    except KeyError:
                        sigma = rms_keV[0]/calibration[i] # MC can have more channels than data
                    for i_point in xrange(len(wfm)):
                        noise = generator.Gaus()*sigma
                        wfm[i_point]+=noise
                else:
                    if not ROOT.gROOT.IsBatch(): print "noise file found"
                    #Have a noise_file get random event and wfm for that channel
                    noise_array = getattr(noise_tree, "wfm%i" % channel[i])
                    #MC length is 801 why?????

                    #for i_point in xrange(len(wfm)):
                    for i_point in xrange(len(noise_array)):
                        #print data_calib applies to the noise in data which is ADC units
                        #convert to keV using current calib for data
                        #than convert to #electrons with Wvalue in calibration for MC
                        #print "Calib ratio", data_calib[i], calibration[i]
                        wfm[i_point] += (noise_array[i_point]*data_calib[i])/calibration[i]

                noise_val[i] = generator.Gaus() # an extra noise value for use with energy smearing

            exo_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[i])

            wfm_max[i] = exo_wfm.GetMaxValue()
            wfm_min[i] = exo_wfm.GetMinValue()

            if do_debug:
                # a copy of the un-transformed wfm, for debugging
                copy_wfm = EXODoubleWaveform(exo_wfm)

            
            label = "Event %i " % n_events
            if isMC:
                label += " MC ch %i " % i 
            label += struck_analysis_parameters.channel_map[i]
            # use wfmProcessing to get most wfm parameters
            (
                baseline_mean[i], 
                baseline_rms[i], 
                energy[i], 
                energy_rms[i], 
                energy1[i], 
                energy_rms1[i],
                energy_pz[i], 
                energy_rms_pz[i], 
                energy1_pz[i], 
                energy_rms1_pz[i],
                calibrated_wfm,
                wfm_max[i],
                wfm_min[i],
                decay_fit[i],
                decay_error[i],
                decay_chi2[i],
                signal_map[i],
                dfilter_max[i],
                dfilter_time[i],
                mfilter_max[i],
                mfilter_time[i],
                baseline_slope[i],
                energy1_pz_slope[i],
                baseline_rms_filter[i],
                sipm_max[i],
                sipm_min[i],
                sipm_max_time[i],
                sipm_min_time[i]
            ) = wfmProcessing.get_wfmparams(
                exo_wfm=exo_wfm, 
                wfm_length=wfm_length[i], 
                sampling_freq_Hz=sampling_freq_Hz,
                n_baseline_samples=n_baseline_samples[0], 
                calibration=calibration[i], 
                decay_time=decay_time[i], 
                is_pmtchannel=channel[i]==pmt_channel,
                is_sipmchannel=(sipm_channels_to_use[channel[i]] > 0),
                channel=channel[i],
                isMC=isMC,
                label=label,
            )


            #print "Using Decay Time %f for chan %i" % (decay_time[i], i)
            
            if charge_channels_to_use[channel[i]] and signal_map[i] > 0.5:
                #This is a signal so add to total and figure out the type
                #Record Energy in  new variable which tracks total energy from 
                #channels above threshold.
                nsignals[0]+=1
                nsignal_strips[0] += n_strips[i]
                SignalEnergy[0] += energy1_pz[i]

                #print "Event %i Ch %i has Signal Energy %f" %(n_events, i,energy1_pz[i])

                if 'X' in channel_map[i]:
                    nXsignals[0]+=1
                    SignalEnergyX[0] += energy1_pz[i]
                elif 'Y' in channel_map[i]:
                    nYsignals[0]+=1
                    SignalEnergyY[0] += energy1_pz[i]

            if channel[i] == pmt_channel:
                #print energy[i], lightEnergy
                lightEnergy[0] += energy[i]
            elif sipm_channels_to_use[channel[i]]:
                lightEnergy[0] += energy[i]
                if abs(energy[i]/baseline_rms_filter[i]) > 5.0: #and  abs(sipm_min[i]/baseline_rms_filter[i]) < 5.0:
                    SignalEnergyLight[0] += energy[i]
            elif charge_channels_to_use[channel[i]]:
                chargeEnergy[0] += energy1_pz[i]
            if isMC:
                MCchargeEnergy[0] += energy1_pz[i]

 
            exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)

            #Sum the Waveforms of the active channels
            if charge_channels_to_use[channel[i]] and signal_map[i] > 0.5:
                if i == 0 or sum_wfm is None:
                    sum_wfm = EXODoubleWaveform(calibrated_wfm)
                else:
                    sum_wfm += calibrated_wfm

            (
                smoothed_max[i], 
                rise_time_stop10[i], 
                rise_time_stop20[i], 
                rise_time_stop30[i],
                rise_time_stop40[i], 
                rise_time_stop50[i], 
                rise_time_stop60[i], 
                rise_time_stop70[i],
                rise_time_stop80[i], 
                rise_time_stop90[i], 
                rise_time_stop95[i],
                rise_time_stop99[i],
            ) = wfmProcessing.get_risetimes(
                exo_wfm, 
                wfm_length[i], 
                sampling_frequency_Hz[0],
                skip_short_risetimes,
                label="%s %i keV" % (label, energy1_pz[i]),
            )


            # pause & draw
            #if not gROOT.IsBatch() and channel[i] == 4:
            #if not gROOT.IsBatch() and smoothed_max[i] > 60 and channel[i] != pmt_channel:
            #if not gROOT.IsBatch() and i_entry > 176:
            #if not gROOT.IsBatch():
            #if not gROOT.IsBatch() and do_debug and channel[i]!=pmt_channel and energy1_pz[i]>100:
            if False:

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


                hist = copy_wfm.GimmeHist("hist")
                hist.SetLineWidth(2)
                #hist.SetAxisRange(4,6)
                hist.Draw()

                canvas.Update()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")
                print val
                if (val == 'q' or val == 'Q'): sys.exit(1) 
                if val == 'b': ROOT.gROOT.SetBatch(True)
                if val == 'p': canvas.Print("entry_%i_proc_wfm_%s.png" % (i_entry, basename,))
                
            if isNGM and i == pmt_channel and pmt_hist:
            
                # check scaling of PMT hist and baseline of exo_wfm
                wfm_hist = exo_wfm.GimmeHist("wfm_hist")
                pmt_hist.Scale(wfm_hist.GetMaximum()/pmt_hist.GetMaximum())
                pmt_chi2[0] = struck_analysis_cuts.pmt_chisq_per_dof(
                    pmt_hist, wfm_hist, rms_keV[pmt_channel]/calibration_values[pmt_channel]
                )
    
                # testing chi2 calc
                if not ROOT.gROOT.IsBatch():
                    print "--> PMT signal"
                    pmt_hist.SetTitle("event %i, entry %i" % (i_entry/32, i_entry))
                    pmt_hist.SetLineColor(ROOT.kBlue)
                    wfm_hist.SetLineColor(ROOT.kRed)
                    print "\t PMT electronics noise:", rms_keV[pmt_channel]/calibration_values[pmt_channel]
                    print "\t lightEnergy:", lightEnergy[0]
                    print "\t pmt_chi2:", pmt_chi2[0]
                    if False:
                        canvas.cd()
                        pmt_hist.Draw()
                        wfm_hist.Draw("same")
                        #wfm_hist.Draw()
                        #pmt_hist.Draw("same")
                        print calibration_values[pmt_channel], lightEnergy[0], wfm_hist.GetMaximum()*calibration_values[pmt_channel]
                        canvas.Update()
                        raw_input("enter to continue")

            exo_wfm.IsA().Destructor(exo_wfm)      
            calibrated_wfm.IsA().Destructor(calibrated_wfm)
            # end loop over channels

        #-------------Create bundles of wire signals-------------
        (   nbundles,
            bundle_type,
            signal_bundle_map,
            bundle_energy,
            bundle_nsigs,
            nbundlesX[0],
            nbundlesY[0]
        ) = BundleSignals.BundleSignals(signal_map, energy1_pz, 
                                        nbundles, bundle_type, signal_bundle_map,
                                        bundle_energy, bundle_nsigs, isMC=isMC)
        
        #nbundles[0] = nbundles_temp
        #for bundle_index in xrange(nbundles[0]):
        #    bundle_type.append(bundle_type_temp[bundle_index])
        #for ch_index, bundle_index in enumerate(signal_bundle_map_temp):
        #    signal_bundle_map[ch_index] = bundle_index
        #--------------EndBundlind----------------
        

        ##### processing sum waveform
        if sum_wfm == None:
            smoothed_max_sum[0] = 0.0
            rise_time_stop10_sum[0] = 0.0 
            rise_time_stop20_sum[0] = 0.0
            rise_time_stop30_sum[0] = 0.0
            rise_time_stop40_sum[0] = 0.0
            rise_time_stop50_sum[0] = 0.0
            rise_time_stop60_sum[0] = 0.0
            rise_time_stop70_sum[0] = 0.0
            rise_time_stop80_sum[0] = 0.0
            rise_time_stop90_sum[0] = 0.0
            rise_time_stop95_sum[0] = 0.0
            rise_time_stop99_sum[0] = 0.0
            maxCurrent[0] = 0.0
            maxCurrent1[0] = 0.0
            maxCurrent2[0] = 0.0
            maxCurrent3[0] = 0.0
            maxCurrent4[0] = 0.0

        else:
            (
                smoothed_max_sum[0], 
                rise_time_stop10_sum[0], 
                rise_time_stop20_sum[0], 
                rise_time_stop30_sum[0],
                rise_time_stop40_sum[0], 
                rise_time_stop50_sum[0], 
                rise_time_stop60_sum[0], 
                rise_time_stop70_sum[0],
                rise_time_stop80_sum[0], 
                rise_time_stop90_sum[0], 
                rise_time_stop95_sum[0],
                rise_time_stop99_sum[0]
            ) = wfmProcessing.get_risetimes(
                sum_wfm, 
                sum_wfm.size(), 
                sampling_frequency_Hz[0],
                skip_short_risetimes,
                label="Event %i Sum %i keV" % (n_events, SignalEnergy[0]),
            )

            baseline_remover.SetStartSample(sum_wfm.size() - 2*n_baseline_samples[0] - 1)
            baseline_remover.Transform(sum_wfm)
            energy_sum[0] = baseline_remover.GetBaselineMean()
            energy_rms_sum[0] = baseline_remover.GetBaselineRMS()
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(sum_wfm)

            trap_wfm = EXODoubleWaveform(sum_wfm)
            trap_wfm2 = EXODoubleWaveform(sum_wfm)
            trap_filter.SetRampTime(280) # ns
            trap_filter.Transform(sum_wfm, trap_wfm)
            maxCurrent[0] = trap_wfm.GetMaxValue()
            trap_filter.SetRampTime(280*2) # ns
            trap_filter.Transform(sum_wfm, trap_wfm2)
            maxCurrent1[0] = trap_wfm2.GetMaxValue()
            trap_filter.SetRampTime(280*3) # ns
            trap_filter.Transform(sum_wfm, trap_wfm2)
            maxCurrent2[0] = trap_wfm2.GetMaxValue()
            trap_filter.SetRampTime(280*4) # ns
            trap_filter.Transform(sum_wfm, trap_wfm2)
            maxCurrent3[0] = trap_wfm2.GetMaxValue()
            trap_filter.SetRampTime(280*5) # ns
            trap_filter.Transform(sum_wfm, trap_wfm2)
            maxCurrent4[0] = trap_wfm2.GetMaxValue()

            if not ROOT.gROOT.IsBatch() and SignalEnergy[0]>200 and False:
                hist = sum_wfm.GimmeHist("sum1")
                hist.SetLineColor(ROOT.kRed)
                hist.SetLineWidth(2)
                hist.Draw()

                hist2 = trap_wfm.GimmeHist("trap")
                hist2.SetLineColor(ROOT.kBlue)
                hist2.SetLineWidth(2)
                hist2.Draw("same")

                hist2 = trap_wfm2.GimmeHist("trap2")
                hist2.SetLineColor(ROOT.kGreen+2)
                hist2.SetLineWidth(2)
                hist2.Draw("same")

                canvas.Update()
                print "maxCurrent:", maxCurrent[0]
                print "SignalEnergy:", SignalEnergy[0]
                print "A/E:", maxCurrent[0]/SignalEnergy[0]
                print "nsignals:", nsignals[0]
                for i_ch, val in enumerate(signal_map):
                    if val: print "\t", i_ch, channel_map[i_ch]
                print "rise_time_stop95_sum:", rise_time_stop95_sum[0]
                print "rise_time_stop50_sum:", rise_time_stop50_sum[0]
                print "95 - 50:", rise_time_stop95_sum[0]-rise_time_stop50_sum[0]
                print sum_wfm.GetSamplingPeriod()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")
                print val
                if (val == 'q' or val == 'Q'): sys.exit(1) 
                if val == 'b': ROOT.gROOT.SetBatch(True)
                if val == 'p': canvas.Print("entry_%i_current_wfm_%s.pdf" % (i_entry, basename,))
                canvas.Clear()

            sum_wfm.IsA().Destructor(sum_wfm)
            trap_wfm.IsA().Destructor(trap_wfm)
            trap_wfm2.IsA().Destructor(trap_wfm2)
            # end sum wfm calcs

        # check for bad conditions:
        high_baseline_rms = False
        high_energy_rms = False
        low_baseline_rms = False
        low_energy_rms = False
        wfm_too_low = False
        wfm_too_high = False
        if not isMC and pmt_chi2[0] > 3.0: is_bad[0] += 1
        rms_keV_sigma = struck_analysis_parameters.rms_keV_sigma

        # if any channels exceed conditions, we flag the event:
        for j, val  in enumerate(charge_channels_to_use):
            if val == 0: continue
            # check for any 5-sigma excursions of noise:
            try: # rms_keV_sigma doesn't exist for all runs
                if baseline_rms[j]*calibration[j] > rms_keV[j] + 5.0*rms_keV_sigma[j]: high_baseline_rms = True
                if energy_rms1_pz[j] > rms_keV[j] + 5.0*rms_keV_sigma[j]: high_energy_rms = True
                if baseline_rms[j]*calibration[j] < rms_keV[j] - 5.0*rms_keV_sigma[j]: low_baseline_rms = True
                if energy_rms1_pz[j] < rms_keV[j] - 5.0*rms_keV_sigma[j]: low_energy_rms = True
            except:
                pass
            if wfm_min[j] == 0: wfm_too_low = True
            if wfm_max[j] == pow(2,14)-1: wfm_too_high = True

        if high_baseline_rms: is_bad[0] += 2
        if high_energy_rms: is_bad[0] += 4
        if wfm_too_low: is_bad[0] += 8
        if wfm_too_high: is_bad[0] += 16
        if low_baseline_rms: is_bad[0] += 64
        if low_energy_rms: is_bad[0] += 128
        if found_dead: is_bad[0] += 256

        if not isMC and pulser_channel:
            if wfm_min[pulser_channel] < 3000: # 9th LXe value
                is_pulser[0] = 1
            if (wfm_max[pulser_channel] - baseline_mean[pulser_channel]) > 3000:
                is_pulser[0] = 1

        if isNGM: # check that event contains all channels:
            do_fill = True
            nfound_channels[0] = len(found_channels)
            #if (n_channels_in_this_event != len(charge_channels_to_use)):
            if (n_channels_in_this_event != n_channels_good):
              print "================> WARNING: %i channels in this event!! <================" % nfound_channels[0]
              print "================> found %i and in event %i <================" % (nfound_channels[0], n_channels_in_this_event)
              is_bad[0] += 32
            else:
                if nsignals[0] > 0: do_fill = True
                if is_pulser[0] > 0: do_fill = True

                if isMakeNoise:
                    if is_pulser[0] and not is_bad[0] and lightEnergy[0]< noiseLightCut and nsignals[0]<1:
                        #Making Noise library so only save noise triggers with no light signal and no charge signals.
                        do_fill = True
                    else:
                        do_fill = False
                    if struck_analysis_parameters.is_10th_LXe and out_tree.GetEntries() >= 20: break # 20 events x 1181 files 

            if do_fill:
                out_tree.Fill()
            n_events+=1
        else:
            out_tree.Fill()
            n_events+=1

        i_entry += 1
        # end loop over tree entries
    
    gout.cd("")
    #out_file = ROOT.TFile(out_filename, "recreate")
    run_tree.Write()

    print "done processing %i events in %.1e seconds" % (
        out_tree.GetEntries(), 
        time.time()-start_time)
    print "writing", out_filename
    out_tree.Write()

    try:
        # change file permissions -- for LLNL aztec:
        cmd = "chmod 644 %s" % out_filename
        output = commands.getstatusoutput(cmd)
        if output[0] != 0:
            print output[1]
    except OSError:
        print "WARNING: Could not chmod!!"


if __name__ == "__main__":


    parser = OptionParser()
    parser.add_option("--no-overwrite", dest="do_overwrite", default=True,
                      action="store_false", help="whether to overwrite files")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    parser.add_option("--MC", dest="isMC", default=False,
                      action="store_true", help="is this MC or Data")
    parser.add_option("-D", "--directory", dest="dir_name", default = "",
                        help="set output directory", metavar="Directory")
    parser.add_option("--Noise", dest="isMakeNoise", default=False,
                       action="store_true", help="are you trying to generate a noise file??")
    parser.add_option("-n", "--NoiseFile", dest="noise_file", default = None,
                        help="set noise file", metavar="Directory")

    (options, filenames) = parser.parse_args()

    if len(filenames) < 1:
        print "arguments: [sis or MC root files]"
        sys.exit(1)

    print "%i files to process" % len(filenames)
    
    print "Is MC set to ", options.isMC
    
    print "Make Noise is set to", options.isMakeNoise

    noise_file = None
    test_noise = ""
    test_noise_slac = ""
    #test_noise = "/home/teststand/testing/test_noiselib/tier3_SIS3316Raw_20160922143510_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root"
    #test_noise = "/p/lscratchd/jewell6/MCData_9thLXe/tier3_SIS3316Raw_20160921080244_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root"
    if struck_analysis_parameters.is_9th_LXe:
        test_noise = "/p/lscratchd/jewell6/MCData_9thLXe/NoiseFiles/noiselib/NoiseLib_9thLXe.root"
        test_noise_slac = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/NoiseLib_9thLXe.root"
    if struck_analysis_parameters.is_10th_LXe:
        test_noise = "/p/lscratchd/jewell6/MCData_9thLXe/NoiseFiles/noiselib/NoiseLib_10thLXe.root"
        test_noise_slac = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/NoiseLib_10thLXe.root"
    if options.isMC:
        if options.noise_file is not None:
            if os.path.isfile(options.noise_file):
                noise_file = options.noise_file
        elif os.path.isfile(test_noise):
            print "Using LLNL test Noise"
            noise_file = test_noise
        elif os.path.isfile(test_noise_slac):
            print "Using SLAC test Noise"
            noise_file = test_noise_slac
        else:
            print "Noise file is set to none"
            noise_file = None
        print "noise_file", noise_file
    

    for filename in filenames:
        process_file(filename, dir_name=options.dir_name, verbose=options.verbose, do_overwrite=options.do_overwrite, isMC=options.isMC, isMakeNoise=options.isMakeNoise, noise_file=noise_file)



