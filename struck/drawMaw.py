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


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(filename):

    # options
    channel = 0

    # maw options
    #gap_time = 30 # delay
    #peaking_time = 10 # length of moving average unit

    # gt 30, pt 10 seems ok for 250 MS/s
    # gt 30, pt 2 to 4 seems ok for 25 MS/s
    gap_time = 30 # delay
    peaking_time = 2 # length of moving average unit


    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree%i" % channel)
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries

    tree.SetLineWidth(2)

    # set up a canvas
    canvas = TCanvas("canvas","", 700, 900)
    canvas.Divide(1,3)


    i_entry = 0
    while i_entry < n_entries:

        tree.GetEntry(i_entry)

        try:
            channel = ord(tree.channel) # old versions
        except TypeError:
            channel = tree.channel
        print "entry %i, channel %i" % (i_entry, channel)
        #if channel != 9:
        #    i_entry+=1
        #    continue

        tree.SetLineColor(TColor.kBlue+1)

        pad = canvas.cd(1)
        pad.SetGrid(1,1)

        tree.SetMarkerStyle(8)
        tree.SetMarkerSize(0.8)

        legend = TLegend(0.7, 0.92, 0.9, 0.99)
        legend.AddEntry(tree, "channel %i" % channel, "pl")
        selection = "Entry$==%i" % i_entry
        #selection += " && Iteration$>165 && Iteration$<250"
        selection += " && Iteration$>120 && Iteration$<500"
        tree.Draw("wfm:Iteration$",selection, "lp")
        legend.Draw()

        # try to reconstruct the MAW:
        wfm = tree.wfm
        maw_graph = TGraph()
        maw_graph.SetLineWidth(2)
        maw_graph.SetLineColor(TColor.kRed)
        maw_graph.SetMarkerStyle(8)
        maw_graph.SetMarkerSize(0.8)
        ma1 = 0
        ma2 = 0 # delayed
        for i in xrange(tree.wfm_length):

            # construct ma1, the first "moving average sum"
            ma1 += wfm[i]
            j = i - peaking_time # remove old part of ma1
            if j < 0: j = 0
            ma1 -= wfm[j]

            # construct ma2, the 2nd "moving average sum"
            j = i - peaking_time - gap_time
            if j < 0: j = 0
            ma2 += wfm[j]
            j = i - peaking_time - gap_time - peaking_time
            if j < 0: j = 0
            ma2 -= wfm[j]

            maw_val = ma1 - ma2
            maw_graph.SetPoint(i, i, maw_val)
            #print "%i : ma1: %i | ma2: %i" % (i, ma1, ma2)
            # done building MAW


        pad = canvas.cd(2)
        pad.SetGrid(1,1)
        #tree.Draw("maw:Iteration$","Entry$==%i" % i_entry, "l")
        tree.Draw("maw:Iteration$",selection, "lp")
        maw_graph.Draw("l same")


        pad = canvas.cd(3)
        pad.SetGrid(1,1)
        maw_graph.Draw("al")

        canvas.Update()
        val = raw_input("--> entry %i | ch %i | enter to continue (q to quit, p to print, or entry number) " % (i_entry, channel))
        i_entry += 1

        if val == 'q': break
        if val == 'p':
            canvas.Update()
            canvas.Print("%s_entry_%i.png" % (basename, i_entry))
        try:
            i_entry = int(val)
        except: 
            pass


        #if i_entry > 2: break # debugging

    #legend.Draw()
    #canvas.Update()
    #canvas.Print("%s_spectrum.png" % basename)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



