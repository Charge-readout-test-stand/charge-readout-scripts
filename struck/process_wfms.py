#!/usr/bin/env python

"""
Do some waveform processing to extract energies, etc. 

available CLHEP units are in 
http://java.freehep.org/svn/repos/exo/show/offline/trunk/utilities/misc/EXOUtilities/SystemOfUnits.hh?revision=HEAD

Use on tier2 files

"""


import os
import sys
import time

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TFile
from ROOT import TTree
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gSystem
from ROOT import gStyle


gSystem.Load("$EXOLIB/lib/libEXOROOT")
#gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import CLHEP
from ROOT import EXODoubleWaveform
#from ROOT import EXOTrapezoidalFilter
from ROOT import EXOBaselineRemover
from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother
from ROOT import EXOPoleZeroCorrection


from array import array

canvas = TCanvas()
canvas.SetGrid(1,1)


def process_file(filename):

    # options---------------------

    do_debug = False

    reporting_period = 1000

    sampling_freq_Hz = 25.0e6
    n_channels = 6


    # values from Peihao, 31 Oct 2015:
    decay_times = {}
    decay_times[0] = 850.0*CLHEP.microsecond
    decay_times[1] = 725.0*CLHEP.microsecond
    decay_times[2] = 775.0*CLHEP.microsecond
    decay_times[3] = 750.0*CLHEP.microsecond
    decay_times[4] = 500.0*CLHEP.microsecond

    #---------------------------------------------------------------

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()

    is_tier1 = False
    try:
        tree.GetEntry(0)
        tree.wfm0
        print "this is a tier2 file"
    except AttributeError:
        print "this is a tier1 file"
        n_channels = 1
        is_tier1 = True

    out_file = TFile("test_%s.root" % basename, "recreate")
    out_tree = TTree("tree", "%s processed wfm tree" % basename)

    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')
  
    channel = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('channel', channel, 'channel[%i]/i' % n_channels)

    # store some processing parameters:
    n_baseline_samples = array('I', [0]) # double
    out_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')

    decay_time = array('d', [0]) # double
    out_tree.Branch('decay_time', decay_time, 'decay_time/D')

    # set the processing parameters:
    n_baseline_samples[0] = 50

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

            else:
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
                if exo_wfm.GetMaxValue() < 50: continue # FIXME
                if i == 5: continue # FIXME

            # measure energy before PZ correction
            baseline_remover.SetStartSample(wfm_length - n_baseline_samples[0] - 1)
            baseline_remover.Transform(exo_wfm, energy_wfm)
            energy[i] = baseline_remover.GetBaselineMean()
            energy_rms[i] = baseline_remover.GetBaselineRMS()

            if do_debug:
                print energy[i]
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

            # measure energy before PZ correction, use 2x n_baseline_samples
            baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(exo_wfm, energy_wfm)
            baseline_remover.SetStartSample(wfm_length - 2*n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm, energy_wfm)
            energy1[i] = baseline_remover.GetBaselineMean()
            energy_rms1[i] = baseline_remover.GetBaselineRMS()

            if do_debug:
                print energy1[i]
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

            # correct for exponential decay
            pole_zero = EXOPoleZeroCorrection()
            decay_time[0] = 0.0
            
            if i < 5:
                decay_time[0] = decay_times[i]
            pole_zero.SetDecayConstant(decay_time[0])
            pole_zero.Transform(exo_wfm, energy_wfm)

            # measure energy after PZ correction
            baseline_remover.SetBaselineSamples(n_baseline_samples[0])
            baseline_remover.SetStartSample(wfm_length - n_baseline_samples[0] - 1)
            baseline_remover.Transform(energy_wfm, energy_wfm)
            energy_pz[i] = baseline_remover.GetBaselineMean()
            energy_rms_pz[i] = baseline_remover.GetBaselineRMS()


            if do_debug:
                print energy_pz[i]
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")


            # measure energy after PZ correction, use 2x n_baseline_samples
            baseline_remover.SetBaselineSamples(2*n_baseline_samples[0])
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(exo_wfm, new_wfm)

            if do_debug:
                baseline_remover.Transform(exo_wfm, energy_wfm)
                energy_wfm.GimmeHist().Draw()
                canvas.Update()
                print "removed baseline"
                val = raw_input("enter to continue (q=quit, b=batch, p=print) ")

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
            energy1_pz[i] = baseline_remover.GetBaselineMean()
            energy_rms1_pz[i] = baseline_remover.GetBaselineRMS()

            if do_debug:
                print energy1_pz[i]
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
            rise_time_calculator.Transform(exo_wfm,exo_wfm)

            # set output tree variables
            event[0] = tree.event
            if is_tier1:
                channel[i] = tree.channel
            else:
                channel[i] = int(tree.channel[i])
            wfm_max[i] = exo_wfm.GetMaxValue()
            wfm_min[i] = exo_wfm.GetMinValue()
            smoothed_max[i] = new_wfm.GetMaxValue()
            rise_time[i] = rise_time_calculator.GetRiseTime()/CLHEP.microsecond
            rise_time_start[i] = rise_time_calculator.GetInitialThresholdCrossing()*period/CLHEP.microsecond
            rise_time_stop[i] = rise_time_calculator.GetFinalThresholdCrossing()*period//CLHEP.microsecond


            """
            trap_filter = EXOTrapezoidalFilter()
            trap_filter.SetFlatTime(1.0*CLHEP.microsecond)
            trap_filter.SetRampTime(1.0*CLHEP.microsecond)
            trap_filter.Transform(exo_wfm, new_wfm)
            """
         

            # pause & draw
            if not gROOT.IsBatch() and smoothed_max[i] > 60 and channel[i] != 8:
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
                print energy_rms1[i] - energy_rms1_pz[i]


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
    out_tree.Write()
    out_file.Close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)

    print "%i files to process" % len(sys.argv[1:])


    for filename in sys.argv[1:]:
        print "calling process_file(",filename,")"
        process_file(filename)
        print "done with  process_file(",filename,")"





