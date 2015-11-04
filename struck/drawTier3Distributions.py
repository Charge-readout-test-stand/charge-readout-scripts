#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* totalEnergy
* energy
* nHits

arguments [sis tier 2 root files of events]
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
from ROOT import TH1D
from ROOT import TH2D


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(filename):

    print "processing file: ", filename

    sampling_freq_Hz = 25.0e6

    min_bin = 0
    max_bin = 2000

    channels = [
      0,1,2,3,4,
      #8, 
    ]

    channel_map = {}
    channel_map[0] = "X26"
    channel_map[1] = "X27"
    channel_map[2] = "X29"
    channel_map[3] = "Y23"
    channel_map[4] = "Y24"
    channel_map[8] = "PMT"

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries

    # decide if this is a tier1 or tier2 file
    is_tier1 = False
    try:
        tree.GetEntry(0)
        tree.wfm0
        print "this is a tier2 file"
    except AttributeError:
        print "this is a tier1 file"
        n_channels = 1
        is_tier1 = True

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)
    #canvas.SetLeftMargin(0.15)

    tree.SetLineColor(TColor.kBlue+1)
    #tree.SetFillColor(TColor.kBlue+1)
    #tree.SetFillStyle(3004)
    tree.SetLineWidth(2)

    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(len(channels))


    colors = [
        TColor.kBlue, 
        TColor.kGreen+2, 
        TColor.kViolet+1,
        TColor.kRed, 
        TColor.kOrange+1,
    ]



    # set up some placeholder hists for the legend
    hists = []
    for (i, channel) in enumerate(channels):
        
        #print i, channel, channel_map[channel]
        hist = TH1D("hist%i" % channel,"",500,0,2000)
        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack

        hist.SetLineColor(color)
        hist.SetFillColor(color)
        hists.append(hist)
        legend.AddEntry(hist, channel_map[channel],"f")


    #tree.Draw("energy[4]","lightEnergy>700 && adc_max_time[5]*40.0/1000<10 &&
    #energy[4]>200")

    selections = [
        #"lightEnergy>700", # keep the light threshold high (some runs had low thresholds)
        #"adc_max_time[5]*40.0/1000<10", # light signal is within 10 microseconds of trigger
        "is_amplified",
    ]

    #min_val = tree.GetMinimum("energy")
    #max_val = tree.GetMaximum("energy")
    #print min_val, max_val

    #frame_hist = TH1D("frame_hist","",100,-5,10.0) # unamplified
    #frame_hist = TH1D("frame_hist","",200,-30,40) # amplified
    #frame_hist = TH1D("frame_hist","",100,-2,2) # pulser
    #tree.Draw("energy >> frame_hist","channel!=8")
    frame_hist = TH1D("frame_hist","",n_bins,min_bin,max_bin)
    frame_hist.SetXTitle("Energy")
    frame_hist.SetYTitle("Counts / %.1f" % frame_hist.GetBinWidth(1))
    frame_hist.SetMaximum(n_entries)
    frame_hist.SetMinimum(0.1)
    frame_hist.Draw()

    for (i, channel) in enumerate(channels):

        index = channel
        if channel == 8: index = 5
        print "%i | channel %i | %s " % (i, channel, channel_map[channel])
        draw_command = "energy"
        #draw_command = "(adc_max_time[%i] - adc_max_time[5])*40.0/1000" % index
        print "\t draw command: %s" % draw_command

        extra_selections = [
            "channel == %i" % channel,
            #"energy[%i] > 0" % index,
            #"(rise_time_stop[%i] - rise_time_start[5]) >6" % index,
            #"(adc_max_time[%i] - adc_max_time[5])*40.0/1000 < 15" % i
        ]
        selection = " && ".join(selections + extra_selections)
        print "\t selection: %s" % selection

        options = "same"
        #if i  == 0: options = ""
        print "\t options: %s" % options


        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack
        tree.SetLineColor(color)

        n_entries = tree.Draw(draw_command, selection, options)
        print "\t %i entries" % n_entries

    legend.Draw()
    canvas.Update()

    val = raw_input("--> enter to continue (q to quit, p to print) ")

    if val == 'q': return
    if val == 'p':
        canvas.Update()
        canvas.Print("%s_test.png" % (basename))



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



