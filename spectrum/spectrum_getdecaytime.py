#!/usr/bin/env python

"""
This script does a fit on the waveform to determine the decay time

See the script for settings of flat time and gap time (for maw)

The script will ask for a channel number and a threshold,
only waveforms in the specified channel and whose maw max is > threshold are included

For qualified waveforms, the script does a fit starting from 100 clockticks after
the maw max and uses exponential decay function:
    def expdecay(x, a, b):
        return a * np.exp(-x / b) + baseline
(the number of baseline samples is set in the script!)

The output of this script is a histogram of the fit parameter b (i.e. the decay time)
"""

import os
import sys
import glob

import numpy as np
from array import array
from scipy.optimize import curve_fit

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

    peaking_time = 50
    gap_time = 250
    trapFilter = EXOTrapezoidalFilter()
    trapFilter.SetFlatTime(peaking_time * 40 * CLHEP.nanosecond)
    trapFilter.SetRampTime(gap_time * 40 * CLHEP.nanosecond)
    trapFilter.SetDoNormalize()

    val = 0
    channel = 100

    baselineRemover = EXOBaselineRemover()
    

    while True:
        channel = input("Which channel (enter -1 to exit): ")
        if channel == -1:
            break

        threshold = input("Enter threshold: ")
    
        fithist = TH1D("decay time", "Decay Time", 500, 0.0, 50000.0)

        for i_entry in xrange(tree.GetEntries()):
            tree.GetEntry(i_entry)
            if tree.channel != channel:
                continue

            wfm = np.array(tree.wfm)

            sp = 10   # the step used when calculating the maw
            mawlen = (len(wfm) - 2*peaking_time - gap_time + 1) // sp  # length of the maw
            maw = np.zeros(mawlen)
            # mawplot = TGraph(mawlen)

            for j in xrange(mawlen):
                i = j * sp
                maw[j] = - np.mean(wfm[i:i+peaking_time]) + np.mean(wfm[i+peaking_time+gap_time:i+2*peaking_time+gap_time])
                # mawplot.SetPoint(j, j, maw[j])

            if np.amax(maw) < threshold:
                continue

            # print "maw_max = %d" % np.amax(maw)

            # canvas.Clear()
            # canvas.Divide(2,2)

            # pad = canvas.cd(1)
            # pad.SetGrid(1,1)

            # legend = TLegend(0.7, 0.92, 0.9, 0.99)
            # legend.AddEntry(tree, "channel %i" % tree.channel, "pl")
            # tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry, "l")
            # legend.Draw()

            # pad = canvas.cd(2)
            # pad.SetGrid(1,1)
            # mawplot.Draw("AL")

            ## number of baseline samples = 600
            baseline = np.mean(wfm[:600])  # assuming that the wfm will eventually decay onto the baseline

            def expdecay(x, a, b):
                return a * np.exp(-x / b) + baseline

            ## start fit at 100 points after the maw max
            fitstart = int(np.argmax(maw) * sp + peaking_time + gap_time + 100)
            
            fitlen = len(wfm) - fitstart
            if fitlen < 10:  ## if remaining length is < 10 then print out warning message and skip
                print "fitting length < 10!"
                continue

            # wfm = 0.5 * np.exp(-np.arange(len(wfm)) / 1000.) + 1 + np.random.normal(0., 0.05, len(wfm)) # test waveform

            tdata = np.arange(fitlen)

            a_guess = wfm[fitstart] - baseline  # making guesses for the fit
            b_guess = 200 / 0.04 # guess for decay time = 200 us
            popt, pcov = curve_fit(expdecay, tdata, wfm[fitstart:], p0 = [a_guess, b_guess])
            #print popt
            #print np.sqrt(np.diag(pcov))

            ## Show data with fit
            # pad = canvas.cd(3)
            # pad.SetGrid(1,1)
            # fitplot = TGraph(fitlen)
            # wfmplot = TGraph(fitlen)
            # for i in xrange(fitlen):
            #     fitplot.SetPoint(i, i, expdecay(i, popt[0], popt[1]))
            #     wfmplot.SetPoint(i, i, wfm[fitstart+i])
            # wfmplot.SetLineColor(1)
            # wfmplot.Draw("AL")
            # fitplot.SetLineColor(2)
            # fitplot.Draw("L")

            # canvas.Update()
            # val = raw_input("Enter q to stop drawing and select another channel: ")
            # if val == 'q':
            #     break

            fithist.Fill(popt[1]) # fill in the histogram


        canvas.Clear()
        fithist.Draw()
        canvas.Update()
        canvas.Print("%s_fit_maw_p%i_g%i_channel%i.png" % (basename, peaking_time, gap_time, channel))

        fitfile = TFile("%s_fit_maw_p%i_g%i_channel%i.root" % (basename, peaking_time, gap_time, channel), "RECREATE")
        fithist.Write()
        #fitfile.Close()

        raw_input("Press Enter to continue...")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



