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
#gROOT.SetBatch(True)
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
from ROOT import EXOTrapezoidalFilter
from ROOT import EXOBaselineRemover
from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother


from array import array

canvas = TCanvas()
canvas.SetGrid(1,1)

def process_waveform(wfm):
    pass


def process_file(filename):

    sampling_freq_Hz = 25.0e6

    n_channels = 6

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

    rise_time = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time', rise_time, 'rise_time[%i]/D' % n_channels)

    rise_time_start = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_start', rise_time_start, 'rise_time_start[%i]/D' % n_channels)

    rise_time_stop = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop', rise_time_stop, 'rise_time_stop[%i]/D' % n_channels)

    smoothed_max = array('d', [0]*n_channels) # double
    out_tree.Branch('smoothed_max', smoothed_max, 'smoothed_max[%i]/D' % n_channels)

    wfm_max = array('d', [0])*n_channels # double
    out_tree.Branch('wfm_max', wfm_max, 'wfm_max[%i]/D' % n_channels)

    start_time = time.clock()
    last_time = start_time

    print "%i entries" % n_entries
    for i_entry in xrange(n_entries):
        tree.GetEntry(i_entry)

        if i_entry % 1000 == 0:
            now = time.clock()
            print "====> entry %i of %i (%.2f percent in %.1f seconds, %.1f seconds total)" % (
                i_entry, n_entries, 100.0*i_entry/n_entries, now - last_time, now -
                start_time)
            last_time = now

        #process_waveform(tree.wfm)

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


            exo_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
            new_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))

            exo_wfm.SetSamplingFreq(25.0e6/CLHEP.second)
            #print exo_wfm.GetSamplingFreq()
            period =  exo_wfm.GetSamplingPeriod()
            
            # remove the baseline
            baseline_remover = EXOBaselineRemover()
            baseline_remover.SetBaselineSamples(100)
            baseline_remover.Transform(exo_wfm,exo_wfm)

            smoother = EXOSmoother()
            smoother.SetSmoothSize(5)
            smoother.Transform(exo_wfm,new_wfm)

            #max_val = exo_wfm.GetMaxValue()
            max_val = new_wfm.GetMaxValue() # smoothed max

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
            smoothed_max[i] = new_wfm.GetMaxValue()
            rise_time[i] = rise_time_calculator.GetRiseTime()
            rise_time_start[i] = rise_time_calculator.GetInitialThresholdCrossing()
            rise_time_stop[i] = rise_time_calculator.GetFinalThresholdCrossing()
            baseline_rms = baseline_remover.GetBaselineRMS()


            """
            trap_filter = EXOTrapezoidalFilter()
            trap_filter.SetFlatTime(1.0*CLHEP.microsecond)
            trap_filter.SetRampTime(1.0*CLHEP.microsecond)
            trap_filter.Transform(exo_wfm, new_wfm)
            """
         

            # pause
            if not gROOT.IsBatch() and smoothed_max[i] > 60 and channel[i] != 8:
            #if not gROOT.IsBatch():

                print "--> entry %i | channel %i" % (i_entry, channel[i])
                print "\t raw max %.2f" % wfm_max[i]
                print "\t smoothed max %.2f" % smoothed_max[i]
                print "\t rise time [microsecond]: %.3f" % (rise_time[i]/CLHEP.microsecond)
                print "\t rise start [microsecond]: %.2f" % (rise_time_start[i]*period/CLHEP.microsecond)
                print "\t rise stop [microsecond]: %.2f" % (rise_time_stop[i]*period/CLHEP.microsecond)
                print "\t baseline RMS: %.3f" % baseline_rms


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

    out_tree.Write()
    out_file.Close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)





