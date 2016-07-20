#!/usr/bin/env python

"""
This script draws events from NGM root file(s). 

arguments [NGM root files of events: HitOut*.root]
"""

import os
import sys
import glob
from scipy.fftpack import fft

import ROOT
#ROOT.gROOT.SetBatch(True) # uncomment to draw multi-page PDF

import struck_analysis_parameters


# set the ROOT style
ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       

# set up a canvas
canvas = ROOT.TCanvas("canvas","", 1000, 800)
canvas.SetGrid(1,1)
#canvas.SetLeftMargin(0.15)
canvas.SetTopMargin(0.15)
canvas.SetBottomMargin(0.12)


def print_tier2_info(tree, energies, sampling_freq_Hz=25.0e6):

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    chargeEnergy = 0.0
    for energy in energies[len(charge_channels_to_use):]:
        chargeEnergy += energy
    print "\t event: %i" % tree.event
    print "\t time stamp: %.2f" % (tree.time_stamp/sampling_freq_Hz)
    print "\t charge energy: %i" % chargeEnergy
    print "\t light energy: %i" % energies[-1]

    i = 0
    for (channel, value) in enumerate(charge_channels_to_use):
        if value == 1:
            print "\t ch %i | energy %i | maw max %i | max time [us]: %.2f" % (
                tree.channel[i],
                #tree.energy[i],
                energies[i],
                tree.maw_max[i],
                tree.wfm_max_time[i]/sampling_freq_Hz*1e6,
            )
            i+=1

def process_file(filename, n_plots=0):

    # options ------------------------------------------
    threshold = 0 # keV
    #threshold = 570 # keV, for generating multi-page PDF
    #threshold = 50 # ok for unshaped, unamplified data

    # y axis limits:
    y_min = -200
    #y_max = 7000 # unamplified, keV
    y_max = 5000 # amplified, keV

    samples_to_avg = 100 # n baseline samples to use for energy 

    n_plots_total = 10 # for drawing multi-page PDF, in batch mode

    #------------------------------------------------------

    calibration_values = struck_analysis_parameters.calibration_values
    channel_map = struck_analysis_parameters.channel_map
    pmt_channel = struck_analysis_parameters.pmt_channel

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    channels = []
    for (channel, value) in enumerate(charge_channels_to_use):
        #print channel, value
        if value: channels.append(channel)
    channels.append(pmt_channel)
    n_channels = len(channels)
    colors = struck_analysis_parameters.get_colors()

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    print "basename:", basename

    # open the root file and grab the tree
    root_file = ROOT.TFile(filename)
    tree = root_file.Get("HitTree")
    n_entries = tree.GetEntries()

    # get NGM system config
    sys_config = root_file.Get("NGMSystemConfiguration")
    card0 = sys_config.GetSlotParameters().GetParValueO("card",0)
    card1 = sys_config.GetSlotParameters().GetParValueO("card",1)

    print "%i entries, %i channels, %.2f events" % (
        n_entries, 
        len(charge_channels_to_use),
        n_entries/len(charge_channels_to_use),
    )

    sampling_freq_Hz = 1
    if card0.clock_source_choice == 3:
        print "sampling_freq_Hz: 25 MHz"
        sampling_freq_Hz = 25.0e6
    else:
        print "*** WARNING: clock_source_choice unknown -- data collected at 25 MHz?"


    channel_map = struck_analysis_parameters.channel_map

    tree.GetEntry(0) # use 0th entry to get some info that we don't expect to change... 
    trace_length_us = tree.HitTree.GetNSamples()/sampling_freq_Hz*1e6
    print "length in microseconds:", trace_length_us

    trigger_time = card0.pretriggerdelay_block[0] # /sampling_freq_Hz*1e6
    print "trigger time: [microseconds]", trigger_time

    frame_hist = ROOT.TH1D("hist", "", 100, 0, 820)
    frame_hist.SetLineColor(ROOT.kWhite)
    frame_hist.SetXTitle("Time [clock ticks]")
    frame_hist.SetYTitle("Energy (with arbitrary offsets) [keV] ")
    frame_hist.GetYaxis().SetTitleOffset(1.3)
    frame_hist.SetBinContent(1, pow(2,14))

    pave_text = ROOT.TPaveText(0.01, 0.01, 0.75, 0.07, "NDC")
    pave_text.SetTextAlign(11)
    pave_text.GetTextFont()
    pave_text.SetTextFont(42)
    pave_text2 = ROOT.TPaveText(0.11, 0.63, 0.28, 0.75, "NDC")
    pave_text2.SetTextAlign(11)
    pave_text2.GetTextFont()
    pave_text2.SetTextFont(42)

    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    pave_text2.SetFillColor(0)
    pave_text2.SetFillStyle(0)
    pave_text2.SetBorderSize(0)

    legend = ROOT.TLegend(0.1, 0.86, 0.9, 0.99)
    legend.SetNColumns(7)

    # set up some placeholder hists for the legend
    hists = []
    for (i, channel) in enumerate(channels):
        #print "i=%i, ch=%i (%s)" % (i, channel, channel_map[channel])
        hist = ROOT.TH1D("hist%i" % channel,"",10,0,10)
        try:
            color = colors[channel]
        except IndexError:
            color = ROOT.kBlack

        hist.SetLineColor(color)
        hist.SetFillColor(color)
        hists.append(hist)
    
    # loop over all events in file
    i_entry = 0
    y_max_old = y_max
    # use while loop instead of for loop so we can modify i_entry if needed
    while i_entry < n_entries:
        y_max = y_max_old # reset at start of each event
       
        chargeEnergy = 0.0

        frame_hist.Draw()
        wfm_length = tree.HitTree.GetNSamples()
        sum_wfm = [0]*wfm_length

        #print "==> entry %i of %i | charge energy: %i" % ( i_entry, n_entries, chargeEnergy,)
      
        legend.Clear()
        legend_entries = [""]*32

        # loop over all channels in the event:
        for i in xrange(len(channels)):

            tree.GetEntry(i_entry)
            i_entry += 1
            channel = tree.HitTree.GetChannel()
            slot = tree.HitTree.GetSlot()

            try:
                color = colors[channel+slot*16]
            except IndexError:
                color = ROOT.kBlack


            multiplier = calibration_values[channel]
            #print "entry %i, channel: %i, multiplier: %.2f" % (i_entry, channel, multiplier)

            # add an offset so the channels are draw at different levels
            #offset = 6000 - i*250
            offset = 0
            if offset < y_min: y_min = offset - 100
            if channel == pmt_channel:
                offset = 1000

            graph = tree.HitTree.GetGraph()
            graph.SetLineColor(color)
            fcn_string = "(y - %s)*%s + %s" % (
                graph.GetY()[0], multiplier, offset)
            #print "fcn_string:", fcn_string
            fcn = ROOT.TF2("fcn",fcn_string)
            graph.Apply(fcn)
            graph.SetLineWidth(2)
            graph.Draw("l")
            #print "\t entry %i, ch %i, slot %i" % ( i_entry-1, channel, slot,)

            # construct a sum wfm
            if channel + slot*16 != 0: # skip ch 0 since it had a pulser during testing:
                for i_point in xrange(tree.HitTree.GetNSamples()):
                    y = graph.GetY()[i_point]
                    sum_wfm[i_point] = sum_wfm[i_point] + y
                
            # not working yet -- graph_max is always ~ -1111
            graph_max = graph.GetMaximum()
            if graph_max > y_max: 
                y_max = graph_max
            #print "graph_max: %s, y_max: %s" % (graph_max, y_max)

            # legend uses hists for color/fill info
            legend_entries[channel+slot*16] = "%s, ch %i" % (channel_map[channel+slot*16], channel+slot*16) #"%s E = %.1f keV" % (channel_map[channel], energies[i]),

            # end loop over channels

        sum_graph = ROOT.TGraph()
        for i_point in xrange(len(sum_wfm)):
            sum_graph.SetPoint(i_point, i_point, sum_wfm[i_point]+2000)

        #sum_graph.SetLineWidth(3)
        sum_graph.Draw("l")

        pave_text.Clear()
        pave_text.AddText("page %i, event %i" % (n_plots+1, i_entry/32))
        pave_text.AddText("%s" % basename)
        pave_text.Draw()

        pave_text2.Clear()
        pave_text2.AddText("#SigmaE_{C} = %i" % chargeEnergy)
        pave_text2.AddText("t=%.4fs" % (tree.HitTree.GetRawClock()/sampling_freq_Hz))
        #pave_text2.Draw()

        frame_hist.SetMinimum(y_min)
        frame_hist.SetMaximum(y_max)
        #frame_hist.SetMinimum(0)
        #frame_hist.SetMaximum(16000)

        for i in xrange(len(channels)):
            legend.AddEntry( hists[i], legend_entries[i], "f")

        # line to show trigger time
        line = ROOT.TLine(trigger_time, y_min, trigger_time,y_max)
        line.SetLineWidth(2)
        line.SetLineStyle(7)
        line.Draw()
        legend.Draw()
        canvas.Update()
        n_plots += 1
        print "n_plots", n_plots

        if not ROOT.gROOT.IsBatch(): 


            if True: # do_fft:
                # FFT, based on Jacopo's script
                sum_fft = fft(sum_wfm)
                fft_graph = ROOT.TGraph()
                fft_graph.SetLineWidth(2)
                for i_point in xrange(len(sum_wfm)/2):
                    if i_point <= 0: continue
                    x = i_point*sampling_freq_Hz/1e6/2/len(sum_wfm)  # MHz?
                    fft_graph.SetPoint(fft_graph.GetN(), x, abs(sum_fft[i_point]))
                    if  abs(sum_fft[i_point]) > 1e4:
                        print "freq=%s kHz | val = %.2e" % (
                            x*1e3, 
                            abs(sum_fft[i_point])
                        )



            #print_tier2_info(tree, energies)
            val = raw_input("--> entry %i | enter to continue (q to quit, p to print, or entry number) " % i_entry)

            if val == 'q': sys.exit()
            if val == 'p':
                canvas.Update()
                canvas.Print("%s_entry_%i.png" % (basename, i_entry))
                canvas.Print("%s_entry_%i.pdf" % (basename, i_entry))
            try:
                i_entry = int(val)
                print "getting entry %i" % i_entry
                continue
            except: 
                pass

                if False: # draw FFT
                    fft_graph.Draw("alp")
                    fft_hist = fft_graph.GetHistogram()
                    fft_hist.SetXTitle("Freq [MHz]")
                    canvas.SetLogy(1)
                    canvas.SetLogx(1)
                    canvas.Update()
                    #val = raw_input("--> FFT -- enter to continue (q to quit) ")
                    if val == 'q': sys.exit()
                    canvas.SetLogy(0)
                    canvas.SetLogx(0)

        else:
            # if we run in batch mode, print a multi-page canvas
            plot_name = "EventsWithChargeAbove%ikeV_6thLXe.pdf" % threshold
            if n_plots == 1:
                plot_name = plot_name + "("
            if n_plots >= n_plots_total:
                plot_name = plot_name + ")"
            print plot_name
            canvas.Print(plot_name)
            if n_plots >= n_plots_total:
                print "quitting..."
                sys.exit()

        # end loop over entries
    
    return n_plots




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [NGM root files (HitOut*.root)]"
        sys.exit(1)


    n_plots = 0
    for filename in sys.argv[1:]:
        n_plots += process_file(filename, n_plots)



