#!/usr/bin/env python

"""
This script draws events from NGM root file(s). 

arguments [NGM root files of events: tier1_SIS3316Raw_*.root]
"""

import os
import sys
import math
import commands
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
canvas.SetRightMargin(0.12)

ROOT.gStyle.SetTitleFontSize(0.04)


def process_file(filename=None, n_plots_total=0):

    # options ------------------------------------------
    threshold = 1000 # keV
    #threshold = -20000
    #threshold = 1250 # keV
    #threshold = 570 # keV, for generating multi-page PDF
    #threshold = 50 # ok for unshaped, unamplified data

    units_to_use = 0 # 0=keV, 1=ADC units, 2=mV

    do_fft = False
    do_fit = False #fit sine to sum wfm

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

    y_max = 31500 # keV
    y_max = 31*500+250 # keV
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
    channels = []
    for (channel, value) in enumerate(charge_channels_to_use):
        #print channel, value
        #if value is not 0: channels.append(channel)
        channels.append(channel)
    print "there are %i charge channels" % len(channels)
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
    n_samples_to_avg = int(200*sampling_freq_Hz/25e6) # n baseline samples to use for energy 

    channel_map = struck_analysis_parameters.channel_map

    tree.GetEntry(0) # use 0th entry to get some info that we don't expect to change... 
    trace_length_us = tree.HitTree.GetNSamples()/sampling_freq_Hz*1e6
    print "length in microseconds:", trace_length_us

    trigger_time = card0.pretriggerdelay_block[0]/sampling_freq_Hz*1e6
    print "trigger time: [microseconds]", trigger_time

    #frame_hist = ROOT.TH1D("hist", "", int(tree.HitTree.GetNSamples()*33.0/32.0), 0, trace_length_us+1)
    frame_hist = ROOT.TH1D("hist", "", int(tree.HitTree.GetNSamples()*33.0/32.0), 0, 25.0)
    frame_hist.SetXTitle("Time [#mus]")
    sum_offset = 400
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

        #print "==> entry %i of %i | charge energy: %i" % ( i_entry, n_entries, chargeEnergy,)
      
        legend.Clear()
        legend_entries = [""]*32

        # loop over all channels in the event:
        sum_energy = 0.0
        for i in xrange(32):

            tree.GetEntry(i_entry)
            i_entry += 1
            slot = tree.HitTree.GetSlot()
            card_channel = tree.HitTree.GetChannel() # 0 to 16 for each card
            channel = card_channel + 16*slot # 0 to 31
            card = sys_config.GetSlotParameters().GetParValueO("card",slot)

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
                multiplier = voltage_range_mV/pow(2,14)


            if False: # print debug output
                print "entry %i | slot %i | card ch %i | ch %i | multiplier: %.4f" % (
                    i_entry, 
                    slot,
                    card_channel,
                    channel, 
                    multiplier,
                )

            graph = tree.HitTree.GetGraph()

            baseline = 0.0
            energy = 0.0
            for i_sample in xrange(n_samples_to_avg):
                baseline += graph.GetY()[i_sample] / n_samples_to_avg
                energy += graph.GetY()[graph.GetN() - i_sample - 1] / n_samples_to_avg
            energy = (energy - baseline)*multiplier
            if channel != pmt_channel:
                if energy > 10.0:
                    sum_energy += energy

            rms_noise = 0.0
            for i_sample in xrange(n_samples_to_avg):
                rms_noise += pow(graph.GetY()[i_sample]-baseline, 2.0)/n_samples_to_avg
            rms_noise = math.sqrt(rms_noise)*multiplier
                

            # add an offset so the channels are draw at different levels
            offset = channel*500

            graph.SetLineColor(color)
            fcn_string = "(y - %s)*%s + %s" % ( baseline, multiplier, offset)
            #print "fcn_string:", fcn_string
            fcn = ROOT.TF2("fcn",fcn_string)
            graph.Apply(fcn)
            # convert x axis to microseconds
            for i_point in xrange(graph.GetN()):
                x = graph.GetX()[i_point]
                y = graph.GetY()[i_point]
                if y > y_max: y_max = y
                if y < y_min: y_min = y

                graph.SetPoint(i_point, x/sampling_freq_Hz*1e6, y)

            graph.SetLineWidth(2)
            if energy>20.0:
                graph.SetLineWidth(5)

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
            legend_entries[channel] = "%s  %.1f" % (
                channel_map[channel], 
                energy,
                #rms_noise,
            ) 

            # end loop over channels

        if sum_energy < threshold: continue

        # create sum graphs; add offsets & set x-coords
        sum_graph = ROOT.TGraphErrors()
        sum_graph0 = ROOT.TGraphErrors()
        sum_graph1 = ROOT.TGraphErrors()

        rms_noise = 0.0
        for i_point in xrange(len(sum_wfm)):
            sum_graph.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm[i_point]+sum_offset)
            #sum_graph.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm[i_point])
            sum_graph.SetPointError(i_point, 0.0, 0.1*multiplier)
            sum_graph0.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm0[i_point]+sum_offset*2)
            sum_graph0.SetPointError(i_point, 0.0, 0.1*multiplier)
            sum_graph1.SetPoint(i_point, i_point/sampling_freq_Hz*1e6, sum_wfm1[i_point]+sum_offset*3)
            sum_graph1.SetPointError(i_point, 0.0, 0.1*multiplier)

            if i_point < n_samples_to_avg:
                rms_noise += pow(sum_wfm[i_point], 2.0)/n_samples_to_avg

        rms_noise = math.sqrt(rms_noise)

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

        pave_text.Clear()
        pave_text.AddText("page %i, event %i" % (n_plots+1, i_entry/32))
        pave_text.AddText("%s" % basename)
        #pave_text.Draw()

        pave_text2.Clear()
        pave_text2.AddText("#SigmaE_{C} = %i" % chargeEnergy)
        pave_text2.AddText("t=%.4fs" % (tree.HitTree.GetRawClock()/sampling_freq_Hz))
        #pave_text2.Draw()

        if units_to_use == 0: y_max += 100

        frame_hist.SetMinimum(y_min)
        frame_hist.SetMaximum(y_max)
        frame_hist.SetTitle("Event %i | Sum Ionization Energy: %.1f keV" % (i_entry/32, sum_energy))
        frame_hist.SetTitleSize(0.2, "t")

        for i in xrange(32):
            index = 31 - i # fill from top down
            if legend_entries[index] != "":
                legend.AddEntry( hists[index], legend_entries[index], "f")

        #legend.AddEntry(sum_graph, "sum %.1f" % rms_noise,"l")
        #legend.AddEntry(sum_graph, "sum %.1f" % sum_energy,"p")
        #legend.AddEntry(sum_graph0, "Y sum slot 0","l")
        #legend.AddEntry(sum_graph1, "X sum slot 1","l")

        # line to show trigger time
        line = ROOT.TLine(trigger_time, y_min, trigger_time,y_max)
        line.SetLineWidth(2)
        line.SetLineStyle(7)
        line.Draw()

        line1 = ROOT.TLine(trigger_time+9.09, y_min, trigger_time+9.09,y_max)
        line1.SetLineWidth(2)
        line1.SetLineStyle(7)
        line1.Draw()

        legend.Draw()
        frame_hist.SetTitleSize(0.02, "t")
        canvas.Update()
        n_plots += 1
        print "--> %i of %i plots so far" % (n_plots, n_plots_total)

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


        if ROOT.gROOT.IsBatch() and n_plots >= n_plots_total: # end multi-page pdf file
            canvas.Print("%s]" % plot_name)

        if n_plots >= n_plots_total:
            print "quitting..."
            sys.exit()

        # end loop over entries
    
    return n_plots


if __name__ == "__main__":

    n_plots_total = 100
    n_plots_so_far = 0
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            n_plots_so_far += process_file(filename, n_plots_total)
    else:
        process_file(n_plots_total=n_plots_total)

