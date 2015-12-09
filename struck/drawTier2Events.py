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
#gROOT.SetBatch(True) # use batch mode to draw multi-page PDF
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

import struck_analysis_parameters


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       



# set up a canvas
canvas = TCanvas("canvas","")
canvas.SetGrid(1,1)
#canvas.SetLeftMargin(0.15)
canvas.SetTopMargin(0.15)
canvas.SetBottomMargin(0.12)




def print_tier2_info(tree, energies, sampling_freq_Hz=25.0e6):
    n_channels = struck_analysis_parameters.n_channels

    chargeEnergy = 0.0
    for energy in energies[:-1]:
        chargeEnergy += energy
    print "\t event: %i" % tree.event
    print "\t time stamp: %.2f" % (tree.time_stamp/sampling_freq_Hz)
    print "\t charge energy: %i" % chargeEnergy
    print "\t light energy: %i" % energies[-1]

    for i in xrange(n_channels):
        print "\t ch %i | energy %i | maw max %i | max time [us]: %.2f" % (
            tree.channel[i],
            #tree.energy[i],
            energies[i],
            tree.maw_max[i],
            tree.wfm_max_time[i]/sampling_freq_Hz*1e6,
        )

def process_file(filename, n_plots=0):

    # options ------------------------------------------
    threshold = 570 # keV
    #threshold = 50 # ok for unshaped, unamplified data

    # y axis limits:
    y_min = -200
    y_max = 3000 # unamplified, keV
    #y_max = 5800 # amplified, keV

    # need to determine this on the fly from PMT signal
    trigger_time = 40.0*200/1e3 # in mircoseconds, 40ns * 200 samples 

    samples_to_avg = 100 # n baseline samples to use for energy 

    do_divide = False # whether to divide the canvas into 6

    n_plots_total = 200 # for drawing multi-page PDF, in batch mode

    #------------------------------------------------------

    calibration_values = struck_analysis_parameters.calibration_values
    channel_map = struck_analysis_parameters.channel_map
    channels = struck_analysis_parameters.channels
    n_channels = struck_analysis_parameters.n_channels

    sampling_freq_Hz = 25.0e6

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries


    # find the file-average baselines to determine whether these data use 2V input
    hist = TH1D("hist","",100, 0, pow(2,14))
    print "calculating mean baseline & baseline RMS for each channel in this file..."
    for (i, i_channel) in enumerate(channels):
        print "%i: ch %i" % (i, i_channel)
        selection = "Iteration$<%i && channel==%i && Entry$<50000" % (samples_to_avg, i_channel)
            
        # calculate avg baseline:
        draw_command = "wfm%i >> hist" % i_channel
        tree.Draw(
            draw_command,
            selection,
            "goff"
        )
        baseline_mean_file = hist.GetMean()
        print "\t draw command: %s | selection %s" % (draw_command, selection)
        print "\t file baseline mean:", baseline_mean_file
        is_2Vinput = struck_analysis_parameters.is_2Vinput(baseline_mean_file)
        if is_2Vinput:
            print "\t channel %i used 2V input range" % i_channel
            print "\t dividing calibration by 2.5"
            calibration_values[i_channel] /= 2.5


    print "trigger time: [microseconds]", trigger_time


    if do_divide:
        title_size = gStyle.GetTitleSize()
        gStyle.SetTitleSize(title_size*10.0)
        label_size = gStyle.GetLabelSize("Y")
        gStyle.SetLabelSize(label_size*4.0,"Y")

        canvas.Divide(1,n_channels)

    channels = struck_analysis_parameters.channels
    channel_map = struck_analysis_parameters.channel_map

    tree.GetEntry(0)
    trace_length_us = tree.wfm_length/sampling_freq_Hz*1e6
    print "length in microseconds:", trace_length_us

    frame_hist = TH1D("hist", "", 100, 0, trace_length_us + 1)
    frame_hist.SetLineColor(TColor.kWhite)
    frame_hist.SetXTitle("Time [#mus]")
    frame_hist.SetYTitle("Energy (with arbitrary offsets) [keV] ")
    frame_hist.GetYaxis().SetTitleOffset(1.3)
    frame_hist.SetBinContent(1, pow(2,14))

    tree.SetLineWidth(2)
    pave_text = TPaveText(0.01, 0.01, 0.75, 0.07, "NDC")
    pave_text.SetTextAlign(11)
    pave_text.GetTextFont()
    pave_text.SetTextFont(42)
    pave_text2 = TPaveText(0.11, 0.63, 0.28, 0.75, "NDC")
    pave_text2.SetTextAlign(11)
    pave_text2.GetTextFont()
    pave_text2.SetTextFont(42)

    if do_divide:
        pave_text = TPaveText(0.9, 0.0, 1.0, 0.6, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    pave_text2.SetFillColor(0)
    pave_text2.SetFillStyle(0)
    pave_text2.SetBorderSize(0)

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
    y_max_old = y_max
    # use while loop instead of for loop so we can modify i_entry if needed
    while i_entry < n_entries:
        tree.GetEntry(i_entry)
        y_max = y_max_old # reset at start of each event
       

        #print "pre-test..."
        # test whether any charge channel is above threshold
        if True:
            if tree.lightEnergy < 15: 
                i_entry += 1
                continue

            n_above_threshold = 0
            for i in xrange(n_channels-1): 
                if tree.energy[i]*calibration_values[tree.channel[i]] > threshold: 
                    #print "ch %i | E: %.2f " % (
                    #    tree.channel[i],
                    #    tree.energy[i]*calibration_values[tree.channel[i]])
                    n_above_threshold += 1

            if n_above_threshold == 0:
                i_entry += 1
                continue
        #print "passed pre-test"

        # do more accurate energy calculation...
        wfm0_e = 0.0
        wfm1_e = 0.0
        wfm2_e = 0.0
        wfm3_e = 0.0
        wfm4_e = 0.0
        wfm5_e = 0.0
        wfm8_e = 0.0
        wfm_length = tree.wfm_length
        for i_sample in xrange(samples_to_avg):
            #print "i_sample:", i_sample
            wfm0_e += tree.wfm0[wfm_length - i_sample - 1]- tree.wfm0[i_sample]
            wfm1_e += tree.wfm1[wfm_length - i_sample - 1]- tree.wfm1[i_sample]
            wfm2_e += tree.wfm2[wfm_length - i_sample - 1]- tree.wfm2[i_sample]
            wfm3_e += tree.wfm3[wfm_length - i_sample - 1]- tree.wfm3[i_sample]
            wfm4_e += tree.wfm4[wfm_length - i_sample - 1]- tree.wfm4[i_sample]
            wfm5_e += tree.wfm5[wfm_length - i_sample - 1]- tree.wfm5[i_sample]
            wfm8_e += tree.wfm8[wfm_length - i_sample - 1]- tree.wfm8[i_sample]
        energies = [wfm0_e, wfm1_e, wfm2_e, wfm3_e, wfm4_e, wfm5_e, wfm8_e]
        for i in xrange(len(energies)): energies[i] = energies[i]/samples_to_avg

        #print "threshold test..."
        n_above_threshold = 0
        for (i, channel) in enumerate(channels):
            energies[i] *= calibration_values[channel]
            if channel == 8:
                energies[i] = tree.lightEnergy*calibration_values[channel]
            if energies[i] > threshold and channel != 8:
                #print "ch %i | E: %.2f" % (channel, energies[i])
                n_above_threshold += 1
        #print "done w threshold test"


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


      
        #wfm0_e = tree.wfm0[-100:] - tree.wfm0[100:]
        #print wfm0_e

        legend.Clear()
        for (i, channel) in enumerate(channels):

            legend.AddEntry(
                hists[i], 
                "%s E = %.1f keV" % (channel_map[channel], energies[i]),
                "f"
            )

        # loop over all channels in the event:
        for (i, channel) in enumerate(channels):

            #print "\t %i | channel %i" % (i, channel)

            options = "l"
            if not do_divide:
                options = "l same"

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

            multiplier = calibration_values[tree.channel[i]]

            # add an offset so the channels are draw at different levels
            offset = 1000 - i*250
            if channel == 8:
                offset = 2000

            if energies[i]+offset > y_max:
                y_max = energies[i]+offset+800

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
            pave_text2.Clear()
            if do_divide:
                pave_text.AddText("%s" % channel_map[tree.channel[i]])
                pave_text.AddText("E=%i" % tree.energy[i])
            else:
                chargeEnergy = 0.0
                for energy in energies[:-1]:
                    chargeEnergy += energy

                pave_text.AddText("page %i, event %i" % (n_plots+1, i_entry))
                pave_text.AddText("%s" % basename)
                pave_text2.AddText("#SigmaE_{C} = %i" % chargeEnergy)
                pave_text2.AddText("t=%.4fs" % (tree.time_stampDouble/sampling_freq_Hz))
                pave_text2.Draw()
            pave_text.Draw()
                
            # end loop over channels


        frame_hist.SetMinimum(y_min)
        frame_hist.SetMaximum(y_max)

        # line to show trigger time
        line = TLine(trigger_time, y_min, trigger_time,y_max)
        line.SetLineWidth(2)
        line.SetLineStyle(7)
        line.Draw()
        legend.Draw()
        canvas.Update()
        n_plots += 1
        print "n_plots", n_plots

        if not gROOT.IsBatch(): 
            print_tier2_info(tree, energies)
            val = raw_input("--> entry %i | enter to continue (q to quit, p to print, or entry number) " % i_entry)

            if val == 'q': sys.exit()
            if val == 'p':
                canvas.Update()
                canvas.Print("%s_entry_%i.png" % (basename, i_entry))
                canvas.Print("%s_entry_%i.pdf" % (basename, i_entry))
            try:
                i_entry = int(val)
            except: 
                pass

        else:
            # if we run in batch mode, print a multi-page canvas
            plot_name = "EventsWithChargeAbove%ikeV.pdf" % threshold
            if n_plots == 1:
                plot_name = plot_name + "("
            if n_plots >= n_plots_total:
                plot_name = plot_name + ")"
            print plot_name
            canvas.Print(plot_name)
            if n_plots >= n_plots_total:
                print "quitting..."
                sys.exit()


        i_entry += 1
        # end loop over entries
    
    return n_plots




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    n_plots = 0
    for filename in sys.argv[1:]:
        n_plots += process_file(filename, n_plots)



