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
    canvas = TCanvas("canvas","", 700, 900)

    # settings
    peaking_time = 50
    gap_time = 250
    channel = input("Channel = ? ")
    baseline_samples = 600
    clocktick = 40. * CLHEP.nanosecond
    decay_time = input("Decay time in microseconds = ? ") * 1.0 * CLHEP.microsecond
    threshold = input("Threshold = ? ")
    
    trapFilter = EXOTrapezoidalFilter()
    trapFilter.SetFlatTime(peaking_time * clocktick)
    trapFilter.SetRampTime(gap_time * clocktick)
    trapFilter.SetDoNormalize()

    baselineRemover = EXOBaselineRemover()
    
    spec = TH1D("spectrum", "Spectrum", 160, 0.0, 480.0)

    for i_entry in xrange(tree.GetEntries()):
        tree.GetEntry(i_entry)
        if tree.channel != channel:
            continue

        wfm = EXODoubleWaveform(array('d',tree.wfm), len(tree.wfm))
        wfm.SetSamplingPeriod(40 * CLHEP.nanosecond)
        baselineRemover.SetBaselineSamples(baseline_samples)            
        baselineRemover.Transform(wfm)

        trapFilter.SetDecayConstant(0)
        trapOut = EXODoubleWaveform()
        trapFilter.Transform(wfm, trapOut)

        if trapOut.GetMaxValue() >= threshold:
            spec.Fill(trapOut.GetMaxValue())

    legend = TLegend(0.6, 0.7, 0.9, 0.9)
    legend.AddEntry(spec, "channel%i" % channel)
            
    canvas.Clear()
    spec.Draw()
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_spec_trapezoid_p%i_g%i_channel%i.png" % (basename, peaking_time, gap_time, channel))

    specfile = TFile("%s_spec_trapezoid_p%i_g%i_channel%i.root" % (basename, peaking_time, gap_time, channel), "RECREATE")
    spec.Write()
    specfile.Close()

    raw_input("Press Enter to continue...")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



