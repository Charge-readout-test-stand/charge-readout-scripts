#!/usr/bin/env python

"""
Do some waveform processing to extract energies, etc. 

to do:
  * add other rise times: 95, 99 
  * add slope of PZ-corrected section ?
  * fix decay time and calibration to work for tier 1 files

available CLHEP units are in 
http://java.freehep.org/svn/repos/exo/show/offline/trunk/utilities/misc/EXOUtilities/SystemOfUnits.hh?revision=HEAD

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

from ROOT import gROOT
# run in batch mode, suppress x output:
gROOT.SetBatch(True)
from ROOT import TFile
from ROOT import TTree
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TH1D
from ROOT import gSystem
from ROOT import gStyle


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



def process_file(filename):

    # options---------------------

    # whether to run in debug mode (draw wfms):
    do_debug = False
    #do_debug = True

    reporting_period = 1000

    # samples at wfm start and end to use for energy calc:
    n_baseline_samples_to_use = 50

    sampling_freq_Hz = 25.0e6
    n_channels = 6

    channels = [0,1,2,3,4,8]

    #---------------------------------------------------------------

    print "processing file: ", filename

    # construct a basename to use as output file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    basename = "_".join(basename.split("_")[1:])

    canvas = TCanvas()
    canvas.SetGrid(1,1)

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()

    # decide if this is a tier1 or tier2 file
    is_tier1 = False
    try:
        tree.GetEntry(0)
        tree.wfm0
        print "this is a tier2 file"
    except AttributeError:
        print "this is a tier1 file"
        n_channels = 1
        is_tier1 = True

    # open output file and tree
    out_filename = "tier3_%s.root" % basename
    out_file = TFile(out_filename, "recreate")
    out_tree = TTree("tree", "%s processed wfm tree" % basename)
    out_tree.SetLineColor(TColor.kBlue)
    out_tree.SetLineWidth(2)
    out_tree.SetMarkerColor(TColor.kBlue)


    # Writing trees in pyroot is clunky... need to use python arrays to provide
    # branch addresses, see:
    # http://wlav.web.cern.ch/wlav/pyroot/tpytree.html

    is_5Vinput = array('B', [0]*6) # unsigned 1-byte
    out_tree.Branch('is_5Vinput', is_5Vinput, 'is_5Vinput[%i]/b' % 6)

    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    channel = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('channel', channel, 'channel[%i]/i' % n_channels)

    # store some processing parameters:
    n_baseline_samples = array('I', [0]) # double
    out_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')
    n_baseline_samples[0] = n_baseline_samples_to_use

    decay_time = array('d', [0]*n_channels) # double
    out_tree.Branch('decay_time', decay_time, 'decay_time[%i]/D' % n_channels)

    # values from Peihao, 31 Oct 2015:
    decay_time_values = {}
    decay_time_values[0] = 850.0*CLHEP.microsecond
    decay_time_values[1] = 725.0*CLHEP.microsecond
    decay_time_values[2] = 775.0*CLHEP.microsecond
    decay_time_values[3] = 750.0*CLHEP.microsecond
    decay_time_values[4] = 450.0*CLHEP.microsecond
    decay_time_values[8] = 1e9*CLHEP.microsecond # FIXME -- should skip PZ for PMT

    # relative calibration:
    calibration = array('d', [0.0]*n_channels) # double
    out_tree.Branch('calibration', calibration, 'calibration[%i]/D' % n_channels)

    rise_time = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time', rise_time, 'rise_time[%i]/D' % n_channels)

    rise_time_start = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_start', rise_time_start, 'rise_time_start[%i]/D' % n_channels)

    rise_time_stop = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop', rise_time_stop, 'rise_time_stop[%i]/D' % n_channels)

    smoothed_max = array('d', [0]*n_channels) # double
    out_tree.Branch('smoothed_max', smoothed_max, 'smoothed_max[%i]/D' % n_channels)

    wfm_max = array('d', [0]*n_channels) # double
    out_tree.Branch('wfm_max', wfm_max, 'wfm_max[%i]/D' % n_channels)

    wfm_min = array('d', [0]*n_channels) # double
    out_tree.Branch('wfm_min', wfm_min, 'wfm_min[%i]/D' % n_channels)

    baseline_mean = array('d', [0]*n_channels) # double
    out_tree.Branch('baseline_mean', baseline_mean, 'baseline_mean[%i]/D' % n_channels)

    baseline_rms = array('d', [0]*n_channels) # double
    out_tree.Branch('baseline_rms', baseline_rms, 'baseline_rms[%i]/D' % n_channels)

    # some file-averaged parameters
    baseline_mean_file = array('d', [0]*6) # double
    out_tree.Branch('baseline_mean_file', baseline_mean_file, 'baseline_mean_file[%i]/D' % 6)

    baseline_rms_file = array('d', [0]*6) # double
    out_tree.Branch('baseline_rms_file', baseline_rms_file, 'baseline_rms_file[%i]/D' % 6)

    # make a hist for calculating some averages
    hist = TH1D("hist","",100, 0, pow(2,14))
    print "calculating mean baseline & baseline RMS for each channel in this file..."
    for (i, i_channel) in enumerate(channels):
        print "%i: ch %i" % (i, i_channel)
        draw_command = "wfm >> hist"
        if not is_tier1:
            draw_command = "wfm%i >> hist" % i_channel
        selection = "Iteration$<%i && channel==%i" % (n_baseline_samples[0], i_channel)
        print draw_command
        print selection
            
        tree.Draw(
            draw_command,
            selection,
            "goff"
        )
        baseline_mean_file[i] = hist.GetMean()
        baseline_rms_file[i] = hist.GetRMS()
        print baseline_mean_file[i]
        print baseline_rms_file[i]
    print "\t done"

    # decide whether 5V input was used for the digitizer or not. The
    # file-averaged baseline mean for channel 0 seems like a good indicator of
    # this -- we should also figure out if any channels are shaped...

    # from tier1_LXe_Run1_Amplifier_100mVPulse_10dB_5chargechannels_736AM_0
    calibration_values = {}
    calibration_values[0] = 1.0/3.76194501827427302e+02
    calibration_values[1] = 1.0/1.84579440737210035e+02
    calibration_values[2] = 1.0/1.90907907272149885e+02
    calibration_values[3] = 1.0/2.94300492610837466e+02
    calibration_values[4] = 1.0/1.40734817170111285e+02

    for (i, i_channel) in enumerate(channels):
        if baseline_mean_file[i] < 6500:
            is_5Vinput[i] = 1
            print "channel %i used 5V input range" % i_channel
            print "dividing calibration by 2.5"
            try:
                print calibration_values[i_channel]
                calibration_values[i_channel] /= 2.5
                print calibration_values[i_channel]
            except KeyError:
                print "no calibration data for ch %i" % i_channel

    print "calibration values:"
    for (i_channel, value)  in calibration_values.items():
        print "\t ch %i: %.3e" % (i_channel, value)


    # energy & rms before any processing
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

    fname = TObjString(filename)
    out_tree.Branch("filename",fname)

    start_time = time.clock()
    last_time = start_time

    if do_debug:
        reporting_period = 1

    print "%i entries" % n_entries

    # loop over all entries in tree
    for i_entry in xrange(n_entries):
        tree.GetEntry(i_entry)

        # print periodic output message
        if i_entry % reporting_period == 0:
            now = time.clock()
            print "====> entry %i of %i (%.2f percent in %.1f seconds, %.1f seconds total)" % (
                i_entry, n_entries, 100.0*i_entry/n_entries, now - last_time, now -
                start_time)
            last_time = now

        for i in xrange(n_channels):

            if is_tier1:
                wfm = tree.wfm
                channel[i] = tree.channel

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
                    wfm = tree.wfm8

            wfm_length = len(wfm)

            exo_wfm = EXODoubleWaveform(array('d',wfm), wfm_length)


            new_wfm = EXODoubleWaveform(array('d',wfm), wfm_length)
            energy_wfm = EXODoubleWaveform(array('d',wfm), wfm_length)


            wfm_max[i] = exo_wfm.GetMaxValue()
            wfm_min[i] = exo_wfm.GetMinValue()

            exo_wfm.SetSamplingFreq(25.0e6/CLHEP.second)
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
                if exo_wfm.GetMaxValue() < 50: continue # skip low energy wfms
                if i == 5: continue # skip PMT

            # measure energy before PZ correction
            baseline_remover.SetStartSample(wfm_length - n_baseline_samples[0] - 1)
            baseline_remover.Transform(exo_wfm, energy_wfm)
            try:
                calibration[i] = calibration_values[channel[i]]
            except KeyError:
                #print channel[i]
                calibration[i] = 1.0
                
            energy[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms[i] = baseline_remover.GetBaselineRMS()*calibration[i]
            if channel[i] == 8:
                energy[i] = exo_wfm.GetMaxValue()

            if do_debug:
                print "energy measurement with %i samples: %.2f" % (
                    n_baseline_samples[0], energy[i])
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                val = raw_input("press enter ")

            # measure energy before PZ correction, use 2x n_baseline_samples
            baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(exo_wfm, energy_wfm)
            baseline_remover.SetStartSample(wfm_length - 2*n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm, energy_wfm)
            energy1[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms1[i] = baseline_remover.GetBaselineRMS()*calibration[i]

            if do_debug:
                print "energy measurement with %i samples: %.2f" % (
                    2*n_baseline_samples[0], energy1[i])
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                val = raw_input("press enter ")

            # correct for exponential decay
            pole_zero = EXOPoleZeroCorrection()
            
            decay_time[i] = decay_time_values[channel[i]]
            pole_zero.SetDecayConstant(decay_time[i])
            pole_zero.Transform(exo_wfm, energy_wfm)

            # measure energy after PZ correction
            baseline_remover.SetBaselineSamples(n_baseline_samples[0])
            baseline_remover.SetStartSample(wfm_length - n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm, energy_wfm)
            energy_pz[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms_pz[i] = baseline_remover.GetBaselineRMS()*calibration[i]


            if do_debug:
                print "energy measurement after PZ with %i samples: %.2f" % (
                    n_baseline_samples[0], energy_pz[i])
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                val = raw_input("press enter ")


            # measure energy after PZ correction, use 2x n_baseline_samples
            baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(exo_wfm, new_wfm)

            if do_debug:
                baseline_remover.Transform(exo_wfm, energy_wfm)
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                print "removed baseline"
                val = raw_input("press enter ")

            # FIXME -- having trouble doing PZ transform in place!!
            #pole_zero.Transform(energy_wfm, energy_wfm)
            pole_zero.Transform(new_wfm, energy_wfm)
            #print pole_zero.GetDecayConstant()

            if do_debug:
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                print "PZ transform"
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

            baseline_remover.SetStartSample(wfm_length - 2*n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm, energy_wfm)
            energy1_pz[i] = baseline_remover.GetBaselineMean()*calibration[i]
            energy_rms1_pz[i] = baseline_remover.GetBaselineRMS()*calibration[i]

            if do_debug:
                print "energy measurement after PZ with %i samples: %.2f" % (
                    2*n_baseline_samples[0], energy1_pz[i])
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                print "energy calc"
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")


            # perform some smoothing -- be careful because this changes the rise
            # time
            smoother = EXOSmoother()
            smoother.SetSmoothSize(5)
            #smoother.SetSmoothSize(50)
            smoother.Transform(exo_wfm,new_wfm) #FIXME

            # used smoothed max val to calculate rise time
            #max_val = exo_wfm.GetMaxValue()
            max_val = new_wfm.GetMaxValue() # smoothed max

            #pole_zero.Transform(new_wfm, new_wfm) # FIXME -- just for drawing

            rise_time_calculator = EXORisetimeCalculation()
            rise_time_calculator.SetPulsePeakHeight(max_val)
            rise_time_calculator.SetInitialThresholdPercentage(0.1)
            rise_time_calculator.SetFinalThresholdPercentage(0.90)
            # throws an alert if max_val is 0
            if max_val > 0.0:
                rise_time_calculator.Transform(exo_wfm,exo_wfm)

            # set output tree variables
            event[0] = tree.event
            smoothed_max[i] = new_wfm.GetMaxValue()
            rise_time[i] = rise_time_calculator.GetRiseTime()/CLHEP.microsecond
            rise_time_start[i] = rise_time_calculator.GetInitialThresholdCrossing()*period/CLHEP.microsecond
            rise_time_stop[i] = rise_time_calculator.GetFinalThresholdCrossing()*period/CLHEP.microsecond


            """
            trap_filter = EXOTrapezoidalFilter()
            trap_filter.SetFlatTime(1.0*CLHEP.microsecond)
            trap_filter.SetRampTime(1.0*CLHEP.microsecond)
            trap_filter.Transform(exo_wfm, new_wfm)
            """
         

            # pause & draw
            if not gROOT.IsBatch() and channel[i] == 4:
            #if not gROOT.IsBatch() and smoothed_max[i] > 60 and channel[i] != 8:
            #if not gROOT.IsBatch() and i_entry > 176:
            #if not gROOT.IsBatch():

                print "--> entry %i | channel %i" % (i_entry, channel[i])
                print "\t n samples: %i" % wfm_length
                print "\t max %.2f" % wfm_max[i]
                print "\t min %.2f" % wfm_min[i]
                print "\t smoothed max %.2f" % smoothed_max[i]
                print "\t rise time [microsecond]: %.3f" % (rise_time[i])
                print "\t rise start [microsecond]: %.2f" % (rise_time_start[i])
                print "\t rise stop [microsecond]: %.2f" % (rise_time_stop[i])
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

                #print val
                if (val == 'q' or val == 'Q'): sys.exit(1) 
                if val == 'b': gROOT.SetBatch(True)
                if val == 'p': canvas.Print("entry_%i_proce_wfm_%s.png" % (i_entry, basename,))
                
            # end loop over channels

        out_tree.Fill()

    print "done processing"
    print "writing", out_filename
    out_tree.Write()
    out_file.Close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)

    print "%i files to process" % len(sys.argv[1:])


    for filename in sys.argv[1:]:
        process_file(filename)





