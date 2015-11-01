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
from ROOT import TLine
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

def print_tier2_info(tree, sampling_freq_Hz=25.0e6):

    print "\t time stamp: %.2f" % (tree.time_stamp/sampling_freq_Hz)
    print "\t charge energy: %i" % tree.chargeEnergy
    print "\t light energy: %i" % tree.lightEnergy

    for i in xrange(6):
        print "\t ch %i | energy %i | maw max %i | max time [us]: %.2f" % (
            tree.channel[i],
            tree.energy[i],
            tree.maw_max[i],
            tree.wfm_max_time[i]/sampling_freq_Hz*1e6,
        )

def process_file(filename):

    # options ------------------------------------------
    threshold = 150
    #threshold = 50 # ok for unshaped, unamplified data

    # y axis limits:
    y_min = -200
    y_max = 2200

    # need to determine this on the fly from PMT signal
    trigger_time = 40.0*200/1e3 # in mircoseconds, 40ns * 200 samples 

    #------------------------------------------------------


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
    canvas.SetTopMargin(0.15)
    canvas.SetBottomMargin(0.12)

    # line to show trigger time
    line = TLine(trigger_time, y_min, trigger_time,y_max)
    line.SetLineStyle(7)
    print "trigger time: [microseconds]", trigger_time

    # whether to divide the canvas into 6
    do_divide = False

    if do_divide:
     
        title_size = gStyle.GetTitleSize()
        gStyle.SetTitleSize(title_size*10.0)
        label_size = gStyle.GetLabelSize("Y")
        gStyle.SetLabelSize(label_size*4.0,"Y")

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
    channel_map[8] = "PMT/10"

    tree.GetEntry(0)
    trace_length_us = tree.wfm_length/sampling_freq_Hz*1e6
    print "length in microseconds:", trace_length_us

    frame_hist = TH1D("hist", "", 100, 0, trace_length_us + 1)
    frame_hist.SetLineColor(TColor.kWhite)
    frame_hist.SetXTitle("Time [#mus]")
    frame_hist.SetYTitle("ADC units")
    frame_hist.GetYaxis().SetTitleOffset(1.3)
    frame_hist.SetBinContent(1, pow(2,14))

    tree.SetLineWidth(2)
    pave_text = TPaveText(0.01, 0.01, 0.75, 0.07, "NDC")
    pave_text.SetTextAlign(11)
    pave_text.GetTextFont()
    pave_text.SetTextFont(42)

    if do_divide:
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

    legend = TLegend(0.1, 0.86, 0.9, 0.99)
    legend.SetNColumns(3)

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
    
    # loop over all events in file
    i_entry = 0
    while i_entry < n_entries:

        tree.GetEntry(i_entry)

       
        # test whether any charge channel is above threshold
        if True:
            if tree.lightEnergy < 15: 
                i_entry += 1
                continue
            n_above_threshold = 0
            for i in xrange(5): 
                if tree.energy[i] > threshold: n_above_threshold += 1
            if n_above_threshold == 0:
                i_entry += 1
                continue

        # use total charge energy:
        #if tree.chargeEnergy<100: 
        #    i_entry+= 1
        #    continue

        if not do_divide:
            frame_hist.Draw()


        print "==> entry %i of %i | charge energy: %i" % (
            i_entry, 
            n_entries,
            tree.chargeEnergy,
        )


        wfm_max = 0
        adc_min = pow(2,14)

        print_tier2_info(tree)

      
        #wfm0_e = tree.wfm0[-100:] - tree.wfm0[100:]
        #print wfm0_e
        samples_to_avg = 100

        wfm0_e = 0.0
        wfm1_e = 0.0
        wfm2_e = 0.0
        wfm3_e = 0.0
        wfm4_e = 0.0
        wfm8_e = 0.0


        wfm_length = tree.wfm_length

        for i_sample in xrange(samples_to_avg):
            #print "i_sample:", i_sample
            wfm0_e += tree.wfm0[wfm_length - i_sample - 1]- tree.wfm0[i_sample]
            wfm1_e += tree.wfm1[wfm_length - i_sample - 1]- tree.wfm1[i_sample]
            wfm2_e += tree.wfm2[wfm_length - i_sample - 1]- tree.wfm2[i_sample]
            wfm3_e += tree.wfm3[wfm_length - i_sample - 1]- tree.wfm3[i_sample]
            wfm4_e += tree.wfm4[wfm_length - i_sample - 1]- tree.wfm4[i_sample]
            wfm8_e += tree.wfm8[wfm_length - i_sample - 1]- tree.wfm8[i_sample]

        energies = [wfm0_e, wfm1_e, wfm2_e, wfm3_e, wfm4_e, wfm8_e]
        for i in xrange(len(energies)): energies[i] = energies[i]/samples_to_avg

        legend.Clear()
        for (i, channel) in enumerate(channels):

            energy = energies[i]
            if channel == 8:
                energy = tree.lightEnergy
            legend.AddEntry(
                hists[i], 
                "%s E = %.1f" % (channel_map[channel], energy),
                "f"
            )

        # loop over all channels in the event:
        for (i, channel) in enumerate(channels):

            #print "\t %i | channel %i" % (i, channel)

            options = "l"
            if not do_divide:
                options = "l same"

            #if i == 0:
            #    if channel == 8:
            #        options = "l"
            #    else:
            #        frame_hist.Draw()
            #print options


            # find range of charge channels:
            #if channel < 5:

                # FIXME -- save wfm max in tree:
                #for index in tree.wfm_length:
                #    if tree. > wfm_max: wfm_max = tree.wfm_max[channel]
                #    if tree.adc_min[channel] < adc_min: adc_min = tree.adc_min[channel]


            try:
                color = colors[channel]
            except IndexError:
                color = TColor.kBlack

            tree.SetLineColor(color)

            if do_divide:
                pad = canvas.cd(i+1)
                pad.SetGrid(1,1)
                pad.SetBottomMargin(0.01)
                pad.SetTopMargin(0.01)
                pad.SetLeftMargin(0.05)
                pad.SetRightMargin(0.001)

            # scale the PMT signal b/c it is huge
            multiplier = 1.0
            if channel == 8:
                multiplier = 0.1

            # add an offset so the channels are draw at different levels
            offset = 800 - i*200
            if channel == 8:
                offset = 1500

            draw_command = "((wfm%i - wfm%i[0])*%s+%i):Iteration$*40/1e3" % (
                channel, 
                channel, 
                multiplier,
                offset,
            )
            #print draw_command

            tree.Draw(
                draw_command,
                "Entry$==%i" % i_entry, 
                options
            )

            pave_text.Clear()
            if do_divide:
                pave_text.AddText("%s" % channel_map[tree.channel[i]])
                pave_text.AddText("E=%i" % tree.energy[i])
            else:
                pave_text.AddText("event %i" % i_entry)
                pave_text.AddText("%s" % basename)
            pave_text.Draw()
                
            # end loop over channels


        frame_hist.SetMinimum(y_min)
        frame_hist.SetMaximum(y_max)

        line.Draw()
        legend.Draw()
        canvas.Update()

  
        val = raw_input("--> entry %i | enter to continue (q to quit, p to print, or entry number) " % i_entry)
        i_entry += 1

        if val == 'q': break
        if val == 'p':
            canvas.Update()
            canvas.Print("%s_entry_%i.png" % (basename, i_entry))
            canvas.Print("%s_entry_%i.pdf" % (basename, i_entry))
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



