#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* totalEnergy
* energy
* nHits

arguments [sis tier 3 root files of events]
"""

import os
import sys
import math

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



def setup_hist(hist, color):
    """
    Set color, line and marker style of hist
    """

    hist.SetLineColor(color)
    hist.SetMarkerStyle(8)
    hist.SetMarkerSize(1.5)
    hist.SetMarkerColor(color)
    hist.SetLineWidth(2)
    #hist.SetFillColor(color)


def process_file(filename):

    print "processing file: ", filename

    #-------------------------------------------------------------------------------
    # options

    min_bin = 0
    max_bin = 2500
    bin_width = 10
    n_bins = int(math.floor(max_bin*1.0 / bin_width))

    #-------------------------------------------------------------------------------

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz
    channels = struck_analysis_parameters.channels
    channel_map = struck_analysis_parameters.channel_map
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use

    colors = [
        TColor.kBlue, 
        TColor.kGreen+2, 
        TColor.kViolet+1,
        TColor.kRed, 
        TColor.kOrange+1,
        TColor.kMagenta,
    ]

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



    # set up some hists to hold TTree::Draw results
    hists = []
    
    selections = [
        #"lightEnergy>700", # keep the light threshold high (some runs had low thresholds)
        #"adc_max_time[5]*40.0/1000<10", # light signal is within 10 microseconds of trigger
        #"is_amplified",
        #"energy>100",
        #"energy[5]>15",
        #"rise_time_stop-trigger_time <15",
        #"rise_time_stop-trigger_time >5"
    ]

    frame_hist = TH1D("frame_hist","",n_bins,min_bin,max_bin)
    frame_hist.SetLineWidth(2)
    frame_hist.SetXTitle("Energy [keV]")
    frame_hist.SetYTitle("Counts / %.1f keV" % frame_hist.GetBinWidth(1))
    frame_hist.SetMinimum(0.5)
    tree.Draw("")
    selection = " && ".join(selections)

    print "%i entries in sum hist" % tree.Draw("chargeEnergy >> frame_hist", selection)
    setup_hist(frame_hist, TColor.kBlack)
    legend.AddEntry(frame_hist, "sum","lp")


    y_max = 0
    for (channel, value) in enumerate(charge_channels_to_use):

        if not value:
            continue
 
        hist = TH1D("hist%i" % channel,"",n_bins,min_bin,max_bin)
        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack
        
        setup_hist(hist, color)
        hists.append(hist)
        legend.AddEntry(hist, channel_map[channel],"pl")

        print "channel %i | %s " % (channel, channel_map[channel])
        draw_command = "energy1_pz >> %s" % hist.GetName()
        print "\t draw command: %s" % draw_command

        extra_selections = [
            "channel == %i" % channel,
            #"energy > 0",
            #"(rise_time_stop95 - trigger_time) >6",
            #"(adc_max_time - adc_max_time[5])*40.0/1000 < 15"
        ]
        selection = " && ".join(selections + extra_selections)
        print "\t selection: %s" % selection

        options = "same"
        print "\t options: %s" % options


        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack
        tree.SetLineColor(color)

   

        n_entries = tree.Draw(draw_command, selection, options)
        if y_max < hist.GetMaximum(): y_max = hist.GetMaximum()
        print "\t %i entries" % n_entries

    legend.Draw()
    #frame_hist.SetMaximum(y_max)
    canvas.Update()

    canvas.Update()
    canvas.Print("%s_test.png" % (basename))
    canvas.Print("%s_test.pdf" % (basename))

    val = raw_input("--> enter to continue (q to quit) ")
    if val == 'q': 
        sys.exit()



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



