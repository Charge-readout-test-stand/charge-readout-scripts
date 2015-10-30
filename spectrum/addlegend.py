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
from ROOT import TF1


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import EXOWaveform


def process_file(filename):

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and get the histogram
    root_file = TFile(filename, "READ")
    decaytime = TH1D(root_file.Get("decay time"))
    
    # set up a canvas
    canvas = TCanvas("canvas","", 1700, 900)

    # fit with poisson distribution
    func = TF1("poisson", "[0]/[2]*TMath::Power([1]/[2],x/[2])*TMath::Exp(-[1]/[2])/TMath::Gamma(x/[2]+1)", 0, 50000)
    func.SetParameters(decaytime.Integral(), 15000, 5000)
    decaytime.Fit(func, "R")
    # print "chisquare = ", func.GetChisquare()
    # func = TF1("gaussian", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)", 0, 50000)
    # func.SetParameters(decaytime.Integral(), decaytime.GetMean(), decaytime.GetRMS())
    # decaytime.Fit(func, "R")
    
    decaytime.Draw()

    leg = TLegend(0.7, 0.8, 0.9, 0.9)
    leg.SetHeader("Mean = %d" % func.GetParameter(1))
    leg.AddEntry(decaytime, "channel%c" % basename[-1])
    leg.Draw()
    
    canvas.Update()
    canvas.Print("%s.png" % basename)
    raw_input("Press Enter to continue...")

    root_file.Close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



