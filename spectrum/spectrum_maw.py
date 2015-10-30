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

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    # set up a canvas
    canvas = TCanvas("canvas","", 700, 900)
    canvas.Divide(2,2)


    #maw_graph = TGraph()

    peaking_time = 50
    gap_time = 250

    # for i_entry in xrange(tree.GetEntries()):
    #     tree.GetEntry(i_entry)

    #     #for i in xrange(tree.sample_length):
    #     #    print i_entry, i, tree.wfm[i], tree.maw[i]
    #     #    maw_graph.SetPoint(i, tree.maw[i])
    #     #graph.Draw("al")

    #     tree.SetLineColor(TColor.kBlue+1)

    #     pad = canvas.cd(1)
    #     pad.SetGrid(1,1)

    #     legend = TLegend(0.7, 0.92, 0.9, 0.99)
    #     legend.AddEntry(tree, "channel %i" % tree.channel, "pl")
    #     tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry, "l")
    #     legend.Draw()

    #     pad = canvas.cd(2)
    #     pad.SetGrid(1,1)
    #     tree.Draw("maw:Iteration$","Entry$==%i" % i_entry, "l")

    #     #waveform = EXOWaveform(tree.wfm[0], tree.sample_length)
    #     #waveform.GimmeHist().Draw()
        

    #     #canvas.Update()
    #     print "adc_max = %d, adc_min = %d, maw_max = %d, maw_min = %d" % (tree.adc_max, tree.adc_min, tree.maw_max, tree.maw_min) 
    #     val = raw_input("--> ch %i | press any key to continue (q to quit, p to print) " % tree.channel)
    #     if val == 'q': break
    #     if val == 'p':
    #         canvas.Update()
    #         canvas.Print("%s_entry_%i.png" % (basename, i_entry))

    #     #if i_entry > 2: break # debugging

    # #legend.Draw()
    # #canvas.Update()
    # #canvas.Print("%s_spectrum.png" % basename)

    val = 0
    channel = 100

    while True:
        channel = input("Which channel (enter -1 to exit): ")
        if channel == -1:
            break
    
        spec = TH1D("spectrum", "Spectrum", 500, 0.0, 500.0)

        for i_entry in xrange(tree.GetEntries()):
            tree.GetEntry(i_entry)
            if tree.channel != channel:
                continue

            wfm = np.array(tree.wfm)

            mawlen = len(wfm) - 2*peaking_time - gap_time + 1
            maw = np.zeros(mawlen)
            #mawplot = TGraph(mawlen)

            for i in range(mawlen):
                maw[i] = - np.mean(wfm[i:i+peaking_time]) + np.mean(wfm[i+peaking_time+gap_time:i+2*peaking_time+gap_time])
                #mawplot.SetPoint(i, i, maw[i])

            if val != 'q':
                print "maw_max = %d" % np.amax(maw)

                pad = canvas.cd(1)
                pad.SetGrid(1,1)

                legend = TLegend(0.7, 0.92, 0.9, 0.99)
                legend.AddEntry(tree, "channel %i" % tree.channel, "pl")
                tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry, "l")
                legend.Draw()

                pad = canvas.cd(2)
                pad.SetGrid(1,1)
                tree.Draw("maw:Iteration$","Entry$==%i" % i_entry, "l")

                pad = canvas.cd(3)
                pad.SetGrid(1,1)
                #mawplot.Draw("AL")

                canvas.Update()
                val = raw_input("Press q to stop drawing: ")

            spec.Fill(np.amax(maw))


        canvas.Clear()
        spec.Draw()
        canvas.Update()
        canvas.Print("%s_spec_maw_p%i_g%i_channel%i.png" % (basename, peaking_time, gap_time, channel))

        specfile = TFile("%s_spec_maw_p%i_g%i_channel%i.root" % (basename, peaking_time, gap_time, channel), "RECREATE")
        spec.Write()
        specfile.Close()
        raw_input("Press any key to continue...")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



