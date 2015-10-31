#!/usr/bin/env python

"""
This script draws a histogram for the ratio between 
height (= avg of last 100 entries of wfm - avg of first 100 entries of wfm)
and the maximum after the trapezoidal filter

To use it:
python <this script> <root file>

The script will ask for the channel#, flat time, gap time, and decay time
for the trapezoidal filter

Number of baseline samples = 100
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
    canvas = TCanvas("canvas","", 900, 900)

    channel = input("Which channel? ")
    peaking_time = input("Flat time = ? (in clockticks) ")
    gap_time = input("Gap time = ? (in clockticks) ")
    tau = input("Decay time = ? (in microseconds) ")
    baselineSamples = 100
    
    clocktick = 40. * CLHEP.nanosecond
    trapFilter = EXOTrapezoidalFilter()
    trapFilter.SetFlatTime(peaking_time * clocktick)
    trapFilter.SetRampTime(gap_time * clocktick)
    trapFilter.SetDoNormalize()
    trapFilter.SetDecayConstant(tau * CLHEP.microsecond)

    baselineRemover = EXOBaselineRemover()
    baselineRemover.SetBaselineSamples(baselineSamples)            

    hist = TH1D("ratio", "height over trapMax", 200, 0.0, 2.0)

    for i_entry in xrange(tree.GetEntries()):
        tree.GetEntry(i_entry)
        if tree.channel != channel:
            continue

        wfm = array('d', tree.wfm)
        height = (sum(wfm[-100:]) - sum(wfm[:100])) / 100.

        wfm = EXODoubleWaveform(wfm, len(wfm))
        wfm.SetSamplingPeriod(40 * CLHEP.nanosecond)
        baselineRemover.Transform(wfm)

        trapOut = EXODoubleWaveform()
        trapFilter.Transform(wfm, trapOut)

        hist.Fill(height / trapOut.GetMaxValue())


    canvas.Clear()
    hist.Draw()

    legend = TLegend(0.6, 0.7, 0.9, 0.9)
    legend.SetHeader("Mean = %f, RMS = %f" % (hist.GetMean(), hist.GetRMS()))
    legend.AddEntry(hist,"channel %i" % channel)
    legend.Draw()
    
    canvas.Update()
    #canvas.Print("%s_ratio__p%i_g%i_channel%i.png" % (basename, peaking_time, gap_time, channel))

    #fout = TFile("%s_ratio_p%i_g%i_channel%i.root" % (basename, peaking_time, gap_time, channel), "RECREATE")
    #hist.Write()
    #fout.Close()

    raw_input("Press Enter to continue...")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



