#!/usr/bin/env python

"""
This script draws a spectrum from an NGM root tree. 

arguments [NGM sis tier1 root files]
"""

import os
import sys

import ROOT
#ROOT.gROOT.SetBatch(True)

ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       


def process_file(filename):

    # options
    #channel = 0

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
    root_file = ROOT.TFile(filename)
    tree = root_file.Get("HitTree")
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries

    tree.SetLineWidth(2)
    tree.SetLineColor(ROOT.kBlue+1)
    tree.SetMarkerStyle(8)
    tree.SetMarkerSize(0.8)

    # set up a canvas
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetGrid()

    i_entry = 0
    while i_entry < n_entries:
    #for i_entry in xrange(n_entries):

        tree.GetEntry(i_entry)

        channel =  tree.HitTree.GetChannel()
        gate_size = tree.HitTree.GetGateCount()
        #print tree.HitTree._channel
        #print tree._channel
        #channel = tree.HitTree._channel

        print "entry %i, channel %i" % (i_entry, channel)
        print "gate_size:", gate_size


        legend = ROOT.TLegend(0.7, 0.92, 0.9, 0.99)
        legend.AddEntry(tree, "channel %i" % channel, "pl")
        selection = "Entry$==%i" % i_entry
        #n_drawn = tree.Draw("_waveform:Iteration$",selection, "lp")
        n_drawn = tree.Draw("(_waveform-_waveform[0])*5000/pow(2,14):Iteration$",selection, "lp")
        legend.Draw()
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



