#!/usr/bin/env python

"""
This script draws events from NGM root file(s). 

arguments [NGM root files of events: tier1_SIS3316Raw_*.root]
"""

import os
import sys
import math
import commands
import numpy as np
from scipy.fftpack import fft

import ROOT
ROOT.gROOT.SetBatch(True) # uncomment to draw multi-page PDF

from struck import struck_analysis_parameters

# set the ROOT style
ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       
print "title align:", ROOT.gStyle.GetTitleAlign() 
ROOT.gStyle.SetTitleX(.5)
# default: 13
ROOT.gStyle.SetTitleAlign(23) 

# set up a canvas
canvas = ROOT.TCanvas("canvas","", 1000, 800)
canvas.SetGrid(1,1)
canvas.SetLeftMargin(0.12)
canvas.SetTopMargin(0.15)
canvas.SetBottomMargin(0.12)

# for RHS legend:
canvas.SetTopMargin(0.05)
canvas.SetBottomMargin(0.1)
canvas.SetRightMargin(0.15)

ROOT.gStyle.SetTitleFontSize(0.04)

nchannels = len(struck_analysis_parameters.channel_map) 
#nchannels = 32 # FIXME -- for DT unit!!
bits = 14

print "%i channels" % nchannels

def process_file(filename=None, n_plots_total=0):

    # options ------------------------------------------
    is_for_paper = False # change some formatting
    threshold = 500 # keV
    #threshold = 0
    #threshold = 1250 # keV
    #threshold = 570 # keV, for generating multi-page PDF
    #threshold = 50 # ok for unshaped, unamplified data
    #energy_offset = 100*700 # keV, space between traces
    energy_offset = 40000.0/nchannels
    
    units_to_use = 0 # 0=keV, 1=ADC units, 2=mV

    do_fft = False
    do_fit = False #fit sine to sum wfm

    # if this is 1.0 there is no effect:
    pmt_shrink_scale = 1.0 # shrink PMT signal by an additional factor so it doesn't set the graphical scale

    #------------------------------------------------------

    # figure out which units we are using, to construct the file name
    units = "keV"
    if units_to_use == 1:
        units = "AdcUnits"
    elif units_to_use == 2:
        units = "mV"


    # y axis limits:
    y_min = -250 # keV
    if units_to_use == 1:
        y_min = -50 # ADC units
    elif units_to_use == 2:
        y_min = -5 # mV
    #y_min = -20000

    #y_max = 31500 # keV
    #y_max = nchannels*500+250 # keV
    y_max = nchannels*energy_offset # +250 # keV
    #y_max = (nchannels+3)*energy_offset #For SUM WF
    if units_to_use == 1:
        y_max = 200 # ADC units
    elif units_to_use == 2:
        y_max = 40 # mV

    #If input filename is null assume we want to examine the most recent file
    if(filename == None):
        # example name: SIS3316Raw_20160712204526_1.bin
        output  = commands.getstatusoutput("ls -rt tier1_SIS3316Raw_*.root | tail -n1")
        filename = output[1]
        print "--> using most recent NGM file, ", filename

    print "--> processing file", filename

    calibration_values = struck_analysis_parameters.calibration_values
    channel_map = struck_analysis_parameters.channel_map
    pmt_channel = struck_analysis_parameters.pmt_channel
    print "pmt_channel:", pmt_channel

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    sipm_channels_to_use   = struck_analysis_parameters.sipm_channels_to_use
    dead_channels          = struck_analysis_parameters.dead_channels
    nchannels_good         = nchannels - sum(dead_channels)  
    energy_start_time_microseconds = struck_analysis_parameters.energy_start_time_microseconds

    channels = []
    for (channel, value) in enumerate(charge_channels_to_use):
        print "Charge Channel to use", channel, value
        #if value is not 0: channels.append(channel)
        channels.append(channel)
    print "there are %i charge channels" % len(channels)
    if pmt_channel != None:
        channels.append(pmt_channel)
    n_channels = len(channels)
    colors = struck_analysis_parameters.get_colors()

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    #print "basename:", basename

    # open the root file and grab the tree
    root_file = ROOT.TFile(filename)
    tree = root_file.Get("HitTree")
    n_entries = tree.GetEntries()
    print "%i entries in tree" % n_entries

    # get NGM system config
    sys_config = root_file.Get("NGMSystemConfiguration")
    card0 = sys_config.GetSlotParameters().GetParValueO("card",0)
    card1 = sys_config.GetSlotParameters().GetParValueO("card",1)

    print "%i entries, %i channels, %.2f events" % (
        n_entries, 
        len(charge_channels_to_use),
        n_entries/len(charge_channels_to_use),
    )

    sampling_freq_Hz = struck_analysis_parameters.get_clock_frequency_Hz_ngm(card0.clock_source_choice)
    print "sampling_freq_Hz: %.1f MHz" % (sampling_freq_Hz/1e6)
    #n_samples_to_avg = int(200*sampling_freq_Hz/sampling_freq_Hz) # n baseline samples to use for energy 
    n_samples_to_avg = int(struck_analysis_parameters.n_baseline_samples)
    print "n_samples_to_avg", n_samples_to_avg
    energy_start_time_samples = int(energy_start_time_microseconds*struck_analysis_parameters.microsecond*sampling_freq_Hz/struck_analysis_parameters.second)
    
    channel_map = struck_analysis_parameters.channel_map

    tree.GetEntry(0) # use 0th entry to get some info that we don't expect to change... 
    trace_length_us = tree.HitTree.GetNSamples()/sampling_freq_Hz*1e6
    print "length in microseconds:", trace_length_us

    trigger_time = card0.pretriggerdelay_block[0]/sampling_freq_Hz*1e6
    print "trigger time: [microseconds]", trigger_time
    if "crosstalk" in basename: trigger_time = 5.0

    frame_hist = ROOT.TH1D("hist", "", tree.HitTree.GetNSamples(), 0, trace_length_us+0.5)
    #frame_hist = ROOT.TH1D("hist", "", int(tree.HitTree.GetNSamples()*33.0/32.0), 0, 25.0)
    frame_hist.SetXTitle("Time [#mus]")
    sum_offset = 51500
    frame_hist.SetYTitle("Energy (with arbitrary offsets) [keV]")
    if units_to_use == 1: # ADC units
        frame_hist.SetYTitle("ADC units")
        sum_offset = 50
    elif units_to_use == 2: # mV
        frame_hist.SetYTitle("mV")
        sum_offset = 10

    frame_hist.GetYaxis().SetTitleOffset(1.6)

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

    #legend = ROOT.TLegend(0.15, 0.86, 0.9, 0.99)
    legend = ROOT.TLegend(
        1.005 - canvas.GetRightMargin(), 
        canvas.GetBottomMargin(), 
        0.99, 
        1.0-canvas.GetTopMargin()
    )
    #legend.SetNColumns(7)
    #legend.SetBorderSize(0)

    # set up some placeholder hists for the legend
    hists = []
    for (i, channel) in enumerate(channels):
        #print "i=%i, ch=%i (%s)" % (i, channel, channel_map[channel])
        hist = ROOT.TH1D("hist%i" % channel,"",10,0,10)
        if "XChannels" in basename: channel +=15
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
    y_min_old = y_min
    # use while loop instead of for loop so we can modify i_entry if needed
    while i_entry < n_entries:
        tree.GetEntry(i_entry)
        timestamp_first = tree.HitTree.GetRawClock()
        #print "At entry %i With Time stamp %i" % (i_entry, timestamp_first)

        canvas.SetLogy(0)
        canvas.SetLogx(0)

        # reset at start of each event
        y_max = y_max_old 
        y_min = y_min_old
       
        chargeEnergy = 0.0

        frame_hist.Draw()
        wfm_length = tree.HitTree.GetNSamples()
        sum_wfm = [0]*wfm_length
        sum_wfm0 = [0]*wfm_length
        sum_wfm1 = [0]*wfm_length

        sum_sipm_wfm = np.zeros(wfm_length)

        #print "==> entry %i of %i | charge energy: %i" % ( i_entry, n_entries, chargeEnergy,)
      
        legend.Clear()
        legend_entries = [""]*nchannels

        # loop over all channels in the event:
        sum_energy = 0.0
        sum_energy_light = 0.0
        n_high_rms = 0
        n_signals = 0
        n_strips = 0

        graph_dict = {}
        
        found_channels = []
        isdead_event = False
        timestamp_diff = 0.0
        
        for i_channel in xrange(nchannels):
            if i_channel > 0 : tree.GetEntry(i_entry)

            slot = tree.HitTree.GetSlot()
            card_channel = tree.HitTree.GetChannel() # 0 to 16 for each card
            timestamp = tree.HitTree.GetRawClock()
            timestamp_diff = timestamp - timestamp_first
            channel = card_channel + 16*slot # 0 to 31

            if timestamp_diff > 0.5: 
                print "Moving on to next event after finding next time stamp", i_entry, timestamp_diff, channel
                break

            #Don't increment until after we confirm this entry is part of current event
            i_entry +=1 

            if dead_channels[channel] > 0: 
                isdead_event = True
                print "Break after finding dead channel", i_entry, channel
                break

            if channel in found_channels:
                print "Entry %i Channel %i" % (i_entry, channel)
                raw_input("Found a channel more than once is this ok????? Pause here")
            found_channels.append(channel)

            #print "Entry %i time %i time diff %.2f WF for slot %i and card-ch %i and true ch %i" % (i_entry, timestamp, timestamp_diff, slot, card_channel, card_channel + 16*slot)

            card = sys_config.GetSlotParameters().GetParValueO("card",slot)

            # for crosstalk studies:
            if "XChannels" in basename: 
                #print "This is crosstalk study!!"
                channel += 16-1
                #print "channel", channel

            gain = card.gain[card_channel]
            # gain: 1 = 2V; 0 = 5V
            voltage_range_mV = struck_analysis_parameters.get_voltage_range_mV_ngm(gain)

            try:
                color = colors[channel]
            except IndexError:
                color = ROOT.kBlack

            multiplier = calibration_values[channel] # keV
            if units_to_use == 1: # ADC units
                multiplier = 1.0
            elif units_to_use == 2: # mV
                multiplier = voltage_range_mV/pow(2,bits)
            if channel == pmt_channel:
                multiplier /= pmt_shrink_scale
            if sipm_channels_to_use[channel] > 0:
                multiplier = 1.3

            if False: # print debug output
                print "entry %i | slot %i | card ch %i | ch %i | multiplier: %.4f" % (
                    i_entry, 
                    slot,
                    card_channel,
                    channel, 
                    multiplier,
                )

            graph = tree.HitTree.GetGraph()
            graph_dict_name = "graph_ch%i" % channel
            graph_dict[graph_dict_name] = graph

            #--------------------------------------------------------------------------------------
            #------------------------------------------SiPM filter--------------------------
            #--------------------------------------------------------------------------------------

            if sipm_channels_to_use[channel] > 0:
                #Filter the sipm channels
                sipm_wfm = np.array([graph.GetY()[isamp] for isamp in xrange(graph.GetN())])
                sipm_fft = np.fft.rfft(sipm_wfm)
                sipm_fft[600:] = 0
                sipm_wfm_filter = np.fft.irfft(sipm_fft)
                sum_sipm_wfm += sipm_wfm_filter
                for isamp in xrange(graph.GetN()):
                    x = graph.GetX()[isamp]
                    graph.SetPoint(isamp,x,sipm_wfm_filter[isamp])

            #--------------------------------------------------------------------------------------
            #------------------------------------------Energy Calculation--------------------------
            #--------------------------------------------------------------------------------------
            # as in http://exo-data.slac.stanford.edu/exodoc/src/EXOBaselineRemover.cxx.html#48
            
            baseline = 0.0
            energy = 0.0
            baseline_avg_sq = 0.0
            energy_avg_sq = 0.0
            for i_sample in xrange(n_samples_to_avg):
                y = graph.GetY()[i_sample]
                y2 = graph.GetY()[i_sample+energy_start_time_samples]
                baseline += y / n_samples_to_avg
                energy += y2 / n_samples_to_avg
                baseline_avg_sq += y*y/n_samples_to_avg
                energy_avg_sq += y2*y2/n_samples_to_avg
            rms_noise = math.sqrt(baseline_avg_sq-baseline*baseline)*multiplier
            try:
                energy_noise = math.sqrt(energy_avg_sq-energy*energy)*multiplier
            except ValueError:
                energy_noise = 0.0
            energy = (energy - baseline)*multiplier
            
            #--------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------

            if channel == pmt_channel:
                # pmt energy is proportional to max, which occurs ~ 27
                # samples after trigger
                i_sample = int(struck_analysis_parameters.n_baseline_samples + 27)
                energy = (graph.GetY()[i_sample]-baseline)*multiplier
                energy *= pmt_shrink_scale
                #energy = (graph.GetMaximum()-baseline)*multiplier
                print energy, baseline, multiplier
            
            if sipm_channels_to_use[channel] > 0:
                #print "SiPM Channel Energy", channel
                wf = []
                for i_sample in xrange(graph.GetN()):
                    #print i_sample, graph.GetY()[i_sample]
                    wf.append(graph.GetY()[i_sample])
                energy = (np.max(wf) - baseline)*multiplier
                #print "Maximum is", graph.GetMaximum(), np.argmax(wf), np.max(wf), np.mean(wf)
                #print dir(graph)
                #raw_input()
                #energy = np.max(graph.GetY())

            #--------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------


            # add an offset so the channels are drawn at different levels
            offset = channel*energy_offset

            if "XChannels" in basename: offset = (channel-16)*100 

            graph.SetLineColor(color)
            #Subtract off the baseline and apply calibration
            fcn_string = "(y - %s)*%s + %s" % ( baseline, multiplier, offset)
            #print "fcn_string:", fcn_string
            fcn = ROOT.TF2("fcn",fcn_string)
            graph.Apply(fcn)
            # convert x axis to microseconds
            for i_point in xrange(graph.GetN()):
                x = graph.GetX()[i_point]
                y = graph.GetY()[i_point]
                if y > y_max: y_max = y
                #if y < y_min: y_min = y
                graph.SetPoint(i_point, x/sampling_freq_Hz*1e6, y)

            graph.SetLineWidth(2)
            
            #----------------------------------------------------------------------------------------
            #----------------------------Find Signals above Threshold--------------------------------
            #----------------------------Add Up Charge and Light Energy------------------------------
            #----------------------------------------------------------------------------------------
            #signal_threshold = 5.0*rms_noise/10.0
            signal_threshold = 5.0*energy_noise/10.0
            rms_threshold = struck_analysis_parameters.rms_keV[channel] + struck_analysis_parameters.rms_keV_sigma[channel]*4.0
            if charge_channels_to_use[channel] > 0:
                if energy > signal_threshold:
                    if not is_for_paper: graph.SetLineWidth(4) # don't bold for paper
                    sum_energy += energy
                    n_signals +=1
                    n_strips += struck_analysis_parameters.channel_to_n_strips_map[channel]
                if rms_noise >  rms_threshold:
                    n_high_rms += 1
                    #graph.SetLineColor(ROOT.kBlack)

            if sipm_channels_to_use[channel] > 0:
                sum_energy_light += energy

            graph.Draw("l")
            #print "\t entry %i, ch %i, slot %i" % ( i_entry-1, channel, slot,)
            # construct sum wfm
            for i_point in xrange(tree.HitTree.GetNSamples()):
                y = graph.GetY()[i_point]
                if channel != pmt_channel:
                    sum_wfm[i_point] = sum_wfm[i_point] + y - offset

                    if slot == 0:
                        sum_wfm0[i_point] = sum_wfm0[i_point] + y - offset
                    if slot == 1:
                        sum_wfm1[i_point] = sum_wfm1[i_point] + y - offset
                    
            # legend uses hists for color/fill info
            leg_entry= "%s  %.1f" % (
                channel_map[channel], 
                energy,
                #rms_noise,
            ) 
            if charge_channels_to_use[channel] > 0:
                if energy > signal_threshold:
                    #leg_entry = "#bf{%s}" % leg_entry
                    leg_entry = "%s #leftarrow" % leg_entry

            i_legend_entry = channel
            if "XChannels" in basename: i_legend_entry -= 15 # crosstalk studies
            legend_entries[i_legend_entry] = leg_entry

            #------------------------------------------------------------------------------------------
            # end loop over channels
            #------------------------------------------------------------------------------------------

        if isdead_event: 
            print "Skipping event where we found a dead channel"
            continue
        nfound = len(found_channels)
        if nfound < nchannels_good:
            raw_input("Found %i channels which is less than %i good channels" % (nfound, nchannels_good))

        print "Found Channels", len(found_channels), found_channels

        print "---------> entry %i of %i (%.1f percent), %i plots so far" % (
            i_entry/nchannels,  # current event
            n_entries/nchannels,  # n events in file                       
            100.0*i_entry/n_entries, # percent done
            n_plots,
        ) 
        #if n_high_rms <= 0: continue
        #if sum_energy < threshold or sum_energy > 650: continue
        print "n_signals:", n_signals, " | sum_energy: %.1f" % sum_energy
        if sum_energy < threshold: continue
        if is_for_paper:
          if sum_energy > threshold + 40: continue
          if n_signals != 2: continue
          if n_strips != 2: continue

        # create sum graphs; add offsets & set x-coords
        sum_graph = ROOT.TGraphErrors()
        sum_graph0 = ROOT.TGraphErrors()
        sum_graph1 = ROOT.TGraphErrors()
        sum_graph_sipm = ROOT.TGraphErrors()

        rms_noise = 0.0
        sum_sipm_wfm -= np.mean(sum_sipm_wfm[:100])
        for i_point in xrange(len(sum_wfm)):
            sum_graph.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm[i_point]+sum_offset)
            #sum_graph.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm[i_point])
            sum_graph.SetPointError(i_point, 0.0, 0.1*multiplier)
            sum_graph0.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm0[i_point]+sum_offset*2)
            sum_graph0.SetPointError(i_point, 0.0, 0.1*multiplier)
            sum_graph1.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm1[i_point]+sum_offset*3)
            sum_graph1.SetPointError(i_point, 0.0, 0.1*multiplier)

            sum_graph_sipm.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_sipm_wfm[i_point]+sum_offset)
            sum_graph_sipm.SetPointError(i_point, 0.0, 0.1*multiplier)

            if i_point < n_samples_to_avg:
                rms_noise += pow(sum_wfm[i_point], 2.0)/n_samples_to_avg
        

        rms_noise = math.sqrt(rms_noise)

        #------------------------------------------------------------------------------------------
        #---------------------------------Fit Sum WF to Sin Wave-----------------------------------
        #------------------------------------------------------------------------------------------
        fit_fcn = ROOT.TF1("fit_fcn", "[0] + [1]*sin(2*pi*(x*[2]+[3]))", 0, trace_length_us)
        fit_fcn.SetLineColor(ROOT.kGreen+2)

        # set parameter names
        fit_fcn.SetParName(0, "offset")
        fit_fcn.SetParName(1, "amplitude")
        fit_fcn.SetParName(2, "freq [MHz]")
        fit_fcn.SetParName(3, "phase shift")

        # set initial guesses
        fit_fcn.SetParameter(0, sum_offset) # offset
        fit_fcn.SetParameter(1, 3.0) # amplitude
        fit_fcn.SetParameter(2, 0.445) # freq, MHz
        fit_fcn.SetParameter(3, 0.5) # phase shift

        # set guesses of parameter uncertainty
        fit_fcn.SetParError(0, sum_offset) # offset
        fit_fcn.SetParError(1, 2.0) # amplitude
        fit_fcn.SetParError(2, 0.1) # freq, MHz
        fit_fcn.SetParError(3, 0.5) # phase shift

        if do_fit: # do the fit
            fit_result = sum_graph.Fit(fit_fcn, "SRM")
            print "freq: ", fit_fcn.GetParameter(2)
        """
        sum_graph.Draw("xl")
        sum_graph0.SetLineColor(ROOT.kBlue)
        sum_graph0.Draw("xl")
        sum_graph1.SetLineColor(ROOT.kRed)
        sum_graph1.Draw("xl")
        """
        #sum_graph_sipm.Draw("xl")
        sum_graph_sipm.SetLineColor(ROOT.kRed)
        #------------------------------------------------------------------------------------------
        #------------------------------End Fit Sum WF to Sin Wave-----------------------------------
        #------------------------------------------------------------------------------------------

        pave_text.Clear()
        pave_text.AddText("page %i, event %i" % (n_plots+1, i_entry/nchannels))
        pave_text.AddText("%s" % basename)
        #pave_text.Draw()

        pave_text2.Clear()
        pave_text2.AddText("#SigmaE_{C} = %i" % chargeEnergy)
        pave_text2.AddText("t=%.4fs" % (tree.HitTree.GetRawClock()/sampling_freq_Hz))
        #pave_text2.Draw()

        if units_to_use == 0: y_max += 100

        frame_hist.SetMinimum(y_min)
        if "crosstalk" in basename: frame_hist.SetMaximum(100*16)
        frame_hist.SetMaximum(y_max)
        title = ""
        if not is_for_paper:
            title += "Event %i | " % ((i_entry-1)/nchannels)
        title += "Sum Ionization Energy: %.1f keV " % sum_energy
        title += "Sum Light Energy: %.1f ADC " % sum_energy_light
        if not is_for_paper:
            title += " | time stamp: %i | page %i" % (
                tree.HitTree.GetRawClock(),
                n_plots+1,
            )

        frame_hist.SetTitle(title)
        frame_hist.SetTitleSize(0.2, "t")

        for i in xrange(nchannels):
            index = (nchannels-1) - i # fill from top down
            if legend_entries[index] != "":
                legend.AddEntry( hists[index], legend_entries[index], "f")

        #legend.AddEntry(sum_graph, "sum %.1f" % rms_noise,"l")
        #legend.AddEntry(sum_graph, "sum %.1f" % sum_energy,"p")
        #legend.AddEntry(sum_graph0, "Y sum slot 0","l")
        #legend.AddEntry(sum_graph1, "X sum slot 1","l")
        #legend.AddEntry(sum_graph_sipm, "SiPM Sum","l")

        # line to show trigger time
        print trigger_time, "-------------------------------------------------------------"
        line = ROOT.TLine(trigger_time, y_min, trigger_time,y_max)
        line.SetLineWidth(2)
        line.SetLineStyle(7)
        #line.Draw()

        max_drift_time = struck_analysis_parameters.max_drift_time
        line1 = ROOT.TLine(trigger_time+max_drift_time, y_min, trigger_time+max_drift_time,y_max)
        line1.SetLineWidth(2)
        line1.SetLineStyle(7)
        line1.Draw()
        print "Trigger Lines at", trigger_time, trigger_time+max_drift_time

        legend.Draw()
        frame_hist.SetTitleSize(0.02, "t")
        canvas.Update()
        n_plots += 1
        print "--> Event %i, %i of %i plots so far" % (i_entry/nchannels, n_plots, n_plots_total)

        if not ROOT.gROOT.IsBatch(): 

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

        else: # batch mode
            # if we run in batch mode, print a multi-page canvas
            #plot_name = "EventsWithChargeAbove%ikeV_6thLXe.pdf" % threshold
            
            plot_name = "%s_%s.pdf" % (basename, units) # the pdf file name

            if n_plots == 1: # start the file
                canvas.Print("%s[" % plot_name)
            
            routput_name = "event%i.root" % int((i_entry-1)/nchannels)
            print "Output Root File", routput_name
            routput = ROOT.TFile(routput_name, "RECREATE")
            for key in graph_dict:
                graph_dict[key]
                routput.WriteTObject(graph_dict[key], key)
            routput.Close()
            #raw_input()
            
            canvas.Print(plot_name)

        if do_fft: # calc & draw FFT

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
                x = i_point*sampling_freq_Hz/1e3/len(sum_wfm)  # kHz
                fft_graph.SetPoint(fft_graph.GetN(), x, abs(sum_fft[i_point]))
                fft_graph0.SetPoint(fft_graph0.GetN(), x, abs(sum_fft0[i_point]))
                fft_graph1.SetPoint(fft_graph0.GetN(), x, abs(sum_fft1[i_point]))
                #if  abs(sum_fft[i_point]) > 1e4:
                #    print "freq=%s kHz | val = %.2e" % ( x*1e3, abs(sum_fft[i_point]))

            canvas.SetLogy(1)
            canvas.SetLogx(1)
            fft_graph.Draw("alp")
            fft_hist = fft_graph.GetHistogram()
            fft_hist.SetXTitle("Freq [kHz]")
            fft_hist.SetTitle("Sum wfm FFT")
            fft_hist.GetXaxis().SetTitleOffset(1.2)
            fft_hist.SetMinimum(100)
            fft_hist.SetMaximum(1e6)
            if sampling_freq_Hz == 250e6:
                fft_hist.SetMinimum(100)
                fft_hist.SetMaximum(1e6)
            if units_to_use == 2:
                fft_hist.SetMinimum(1)
                fft_hist.SetMaximum(1e4)
                if sampling_freq_Hz == 250.0e6:
                    fft_hist.SetMinimum(1)
                    fft_hist.SetMaximum(1e6)
            fft_hist.Draw()
            fft_graph.Draw("l same")
            fft_graph0.Draw("l same")
            fft_graph1.Draw("l same")
            canvas.Update()

            if not ROOT.gROOT.IsBatch(): # interactive mode
                val = raw_input("--> FFT -- enter to continue (q to quit, p to print) ")
                if val == 'q': 
                    sys.exit()
                elif val == 'p':
                    canvas.Print("%s_FFT_event_%i.pdf" % (basename, n_plots-1))

            else: # batch mode
                canvas.Print(plot_name)

            # end test of do_fft



        if n_plots >= n_plots_total:
            print "quitting..."
            break

        # end loop over entries
    
    if ROOT.gROOT.IsBatch(): # end multi-page pdf file
        canvas.Print("%s]" % plot_name)
    return n_plots


if __name__ == "__main__":

    n_plots_total = 100
    #n_plots_total = 3
    n_plots_so_far = 0
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            n_plots_so_far += process_file(filename, n_plots_total)
    else:
        process_file(n_plots_total=n_plots_total)

