#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* max
* channel

arguments [sis root files]
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

    # set up a canvas
    canvas = TCanvas("canvas","", 1700, 900)

    peaking_time = 50
    gap_time = 250
    clocktick = 40. * CLHEP.nanosecond
    trapFilter = EXOTrapezoidalFilter()
    trapFilter.SetFlatTime(peaking_time * clocktick)
    trapFilter.SetRampTime(gap_time * clocktick)
    trapFilter.SetDoNormalize()

    val = 0
    channel = 100

    baselineRemover = EXOBaselineRemover()
    

    while True:
        channel = input("Which channel (enter -1 to exit): ")
        if channel == -1:
            break

        threshold = input("Enter threshold: ")
    
        spec = TH1D("spectrum", "Spectrum", 500, 0.0, 500.0)

        for i_entry in xrange(tree.GetEntries()):
            tree.GetEntry(i_entry)
            if tree.channel != channel:
                continue

            wfm = np.array(tree.wfm)

            mawlen = len(wfm) - 2*peaking_time - gap_time + 1
            maw = np.zeros(mawlen)
            mawplot = TGraph(mawlen)

            for i in xrange(mawlen):
                maw[i] = - np.mean(wfm[i:i+peaking_time]) + np.mean(wfm[i+peaking_time+gap_time:i+2*peaking_time+gap_time])
                mawplot.SetPoint(i, i, maw[i])

            if np.amax(maw) < threshold:
                continue

            canvas.Clear()
            canvas.Divide(4,2)

            pad = canvas.cd(1)
            pad.SetGrid(1,1)

            legend1 = TLegend(0.6, 0.8, 0.9, 0.99)
            legend1.AddEntry(tree, "channel %i" % tree.channel, "pl")
            tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry, "l")
            legend1.Draw()

            pad = canvas.cd(2)
            pad.SetGrid(1,1)
            mawplot.Draw("AL")

            wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
            wfm.SetSamplingPeriod(40 * CLHEP.nanosecond)
            baselineSamples = input("Enter number of baseline samples: ")
            baselineRemover.SetBaselineSamples(baselineSamples)            
            print "baseline = %d, RMS = %d" % (baselineRemover.GetBaseline(wfm), baselineRemover.GetBaselineRMS(wfm))

            baselineRemover.Transform(wfm)

            #take tau = infinity
            trapFilter.SetDecayConstant(0)
            trapOut = EXODoubleWaveform()
            trapFilter.Transform(wfm, trapOut)

            pad = canvas.cd(3)
            pad.SetGrid(1,1)
            hist2 = TH1D()
            trapOut.LoadIntoHist(hist2)
            hist2.Draw()
            legend2 = TLegend(0.6, 0.8, 0.9, 0.99)
            legend2.AddEntry(tree, "channel %i" % tree.channel, "pl")
            legend2.SetHeader("tau = inf, max = %d" % trapOut.GetMaxValue())
            legend2.Draw()

            # take tau = 15000 clockticks
            tau = 18079 * clocktick
            trapFilter.SetDecayConstant(tau)
            trapFilter.Transform(wfm, trapOut)

            pad = canvas.cd(4)
            pad.SetGrid(1,1)
            hist3 = TH1D()
            trapOut.LoadIntoHist(hist3)
            hist3.Draw()
            legend3 = TLegend(0.6, 0.8, 0.9, 0.99)
            legend3.AddEntry(tree, "channel %i" % tree.channel, "pl")
            legend3.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
            legend3.Draw()

            # take tau = 200 microseconds
            tau = 200 * CLHEP.microsecond
            trapFilter.SetDecayConstant(tau)
            trapFilter.Transform(wfm, trapOut)

            pad = canvas.cd(5)
            pad.SetGrid(1,1)
            hist4 = TH1D()
            trapOut.LoadIntoHist(hist4)
            hist4.Draw()
            legend4 = TLegend(0.6, 0.8, 0.9, 0.99)
            legend4.AddEntry(tree, "channel %i" % tree.channel, "pl")
            legend4.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
            legend4.Draw()

            # take tau = 20 microseconds
            tau = 20 * CLHEP.microsecond
            trapFilter.SetDecayConstant(tau)
            trapFilter.Transform(wfm, trapOut)

            pad = canvas.cd(6)
            pad.SetGrid(1,1)
            hist5 = TH1D()
            trapOut.LoadIntoHist(hist5)
            hist5.Draw()
            legend5 = TLegend(0.6, 0.8, 0.9, 0.99)
            legend5.AddEntry(tree, "channel %i" % tree.channel, "pl")
            legend5.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
            legend5.Draw()

            # take tau = 400 microseconds
            tau = 400 * CLHEP.microsecond
            trapFilter.SetDecayConstant(tau)
            trapFilter.Transform(wfm, trapOut)

            pad = canvas.cd(7)
            pad.SetGrid(1,1)
            hist6 = TH1D()
            trapOut.LoadIntoHist(hist6)
            hist6.Draw()
            legend6 = TLegend(0.6, 0.8, 0.9, 0.99)
            legend6.AddEntry(tree, "channel %i" % tree.channel, "pl")
            legend6.SetHeader("tau = %d us, max = %d" % (tau/CLHEP.microsecond, trapOut.GetMaxValue()))
            legend6.Draw()

            canvas.Update()
            val = raw_input("Enter p to print, q to stop drawing and select another channel: ")
            if val == 'p':
                canvas.Print("Entry_%i.png" % i_entry)
            elif val == 'q':
                break

            spec.Fill(np.amax(maw))


        #canvas.Clear()
        #spec.Draw()
        #canvas.Update()
        #canvas.Print("%s_spec_maw_p%i_g%i_channel%i.png" % (basename, peaking_time, gap_time, channel))

        #specfile = TFile("%s_spec_maw_p%i_g%i_channel%i.root" % (basename, peaking_time, gap_time, channel), "RECREATE")
        #spec.Write()
        #specfile.Close()

        raw_input("Press Enter to continue...")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



