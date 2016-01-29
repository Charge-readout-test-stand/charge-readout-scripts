#!/usr/bin/env python

"""
FIXME -- Jan 28, 2016 -- energy PZ values are screwed up after switching for wfmProcessing!!!


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
import datetime
import numpy as np
from optparse import OptionParser


from ROOT import gROOT
# run in batch mode -- set to False for debugging:
#gROOT.SetBatch(False)
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
import wfmProcessing


def process_file(filename, dir_name= "", verbose=True, do_overwrite=True, isMC=False):

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
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use

    if isMC:
        #MC has different structure so use MC channels
        channels = struck_analysis_parameters.MCchannels
        n_chargechannels = struck_analysis_parameters.n_MCchargechannels
        pmt_channel = None #No PMT in MC
        n_channels = struck_analysis_parameters.MCn_channels
        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    
    # this is the number of channels per event (1 if we are processing tier1
    # data, len(channels) if we are processing tier2 data
    n_channels_in_event = n_channels

    #---------------------------------------------------------------

    print "processing file: ", filename

    # keep track of how long it takes to process file:
    start_time = time.clock()
    last_time = start_time
    prev_time_stamp = 0.0
    basename = wfmProcessing.create_basename(filename)


    # calculate file start time, in POSIX time, from filename suffix
    # date and time are last two parts of filename separated with "_":
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
        posix_start_time = 0

    # a canvas for drawing, if debugging:
    canvas = TCanvas()
    canvas.SetGrid(1,1)

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = None
    if isMC:
        tree = root_file.Get("evtTree")
    else:
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
    
    if isMC:
        n_channels_in_event = n_channels
        is_tier1 = False

    # open output file and tree
    out_filename = wfmProcessing.create_outfile_name(filename)
    out_filename = dir_name + out_filename
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

    # Writing trees in pyroot is clunky... need to use python arrays to provide
    # branch addresses, see:
    # http://wlav.web.cern.ch/wlav/pyroot/tpytree.html

    is_2Vinput = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('is_2Vinput', is_2Vinput, 'is_2Vinput[%i]/i' % n_channels)

    is_amplified = array('I', [1]*n_channels) # unsigned int
    out_tree.Branch('is_amplified', is_amplified, 'is_amplified[%i]/i' % n_channels)

    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    file_start_time = array('I', [0]) # unsigned int
    file_start_time[0] = posix_start_time
    out_tree.Branch('file_start_time', file_start_time, 'file_start_time/i')
    run_tree.Branch('file_start_time', file_start_time, 'file_start_time/i')

    time_stamp = array('L', [0]) # timestamp for each event, unsigned long
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
    elif isMC:
        #MC so this doesn't exist
        run_time[0] = 0
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
    if isMC:
        #MC is always triggered at sample 200 this is hardcoded into nEXO_Analysis
        trigger_time[0] = 200/sampling_freq_Hz*1e6
    elif do_debug:
        print "--> debugging -- skipping trigger_time calc"
    else:
        trigger_hist = TH1D("trigger_hist","",5000,0,5000)
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
    n_baseline_samples[0] = n_baseline_samples_to_use

    decay_time = array('d', [0]*n_channels_in_event) # double
    out_tree.Branch('decay_time', decay_time, 'decay_time[%i]/D' % n_channels_in_event)

    decay_time_values = struck_analysis_parameters.decay_time_values
    decay_time_values[pmt_channel] = 1e9*CLHEP.microsecond
    for (i, i_channel) in enumerate(channels):
        try:
            decay_time[i] = decay_time_values[i_channel]
        except KeyError:
            print "no decay info for channel %i" % i_channel
            decay_time[i] = 1e9*CLHEP.microsecond


    
    if isMC:
        #No decay in MC so set to infinite
        decay_time_values = [1e9*CLHEP.microsecond]*n_channels


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

    # parameters coming from sum waveform
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

    #Store the total energy on all MC channels even ones that 
    #Are missing in real life
    #MCenergy_sum = array('d', [0.0])
    #out_tree.Branch('MCenergy_sum', MCenergy_sum, 'MCenergy_sum/D')

    energy_rms_sum = array('d', [0.0])
    out_tree.Branch('energy_rms_sum', energy_rms_sum, 'energy_rms_sum/D')


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
        if isMC:
            #Command that worked
            #evtTree->Draw("ChannelWaveform[12]:Iteration$","Entry$==10 && Iteration$<300")
            draw_command = "ChannelWaveform[%i]:Iteration$" % (i_channel)
            selection = "Entry$==0 && Iteration$<%i" % (n_baseline_samples[0])
        tree.Draw(
            draw_command,
            selection,
            "goff"
        )
        baseline_mean_file[i] = hist.GetMean()
        print "\t draw command: %s | selection %s" % (draw_command, selection)
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
    if isMC:
        for n in np.arange(n_channels):
            #MC is given in number of e- so need to multiply by Wvalue to get eV
            #Need factor of 1e-3 to get keV
            calibration_values[int(n)] = struck_analysis_parameters.Wvalue*1e-3

    print "choosing calibration values..."
    for (i, i_channel) in enumerate(channels):
        print "channel %i" % i_channel

        try:
            print "\t original calibration value %.4e" % calibration_values[i_channel]
        except KeyError:
            print "\t no calibration data for ch %i" % i_channel
            continue

        is_2Vinput[i] = struck_analysis_parameters.is_2Vinput(baseline_mean_file[i])
        if isMC:
            is_2Vinput[i] = False
        elif is_2Vinput[i]:
            print "\t channel %i used 2V input range" % i_channel
            print "\t dividing calibration by 2.5"
            calibration_values[i_channel] /= 2.5

        # this doesn't seem very reliable
        #is_amplified[i] = struck_analysis_parameters.is_amplified(
        #    baseline_mean_file[i], baseline_rms_file[i])


        if is_amplified[i] == 0 and not isMC:
            if i_channel != pmt_channel:
                calibration_values[i_channel] *= 4.0
                print "\t multiplying calibration by 4"
                print "\t channel %i is unamplified" % i_channel
        print "\t channel %i calibration: %.4e" % (i_channel, calibration_values[i_channel])
    
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
    else:
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
 
    #Total Energy in MC for all channels including not active channels
    MCchargeEnergy = array('d', [0.0])
    out_tree.Branch('MCchargeEnergy', MCchargeEnergy, 'MCchargeEnergy/D')

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
    
    fname = TObjString(os.path.abspath(filename))
    out_tree.Branch("filename",fname)
    run_tree.Branch("filename",fname)

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
        if isMC:
            #Event number
            event[0] = i_entry
        else:
            event[0] = tree.event

        if is_tier1:
            time_stamp[0] = tree.timestamp
            time_stampDouble[0] = tree.timestampDouble
        elif isMC:
            #No timestamp in MC 
            time_stamp[0] = 0
            time_stampDouble[0] = 0
        else:
            time_stamp[0] = tree.time_stamp
            time_stampDouble[0] = tree.time_stampDouble

        # calculate time since previous event
        if prev_time_stamp > 0:
            time_since_last[0] = time_stampDouble[0] - prev_time_stamp
        else:
            time_since_last[0] = -1.0
        prev_time_stamp = time_stampDouble[0]
        if isMC: prev_time_stamp = 0

        # initialize these two to zero
        chargeEnergy[0] = 0.0
        MCchargeEnergy[0] = 0.0
        lightEnergy[0] = 0.0

        sum_wfm = None
        for i in xrange(n_channels_in_event):

            if is_tier1:
                wfm = tree.wfm
                channel[i] = tree.channel
                wfm_max_time[i] = tree.wfm_max_time
            elif isMC:
                #START HERE MJJJ
                wfm = [wfmp for wfmp in tree.ChannelWaveform[i]]
                channel[i] = i
                wfm_max_time[i] = np.argmax(wfm)
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

            if do_debug:
                # a copy of the un-transformed wfm, for debugging
                copy_wfm = EXODoubleWaveform(exo_wfm)

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
            ) = wfmProcessing.get_wfmparams(
                exo_wfm=exo_wfm, 
                wfm_length=wfm_length[0], 
                sampling_freq_Hz=sampling_freq_Hz,
                n_baseline_samples=n_baseline_samples[0], 
                calibration=calibration[i], 
                decay_time=decay_time[i], 
                is_pmtchannel=channel[i]==pmt_channel,
            )
            
            
            if channel[0] == pmt_channel:
                lightEnergy[0] = energy[i]
            elif charge_channels_to_use[channel[0]]:
                chargeEnergy[0] += energy1_pz[i]
            if isMC:
                MCchargeEnergy[0] += energy1_pz[i]

 
            wfm_max[i] = exo_wfm.GetMaxValue()
            wfm_min[i] = exo_wfm.GetMinValue()

            exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)

            #Sum the Waveforms of the active channels
            if charge_channels_to_use[channel[i]]:
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
                wfm_length[0], 
                sampling_frequency_Hz[0],
            )


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


                hist = copy_wfm.GimmeHist("hist")
                hist.SetLineWidth(2)
                #hist.SetAxisRange(4,6)
                hist.Draw()

                canvas.Update()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

                print val
                if (val == 'q' or val == 'Q'): sys.exit(1) 
                if val == 'b': gROOT.SetBatch(True)
                if val == 'p': canvas.Print("entry_%i_proc_wfm_%s.png" % (i_entry, basename,))
                
            # end loop over channels


        ##### processing sum waveform
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
            wfm_length[0], 
            sampling_frequency_Hz[0]
        )
        
        baseline_remover = EXOBaselineRemover()
        baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
        baseline_remover.SetStartSample(wfm_length[i] - 2*n_baseline_samples[0] - 1)
        baseline_remover.Transform(sum_wfm)
        energy_sum[0] = baseline_remover.GetBaselineMean()
        energy_rms_sum[0] = baseline_remover.GetBaselineRMS()

        #raw_input("Press Enter...")

        out_tree.Fill()

    
    run_tree.Write()

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
    parser.add_option("--MC", dest="isMC", default=False,
                      action="store_true", help="is this MC or Data")
    parser.add_option("-D", "--directory", dest="dir_name", default = "",
                        help="set output directory", metavar="Directory")

    (options, filenames) = parser.parse_args()

    if len(filenames) < 1:
        print "arguments: [sis or MC root files]"
        sys.exit(1)

    print "%i files to process" % len(filenames)

    for filename in filenames:
        process_file(filename, dir_name=options.dir_name, verbose=options.verbose, do_overwrite=options.do_overwrite, isMC=options.isMC)





