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

import struck_analysis_parameters

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(filename):

    print "processing file: ", filename

    sampling_freq_Hz = 25.0e6

    channels = struck_analysis_parameters.channels
    channel_map = struck_analysis_parameters.channel_map

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries

    # is this was created from tier1, branches like energy are just elements
    created_from_tier1 = False
    try:
        tree.GetEntry(0)
        tree.energy[1]
    except TypeError:
        created_from_tier1 = True

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)
    #canvas.SetLeftMargin(0.15)
    canvas.Divide(2,3)

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
        TColor.kMagenta,
    ]



    # set up some placeholder hists for the legend
    hists = []
    for (i, channel) in enumerate(channels):
        
        #print i, channel, channel_map[channel]
        hist = TH1D("hist%i" % channel,"",10,0,10)
        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack

        hist.SetLineColor(color)
        hist.SetFillColor(color)
        hists.append(hist)
        legend.AddEntry(hist, channel_map[channel],"fl")
    


    pave_texts = []
    for (i, channel) in enumerate(channels):
        pave_text = TPaveText(0.9, 0.8, 1.0, 1.0, "NDC")
        pave_text.SetFillColor(0)
        pave_text.SetFillStyle(0)
        pave_text.SetBorderSize(0)

        pave_text.AddText("%s" % channel_map[channel])
        pave_texts.append(pave_text)

    #tree.Draw("energy[4]","lightEnergy>700 && adc_max_time[5]*40.0/1000<10 &&
    #energy[4]>200")

    selections = [
        #"lightEnergy>700", # keep the light threshold high (some runs had low thresholds)
        #"adc_max_time[5]*40.0/1000<10", # light signal is within 10 microseconds of trigger
    ]

    for (i, channel) in enumerate(channels):

        if channel == 8: index = 6
        print "%i | channel %i | %s " % (i, channel, channel_map[channel])
        draw_command = "energy"
        #draw_command = "(adc_max_time - trigger_time)*40.0/1000"
        print "\t draw command: %s" % draw_command

        extra_selections = [
            "channel==%i" % channel,
            #"energy > 300" % index,
            #"(adc_max_time - adc_max_time[5])*40.0/1000 < 15"
        ]
        selection = " && ".join(selections + extra_selections)
        print "\t selection: %s" % selection

        options = "same"
        if i  == 0: options = ""
        print "\t options: %s" % options


        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack
        tree.SetLineColor(color)



        #pad = canvas.cd(i+1)
        #pad.SetGrid(1,1)
        #pad.SetLogy(1)
        #pad.SetBottomMargin(0.01)
        #pad.SetTopMargin(0.01)
        #pad.SetLeftMargin(0.05)
        #pad.SetRightMargin(0.001)

        n_entries = tree.Draw(draw_command, selection, options)
        #pave_texts[i].Draw()
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



