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
import wfmProcessing

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

    # getting tier1 run_tree
    run_tree_tier1 = out_file.Get("run_tree")
    run_tree_tier1.GetEntry(0)

    if run_tree_tier1.is_external: # skipping externally triggered files
        print "skipping externally triggered files"
        return 0
    
    # create a run tree to save active channels and n_entries
    run_tree = TTree("run_tree", "internal trigger run tree")
    channels = []
    n_entries = []

    # channel loop: loop over 16 trees
    for i in xrange(16): 
        tree = root_file.Get("tree%i" % i)

        try: # see if tree exists
            tree.GetEntries() 
        except AttributeError:
            print "problem accessing tree%i -- skipping this file" % i
            return 0

        out_tree = TTree("tree%i", "%s processed wfm tree" % basename)

        if tree.GetEntries() > 0: # if tree is not empty, append to active channel list
            channels.append(i)
            n_entries.append(i)
        else: # if tree is empty, write empty out_tree and go to next channel
            out_tree.Write()
            continue

        ## set up global parameter branches
        tree.GetEntry(0)

        is_external = array('B', [0]) # unsigned char
        out_tree.Branch('is_external', is_external, 'is_external/b')
        is_external[0] = tree.is_external

        is_2Vinput = array('B', [0]) # unsigned char
        out_tree.Branch('is_2Vinput', is_2Vinput, 'is_2Vinput/b')
        is_2Vinput[0] = tree.is_2Vinput

        is_50ohm = array('B', [0]) # unsigned char 
        out_tree.Branch('is_50ohm', is_50ohm, 'is_50ohm/b')
        is_50ohm[0] = tree.is_50ohm

        is_pospolarity = array('B', [0]) # unsigned char
        out_tree.Branch('is_pospolarity', is_pospolarity, 'is_pospolarity/b')
        is_pospolarity[0] = tree.is_pospolarity

        sampling_freq_Hz = array('d', [0]) # double
        out_tree.Branch('sampling_freq_Hz', sampling_freq_Hz, 'sampling_freq_Hz/D')
        sampling_freq_Hz[0] = tree.sampling_freq_Hz

        trigger_time = array('d', [0.0]) # double
        out_tree.Branch('trigger_time', trigger_time, 'trigger_time/D')
        trigger_time[0] = tree.wfm_delay / tree.sampling_freq_Hz * 1e6  ## in microseconds

        wfm_length = array('I', [0]) # unsigned int
        out_tree.Branch('wfm_length', wfm_length, 'wfm_length/i')
        wfm_length[0] = tree.wfm_length

        #store some processing parameters:
        n_baseline_samples = array('I', [0]) # double
        out_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')
        n_baseline_samples[0] = tree.wfm_delay / 4

        decay_time = array('d', [0]) # double
        out_tree.Branch('decay_time', decay_time, 'decay_time/D')
        if i == pmt_channel:
            decay_time[0] = 1e9*CLHEP.microsecond
        else:
            try:
                decay_time[0] = struck_analysis_parameters.decay_time_values[i]
            except KeyError:
                print "no decay info for channel %i" % channel
                decay_time[0] = 1e9*CLHEP.microsecond

        calibration = array('d', [0.0]) # double
        out_tree.Branch('calibration', calibration, 'calibration/D')
        try:
            calibration[0] = struck_analysis_parameters.calibration_values[i]
        except KeyError:
            print "no calibration info for channel %i" % channel
            calibration[0] = 1.0
        if is_2Vinput[0]:
            calibration[0] /= 2.5

        # file parameters
        file_start_time = array('I', [0]) # unsigned int
        file_start_time[0] = posix_start_time
        out_tree.Branch('file_start_time', file_start_time, 'file_start_time/i')

        n_entries_array = array('I', [0]) # unsigned int
        out_tree.Branch('n_entries', n_entries_array, 'n_entries/i')
        n_entries_array[0] = tree.GetEntries()

        ## event-specific parameters
        event = array('I', [0]) # unsigned int
        out_tree.Branch('event', event, 'event/i')

        timestamp = array('L', [0]) # timestamp for each event, unsigned long
        out_tree.Branch('timestamp', timestamp, 'timestamp/l')

        timestampDouble = array('d', [0]) # double
        out_tree.Branch('timestampDouble', timestampDouble, 'timestampDouble/D')

        time_since_last = array('d', [0]) # double
        out_tree.Branch('time_since_last', time_since_last, 'time_since_last/D')

        rise_time_stop10 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop10', rise_time_stop10, 'rise_time_stop10/D')

        rise_time_stop20 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop20', rise_time_stop20, 'rise_time_stop20/D')

        rise_time_stop30 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop30', rise_time_stop30, 'rise_time_stop30/D')

        rise_time_stop40 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop40', rise_time_stop40, 'rise_time_stop40/D')

        rise_time_stop50 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop50', rise_time_stop50, 'rise_time_stop50/D')

        rise_time_stop60 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop60', rise_time_stop60, 'rise_time_stop60/D')

        rise_time_stop70 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop70', rise_time_stop70, 'rise_time_stop70/D')

        rise_time_stop80 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop80', rise_time_stop80, 'rise_time_stop80/D')

        rise_time_stop90 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop90', rise_time_stop90, 'rise_time_stop90/D')

        rise_time_stop95 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop95', rise_time_stop95, 'rise_time_stop95/D')

        rise_time_stop99 = array('d', [0]) # double
        out_tree.Branch('rise_time_stop99', rise_time_stop99, 'rise_time_stop99/D')

        smoothed_max = array('d', [0]) # double
        out_tree.Branch('smoothed_max', smoothed_max, 'smoothed_max/D')

        baseline_mean = array('d', [0]) # double
        out_tree.Branch('baseline_mean', baseline_mean, 'baseline_mean/D')

        baseline_rms = array('d', [0]) # double
        out_tree.Branch('baseline_rms', baseline_rms, 'baseline_rms/D')

        # energy & rms before processing 
        energy = array('d', [0]) # double
        out_tree.Branch('energy', energy, 'energy/D')
        energy_rms = array('d', [0]) # double
        out_tree.Branch('energy_rms', energy_rms, 'energy_rms/D')

        # energy & rms before processing, using 2x sample length
        energy1 = array('d', [0]) # double
        out_tree.Branch('energy1', energy1, 'energy1/D')
        energy_rms1 = array('d', [0]) # double
        out_tree.Branch('energy_rms1', energy_rms1, 'energy_rms1/D')

        # energy & rms after PZ
        energy_pz = array('d', [0]) # double
        out_tree.Branch('energy_pz', energy_pz, 'energy_pz/D')
        energy_rms_pz = array('d', [0]) # double
        out_tree.Branch('energy_rms_pz', energy_rms_pz, 'energy_rms_pz/D')

        # energy & rms after PZ, using 2x sample length
        energy1_pz = array('d', [0]) # double
        out_tree.Branch('energy1_pz', energy1_pz, 'energy1_pz/D')
        energy_rms1_pz = array('d', [0]) # double
        out_tree.Branch('energy_rms1_pz', energy_rms1_pz, 'energy_rms1_pz[%i]/D')
     
          
        # file name branch
        fname = TObjString(os.path.abspath(filename))
        out_tree.Branch("filename",fname)
        run_tree.Branch("filename",fname)

        last_timestamp = 0.0 # used to save timestamp of last event

        # start event loop
        for i_entry in xrange(tree.GetEntries()):
            event[0] = i_entry
            # print periodic output message
            if i_entry % reporting_period == 0:
                now = time.clock()
                print "----> entry %i of %i (%.2f percent in %.1f seconds, %.1f seconds total)" % (
                    i_entry, min(n_entries), 100.0*i_entry/min(n_entries), now - last_time, now -
                    start_time)
                last_time = now

            tree.GetEntry(i_entry)
            
            # save timestamps
            timestamp[0] = tree.timestamp
            timestampDouble[0] = tree.timestampDouble
            time_since_last[0] = timestampDouble[0] - last_timestamp
            last_timestamp = timestampDouble[0]


            # wfm processing:
            wfm = tree.wfm
            exo_wfm = EXODoubleWaveform(array('d', wfm), wfm_length[0])

            (baseline_mean[0], baseline_rms[0], energy[0], energy_rms[0], energy1[0], energy_rms1[0],
                energy_pz[0], energy_rms_pz[0], energy1_pz[0], energy_rms1_pz[0],
                calibrated_wfm) = wfmProcessing.get_wfmparams(exo_wfm, wfm_length[0], sampling_freq_Hz[0],
                                    n_baseline_samples[0], calibration[0], decay_time[0], channel==pmt_channel)
            
            (smoothed_max[0], rise_time_stop10[0], rise_time_stop20[0], rise_time_stop30[0],
                rise_time_stop40[0], rise_time_stop50[0], rise_time_stop60[0], rise_time_stop70[0],
                rise_time_stop80[0], rise_time_stop90[0], rise_time_stop95[0],
                rise_time_stop99[0]) = wfmProcessing.get_risetimes(exo_wfm, wfm_length[0], sampling_freq_Hz[0])


            out_tree.Fill()
        #end event loop

    # end channel loop

    # save run_tree parameters
    n_channels = array('B', [0]) # unsigned char
    run_tree.Branch('n_channels', n_channels, 'n_channels/b')
    n_channels[0] = len(channels)

    channels = array('B', channels) # unsigned char
    run_tree.Branch('channels', channels, 'channels[%i]/b' % len(channels))

    n_entries = array('I', n_entries) # unsigned integer
    run_tree.Branch('n_entries', n_entries, 'n_entries[%i]/i' % len(n_entries))

    run_tree.Fill()
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

    (options, filenames) = parser.parse_args()

    if len(filenames) < 1:
        print "arguments: [sis root files]"
        sys.exit(1)

    print "%i files to process" % len(filenames)

    for filename in filenames:
        process_file(filename, verbose=options.verbose, do_overwrite=options.do_overwrite)





