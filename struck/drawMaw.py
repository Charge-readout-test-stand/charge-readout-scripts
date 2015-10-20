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

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    # set up a canvas
    canvas = TCanvas("canvas","", 700, 900)
    canvas.Divide(1,2)


    #maw_graph = TGraph()

    peaking_time = 4
    gap_time = 10

    for i_entry in xrange(tree.GetEntries()):
        tree.GetEntry(i_entry)

        #for i in xrange(tree.sample_length):
        #    print i_entry, i, tree.wfm[i], tree.maw[i]
        #    maw_graph.SetPoint(i, tree.maw[i])
        #graph.Draw("al")

        tree.SetLineColor(TColor.kBlue+1)

        pad = canvas.cd(1)
        pad.SetGrid(1,1)

        legend = TLegend(0.7, 0.92, 0.9, 0.99)
        legend.AddEntry(tree, "channel %i" % tree.channel, "pl")
        tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry, "l")
        legend.Draw()

        pad = canvas.cd(2)
        pad.SetGrid(1,1)
        tree.Draw("maw:Iteration$","Entry$==%i" % i_entry, "l")


        

        canvas.Update()
        val = raw_input("--> ch %i | press any key to continue (q to quit, p to print) " % tree.channel)
        if val == 'q': break
        if val == 'p':
            canvas.Update()
            canvas.Print("%s_event_%i.png" % (basename, i_entry))

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



