#!/usr/bin/env python

"""
This script draws events from NGM root file(s). 

arguments [NGM root files of events: HitOut*.root]
"""

import os
import sys
import commands
from scipy.fftpack import fft

import ROOT
ROOT.gROOT.SetBatch(True) # uncomment to draw multi-page PDF

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

def process_file(filename=None, n_plots_total=0):


    #If input filename is null assume we want to examine the most recent file
    if(filename == None):
        # example name: SIS3316Raw_20160712204526_1.bin
        output  = commands.getstatusoutput("ls -rt Hit*.root | tail -n1")
        filename = output[1]
        print "--> using most recent NGM file, ", filename



    # options ------------------------------------------
    threshold = 0 # keV
    #threshold = 570 # keV, for generating multi-page PDF
    #threshold = 50 # ok for unshaped, unamplified data

    use_adc_units = True # otherwise keV
    do_fft = True

    # y axis limits:
    y_min = -200 # keV
    if use_adc_units:
        y_min = -50 # ADC units
    y_max = 500 # keV
    if use_adc_units:
        y_max = 200 # ADC units

    samples_to_avg = 100 # n baseline samples to use for energy 

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

    frame_hist = ROOT.TH1D("hist", "", int(tree.HitTree.GetNSamples()*1.05), 0, trace_length_us+1)
    frame_hist.SetXTitle("Time [#mus]")
    if use_adc_units:
        frame_hist.SetYTitle("ADC units ")
        sum_offset = 50
    else:
        frame_hist.SetYTitle("Energy (with arbitrary offsets) [keV] ")
        

    frame_hist.GetYaxis().SetTitleOffset(1.3)

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
    n_plots = 0
    y_max_old = y_max
    # use while loop instead of for loop so we can modify i_entry if needed
    while i_entry < n_entries:

        canvas.SetLogy(0)
        canvas.SetLogx(0)

        y_max = y_max_old # reset at start of each event
       
        chargeEnergy = 0.0

        frame_hist.Draw()
        wfm_length = tree.HitTree.GetNSamples()
        sum_wfm = [0]*wfm_length
        sum_wfm0 = [0]*wfm_length
        sum_wfm1 = [0]*wfm_length

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
            if use_adc_units:
                multiplier = 1.0
            #print "entry %i, channel: %i, multiplier: %.2f" % (i_entry, channel, multiplier)

            # add an offset so the channels are draw at different levels
            #offset = 6000 - i*250
            offset = 0
            #if channel == pmt_channel:
            #    offset = 200
            if offset < y_min: y_min = offset - 100

            graph = tree.HitTree.GetGraph()

            baseline = 0
            for i_sample in xrange(samples_to_avg):
                baseline += graph.GetY()[i_sample]
            baseline /= samples_to_avg

            graph.SetLineColor(color)
            fcn_string = "(y - %s)*%s + %s" % (
                baseline, multiplier, offset)
            #print "fcn_string:", fcn_string
            fcn = ROOT.TF2("fcn",fcn_string)
            graph.Apply(fcn)
            # convert x axis to microseconds
            for i_point in xrange(graph.GetN()):
                x = graph.GetX()[i_point]
                y = graph.GetY()[i_point]
                graph.SetPoint(i_point, x/sampling_freq_Hz*1e6, y)

            graph.SetLineWidth(2)
            graph.Draw("l")
            #print "\t entry %i, ch %i, slot %i" % ( i_entry-1, channel, slot,)

            # construct sum wfm
            for i_point in xrange(tree.HitTree.GetNSamples()):
                y = graph.GetY()[i_point]
                sum_wfm[i_point] = sum_wfm[i_point] + y
                if slot == 0:
                    sum_wfm0[i_point] = sum_wfm0[i_point] + y
                if slot == 1:
                    sum_wfm1[i_point] = sum_wfm1[i_point] + y
                
            # not working yet -- graph_max is always ~ -1111
            graph_max = graph.GetHistogram().GetMaximum()
            if graph_max > y_max: 
                y_max = graph_max
            #print "graph_max: %s, y_max: %s" % (graph_max, y_max)

            # legend uses hists for color/fill info
            legend_entries[channel+slot*16] = "%s, ch %i" % (channel_map[channel+slot*16], channel+slot*16) #"%s E = %.1f keV" % (channel_map[channel], energies[i]),

            # end loop over channels

        sum_graph = ROOT.TGraph()
        sum_graph0 = ROOT.TGraph()
        sum_graph1 = ROOT.TGraph()
        for i_point in xrange(len(sum_wfm)):
            sum_graph.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm[i_point]+sum_offset)
            sum_graph0.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm0[i_point]+sum_offset*2)
            sum_graph1.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm1[i_point]+sum_offset*3)

        #sum_graph.SetLineWidth(3)
        sum_graph.Draw("l")
        sum_graph0.SetLineColor(ROOT.kBlue)
        sum_graph0.Draw("l")
        sum_graph1.SetLineColor(ROOT.kRed)
        sum_graph1.Draw("l")

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

        legend.AddEntry(sum_graph, "sum","l")
        legend.AddEntry(sum_graph0, "sum slot 0","l")
        legend.AddEntry(sum_graph1, "sum slot 1","l")

        # line to show trigger time
        line = ROOT.TLine(trigger_time, y_min, trigger_time,y_max)
        line.SetLineWidth(2)
        line.SetLineStyle(7)
        line.Draw()
        legend.Draw()
        canvas.Update()
        n_plots += 1
        print "n_plots / n_plots_total", n_plots, n_plots_total

        if do_fft: 
            # FFT, based on Jacopo's script
            sum_fft = fft(sum_wfm)
            sum_fft0 = fft(sum_wfm0)
            sum_fft1 = fft(sum_wfm1)
            fft_graph = ROOT.TGraph()
            fft_graph.SetLineWidth(2)
            fft_graph0 = ROOT.TGraph()
            fft_graph0.SetLineColor(ROOT.kBlue)
            fft_graph1 = ROOT.TGraph()
            fft_graph1.SetLineColor(ROOT.kRed)
            for i_point in xrange(len(sum_wfm)/2):
                if i_point <= 0: continue
                x = i_point*sampling_freq_Hz/1e6/2/len(sum_wfm)  # MHz?
                fft_graph.SetPoint(fft_graph.GetN(), x, abs(sum_fft[i_point]))
                fft_graph0.SetPoint(fft_graph0.GetN(), x, abs(sum_fft0[i_point]))
                fft_graph1.SetPoint(fft_graph0.GetN(), x, abs(sum_fft1[i_point]))
                if  abs(sum_fft[i_point]) > 1e4:
                    print "freq=%s kHz | val = %.2e" % (
                        x*1e3, 
                        abs(sum_fft[i_point])
                    )


        if not ROOT.gROOT.IsBatch(): 

            #print_tier2_info(tree, energies)
            val = raw_input("--> entry %i | enter to continue (q to quit, p to print, or entry number) " % i_entry)

            if val == 'q': sys.exit()
            elif val == 'p':
                canvas.Update()
                canvas.Print("%s_event_%i.pdf" % (basename, n_plots-1))
            try:
                i_entry = int(val)
                print "getting entry %i" % i_entry
                continue
            except: 
                pass

                if do_fft: # draw FFT
                    canvas.SetLogy(1)
                    canvas.SetLogx(1)
                    fft_graph.Draw("alp")
                    fft_hist = fft_graph.GetHistogram()
                    fft_hist.SetXTitle("Freq [MHz]")
                    fft_hist.SetTitle("Sum wfm FFT")
                    fft_hist.SetMinimum(100)
                    fft_hist.SetMaximum(1e5)
                    fft_hist.Draw()
                    fft_graph.Draw("l same")
                    fft_graph0.Draw("l same")
                    fft_graph1.Draw("l same")
                    canvas.Update()
                    val = raw_input("--> FFT -- enter to continue (q to quit, p to print) ")
                    if val == 'q': 
                        sys.exit()
                    elif val == 'p':
                        canvas.Print("%s_FFT_event_%i.pdf" % (basename, n_plots-1))
                    canvas.SetLogy(0)
                    canvas.SetLogx(0)

        else:
            # if we run in batch mode, print a multi-page canvas
            #plot_name = "EventsWithChargeAbove%ikeV_6thLXe.pdf" % threshold
            plot_name = "2016_07_NoiseTests.pdf"
            if n_plots == 1:
                canvas.Print("%s[" % plot_name)
                #plot_name = plot_name + "("
            #if n_plots >= n_plots_total:
            #    plot_name = plot_name + ")"
            canvas.Print(plot_name)

            if do_fft: # draw FFT
                canvas.SetLogy(1)
                canvas.SetLogx(1)
                fft_graph.Draw("alp")
                fft_hist = fft_graph.GetHistogram()
                fft_hist.SetXTitle("Freq [MHz]")
                fft_hist.SetTitle("Sum wfm FFT")
                fft_hist.SetMinimum(100)
                fft_hist.SetMaximum(1e5)
                fft_hist.Draw()
                fft_graph.Draw("l same")
                fft_graph0.Draw("l same")
                fft_graph1.Draw("l same")
                canvas.Update()
                canvas.Print(plot_name)

            if n_plots >= n_plots_total:
                canvas.Print("%s]" % plot_name)

            if n_plots >= n_plots_total:
                print "quitting..."
                sys.exit()

        # end loop over entries
    
    return n_plots




if __name__ == "__main__":

    n_plots_total = 50
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            n_plots += process_file(filename, n_plots_total)
    else:
        process_file(n_plots_total=n_plots_total)



