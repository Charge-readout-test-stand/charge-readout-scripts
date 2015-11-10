#!/usr/bin/env python

"""
Run this script to determine the decay time in each channel
It runs on a tier1_root_file containing raw wfms, most of which should contain a clear signal

gap_time (= 250 clockticks) and peaking_time (= 50 clockticks) are set at the beginning of the script

In TEST MODE, the script lets you to look at individual wfms for each channel.
Use this mode to determine the range of scan for WORK MODE.

In WORK MODE:
-- First, the script calculates, for each wfm, the average of the tail after trapezoidal filter
   for different decay times. The results are saved in a "..._trapezoidtest_p%i_g%i_values.root" file
-- Then, the script reads from the file and calculated the average value for each channel.
   The results are saved as graphs in a "..._trapezoidtest_p%i_g%i.root" file
(The intermediate file is used to prevent memory leak)

Warning: may take a long time to run. Use test mode first to set up parameters,
and run work mode as batch job.

List of paramters (and current values):
peaking_time = 50 (clockticks)
gap_time = 250 (clockticks)
clocktick = 40 * CLHEP.nanosecond
baselineSamples = 600
tauMin = 100. (us)
tauMax = 1500. (us)
tauSteps = 50
tailSamples = 100 (for averaging)
"""

import os
import sys
import glob

import numpy as np
from array import array

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TMath
from ROOT import TTree


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import EXODoubleWaveform
from ROOT import EXOBaselineRemover
from ROOT import EXOTrapezoidalFilter
from ROOT import CLHEP


def process_file(filename):

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    # set up flat time and ramp time
    peaking_time = 50
    gap_time = 250
    clocktick = 40. * CLHEP.nanosecond
    trapFilter = EXOTrapezoidalFilter()
    trapFilter.SetFlatTime(gap_time * clocktick)
    trapFilter.SetRampTime(peaking_time * clocktick)
    trapFilter.SetDoNormalize()

    val = 0
    baselineRemover = EXOBaselineRemover()

    ####################### TEST MODE ########################
    ### Uncomment this block to look at one wfm at a time  ###
    ### for different decay times. Use this to determine   ###
    ### the range of scan in the next step.                ###
    ##########################################################
    # set up a canvas
    # canvas = TCanvas("canvas","", 1700, 900)

    # channel = 100
    # while True:
    #     channel = input("Which channel (enter -1 to exit): ")
    #     if channel == -1:
    #         break

    #     threshold = input("Enter threshold: ")

    #     for i_entry in xrange(tree.GetEntries()):
    #         tree.GetEntry(i_entry)
    #         if tree.channel != channel:
    #             continue

    #         wfm = np.array(tree.wfm)

    #         ## calculate and draw maw for comparison
    #         mawlen = len(wfm) - 2*peaking_time - gap_time + 1
    #         maw = np.zeros(mawlen)
    #         mawplot = TGraph(mawlen)

    #         for i in xrange(mawlen):
    #             maw[i] = - np.mean(wfm[i:i+peaking_time]) + np.mean(wfm[i+peaking_time+gap_time:i+2*peaking_time+gap_time])
    #             mawplot.SetPoint(i, i, maw[i])

    #         if np.amax(maw) < threshold:
    #             continue

    #         canvas.Clear()
    #         canvas.Divide(4,2)

    #         pad = canvas.cd(1)
    #         pad.SetGrid(1,1)

    #         legend1 = TLegend(0.6, 0.8, 0.9, 0.99)
    #         legend1.AddEntry(tree, "channel %i" % tree.channel, "pl")
    #         tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry, "l")
    #         legend1.Draw()

    #         pad = canvas.cd(2)
    #         pad.SetGrid(1,1)
    #         mawplot.Draw("AL")

    #         wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
    #         wfm.SetSamplingPeriod(40 * CLHEP.nanosecond)
    #         canvas.Update()
    #         baselineSamples = input("Enter number of baseline samples: ")
    #         baselineRemover.SetBaselineSamples(baselineSamples)            
    #         print "baseline = %d, RMS = %d" % (baselineRemover.GetBaseline(wfm), baselineRemover.GetBaselineRMS(wfm))

    #         baselineRemover.Transform(wfm)

    #         #take tau = infinity
    #         trapFilter.SetDecayConstant(0)
    #         trapOut = EXODoubleWaveform()
    #         trapFilter.Transform(wfm, trapOut)

    #         pad = canvas.cd(3)
    #         pad.SetGrid(1,1)
    #         hist2 = TH1D()
    #         trapOut.LoadIntoHist(hist2)
    #         hist2.Draw()
    #         legend2 = TLegend(0.6, 0.8, 0.9, 0.99)
    #         legend2.SetHeader("tau = inf, max = %d" % trapOut.GetMaxValue())
    #         legend2.Draw()

    #         # take tau = 15000 clockticks
    #         tau = 18079 * clocktick
    #         trapFilter.SetDecayConstant(tau)
    #         trapFilter.Transform(wfm, trapOut)

    #         pad = canvas.cd(4)
    #         pad.SetGrid(1,1)
    #         hist3 = TH1D()
    #         trapOut.LoadIntoHist(hist3)
    #         hist3.Draw()
    #         legend3 = TLegend(0.6, 0.8, 0.9, 0.99)
    #         legend3.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
    #         legend3.Draw()

    #         # take tau = 400 microseconds
    #         tau = 400 * CLHEP.microsecond
    #         trapFilter.SetDecayConstant(tau)
    #         trapFilter.Transform(wfm, trapOut)

    #         pad = canvas.cd(5)
    #         pad.SetGrid(1,1)
    #         hist4 = TH1D()
    #         trapOut.LoadIntoHist(hist4)
    #         hist4.Draw()
    #         legend4 = TLegend(0.6, 0.8, 0.9, 0.99)
    #         legend4.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
    #         legend4.Draw()

    #         # take tau = 200 microseconds
    #         tau = 200 * CLHEP.microsecond
    #         trapFilter.SetDecayConstant(tau)
    #         trapFilter.Transform(wfm, trapOut)

    #         pad = canvas.cd(6)
    #         pad.SetGrid(1,1)
    #         hist5 = TH1D()
    #         trapOut.LoadIntoHist(hist5)
    #         hist5.Draw()
    #         legend5 = TLegend(0.6, 0.8, 0.9, 0.99)
    #         legend5.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
    #         legend5.Draw()

    #         # take tau = 50 microseconds
    #         tau = 50 * CLHEP.microsecond
    #         trapFilter.SetDecayConstant(tau)
    #         trapFilter.Transform(wfm, trapOut)

    #         pad = canvas.cd(7)
    #         pad.SetGrid(1,1)
    #         hist6 = TH1D()
    #         trapOut.LoadIntoHist(hist6)
    #         hist6.Draw()
    #         legend6 = TLegend(0.6, 0.8, 0.9, 0.99)
    #         legend6.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
    #         legend6.Draw()

    #         canvas.Update()
    #         val = raw_input("Enter p to print, s to change channel, q to go to the next step: ")
    #         if val == 'p':
    #             canvas.Print("Entry_%i.png" % i_entry)
    #         elif val == 'q' or val == 's':
    #             break

    #     if val == 'q':
    #         break
    
    ################### END OF TEST MODE #######################


    ############################### WORK MODE ############################

    ## Paramters: please set up before running as batch job
    baselineSamples = 600 #input("Enter number of baseline samples:  ")
    baselineRemover.SetBaselineSamples(baselineSamples)

    tauMin = 100. #float(input("Enter min decay time (in microseconds): "))
    tauMax = 1500. #float(input("Enter max decay time (in microseconds): "))
    tauSteps = 50 #int(input("Enter number of steps for decay time test: "))
    tauArray = np.linspace(tauMin, tauMax, tauSteps)

    tailSamples = 100 #int(input("Enter time length on tail (in microseconds): ") / 0.04)

    fout = TFile("%s_trapezoidtest_p%i_g%i_values.root" % (basename, peaking_time, gap_time), "RECREATE")
    treeout = TTree("tree", "%s trapzoidal test values" % basename)

    channel = array('I', [0])
    treeout.Branch("channel", channel, "channel/i")

    values = array('d', [0]*tauSteps) # for each wfm, array of avg tail value for different tau
    treeout.Branch("values", values, "values[%i]/D" % tauSteps)

    trapOut = EXODoubleWaveform()
    
    for i_entry in xrange(tree.GetEntries()):
        tree.GetEntry(i_entry)

        channel[0] = tree.channel

        wfm = EXODoubleWaveform(array('d',tree.wfm), len(tree.wfm))
        wfm.SetSamplingPeriod(40 * CLHEP.nanosecond)
        baselineRemover.Transform(wfm)

        for i in xrange(tauSteps):
            tau = tauArray[i]
            trapFilter.SetDecayConstant(tau * CLHEP.microsecond)
            trapFilter.Transform(wfm, trapOut)

            # if trapOut.GetMinValue() < -5:
            #     canvas.Clear()
            #     wfm.GimmeHist().Draw()
            #     canvas.Update()
            #     val = raw_input("Trapezoidal output min value = %f, max value = %f; include this waveform? " % (trapOut.GetMinValue(), trapOut.GetMaxValue()))
            #     if val != 'y':
            #         continue

            # if trapOut.GetMinValue() < -20 or - trapOut.GetMaxValue() / trapOut.GetMinValue() < 20:
            #     continue

            trapOutLen = trapOut.GetLength()
            values[i] = trapOut.Sum(trapOutLen - tailSamples, trapOutLen) * 1.0 / tailSamples

            # canvas.Clear()
            # trapOut.GimmeHist().Draw()
            # canvas.Update()
            # print tailAvg[-1]
            # raw_input("Press Enter to continue...")

        treeout.Fill()

    print "Done processing values"
    treeout.Write()
    fout.Close()

    fin = TFile("%s_trapezoidtest_p%i_g%i_values.root" % (basename, peaking_time, gap_time), "READ")
    tree = fin.Get("tree")
    fout = TFile("%s_trapezoidtest_p%i_g%i.root" % (basename, peaking_time, gap_time), "RECREATE")
    
    for channel in [0,1,2,3,4]:
        graph = TGraph(tauSteps)
        graph.SetTitle("channel%i" % channel)
        
        tailAvg = np.zeros((0, tauSteps))        
        for i_entry in xrange(tree.GetEntries()):
            tree.GetEntry(i_entry)
            if tree.channel == channel:
                tailAvg = np.vstack((tailAvg, tree.values))
        tailAvg = np.ndarray.mean(tailAvg,0)
        
        for i in xrange(tauSteps):
            graph.SetPoint(i, tauArray[i], tailAvg[i])

        graph.Write()

    print "Done processing graphs"
    fout.Close()
    

    ########################### END OF WORK MODE ##################################

            
    


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



