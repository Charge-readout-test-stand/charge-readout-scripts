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

title_size = gStyle.GetTitleSize()
gStyle.SetTitleSize(title_size*10.0)
label_size = gStyle.GetLabelSize("Y")
gStyle.SetLabelSize(label_size*4.0,"Y")

def print_tier2_info(tree, sampling_freq_Hz=25.0e6):

    print "\t time stamp: %.2f" % (tree.time_stamp/sampling_freq_Hz)
    print "\t charge energy: %i" % tree.chargeEnergy
    print "\t light energy: %i" % tree.lightEnergy

    for i in xrange(6):
        print "\t ch %i | energy %i | maw max %i | max time [us]: %.2f" % (
            tree.channel[i],
            tree.energy[i],
            tree.maw_max[i],
            tree.adc_max_time[i]/sampling_freq_Hz*1e6,
        )

def process_file(filename):

    sampling_freq_Hz = 25.0e6

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    #canvas.SetLeftMargin(0.15)
    canvas.Divide(1,6)

    channels = [
      0,1,2,3,4,
      8, 
    ]
    channel_map = {}
    channel_map[0] = "X26"
    channel_map[1] = "X27"
    channel_map[2] = "X29"
    channel_map[3] = "Y23"
    channel_map[4] = "Y24"
    channel_map[8] = "PMT"

    frame_hist = TH1D("hist", "", 100, 0, 21)
    frame_hist.SetLineColor(TColor.kWhite)
    frame_hist.SetXTitle("Time [#mus]")
    frame_hist.SetYTitle("ADC units")
    frame_hist.GetYaxis().SetTitleOffset(1.5)
    frame_hist.SetBinContent(1, pow(2,14))

    tree.SetLineWidth(2)
    pave_text = TPaveText(0.9, 0.0, 1.0, 0.6, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)

    colors = [
        TColor.kBlue, 
        TColor.kGreen+2, 
        TColor.kViolet+1,
        TColor.kRed, 
        TColor.kOrange+1,
    ]

    legend = TLegend(0.15, 0.91, 0.9, 0.99)
    legend.SetNColumns(len(channels))

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
    
    legend.Draw()
    # loop over all events in file
    i_entry = 0
    while i_entry < n_entries:

        tree.GetEntry(i_entry)

        threshold = 200
        #threshold = 50 # ok for unshaped, unamplified data
       

        # test whether any charge channel is above threshold
        #n_above_threshold = 0
        #for i in xrange(5): 
        #    if tree.energy[i] > threshold: n_above_threshold += 1
        #if n_above_threshold == 0:
        #    i_entry += 1
        #    continue

        # use total charge energy:
        #if tree.chargeEnergy<100: 
        #    i_entry+= 1
        #    continue
        #frame_hist.Draw()


        print "==> entry %i of %i | charge energy: %i" % (
            i_entry, 
            n_entries,
            tree.chargeEnergy,
        )


        adc_max = 0
        adc_min = pow(2,14)

        print_tier2_info(tree)

        # loop over all channels in the event:
        for (i, channel) in enumerate(channels):

            #print "\t %i | channel %i" % (i, channel)

            #options = "l same"
            options = "l"
            #if i == 0:
            #    if channel == 8:
            #        options = "l"
            #    else:
            #        frame_hist.Draw()
            #print options


            # find range of charge channels:
            #if channel < 5:

                # FIXME -- save wfm max in tree:
                #for index in tree.sample_length:
                #    if tree. > adc_max: adc_max = tree.adc_max[channel]
                #    if tree.adc_min[channel] < adc_min: adc_min = tree.adc_min[channel]


            try:
                color = colors[channel]
            except IndexError:
                color = TColor.kBlack

            tree.SetLineColor(color)
            pad = canvas.cd(i+1)
            pad.SetGrid(1,1)
            pad.SetBottomMargin(0.01)
            pad.SetTopMargin(0.01)
            pad.SetLeftMargin(0.05)
            pad.SetRightMargin(0.001)

            tree.Draw(
                "(wfm%i - wfm%i[0]):Iteration$*40/1e3" % (channel, channel),
                "Entry$==%i" % i_entry, 
                options
            )
            pave_text.Clear()
            pave_text.AddText("%s" % channel_map[tree.channel[i]])
            pave_text.AddText("E=%i" % tree.energy[i])
            pave_text.Draw()


        #frame_hist.SetMinimum(0)
        #frame_hist.SetMaximum(pow(2,14))
        frame_hist.SetMinimum(7400)
        frame_hist.SetMaximum(8500)
        #frame_hist.SetMinimum(adc_min-10)
        #frame_hist.SetMaximum(adc_max+10)

        canvas.cd(0)
        legend.Draw()
        canvas.Update()

  
        val = raw_input("--> entry %i | enter to continue (q to quit, p to print, or entry number) " % i_entry)
        i_entry += 1

        if val == 'q': break
        if val == 'p':
            canvas.Update()
            canvas.Print("%s_entry_%i.png" % (basename, i_entry))
        try:
            i_entry = int(val)
        except: 
            pass




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



