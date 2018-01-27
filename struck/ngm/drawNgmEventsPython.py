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
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as PdfPages
plt.ion()

import ROOT
ROOT.gROOT.SetBatch(True) # uncomment to draw multi-page PDF

import subprocess
root_version = subprocess.check_output(['root-config --version'], shell=True)
isROOT6 = False
if '6.1.0' in root_version or '6.04/06' in root_version:
    print "Found ROOT 6"
    isROOT6 = True

if os.getenv("EXOLIB") is not None and not isROOT6:
    try:
        print "loading libEXOROOT"
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
    except:
        print "Skip it"
        pass

from ROOT import EXOTrapezoidalFilter
from ROOT import EXOBaselineRemover
from ROOT import EXODoubleWaveform
from ROOT import TObjString
from ROOT import EXOSmoother

from struck import struck_analysis_parameters

#-----------------------------------------------------------
#----------------------------------------------------------


nchannels = len(struck_analysis_parameters.channel_map)
#nchannels = 32 # FIXME -- for DT unit!!
bits = 14

threshold = 0 # keV
energy_offset = 33000.0/nchannels
sum_offset = 51500

# if this is 1.0 there is no effect:
pmt_shrink_scale = 1.0 # shrink PMT signal by an additional factor so it doesn't set the graphical scale

units_to_use = 0 # 0=keV, 1=ADC units, 2=mV
# figure out which units we are using, to construct the file name
units = "keV"
if units_to_use == 1:
    units = "AdcUnits"
elif units_to_use == 2:
    units = "mV"

calibration_values = struck_analysis_parameters.calibration_values    
channel_map = struck_analysis_parameters.channel_map
pmt_channel = struck_analysis_parameters.pmt_channel

charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
sipm_channels_to_use   = struck_analysis_parameters.sipm_channels_to_use
dead_channels          = struck_analysis_parameters.dead_channels
nchannels_good         = nchannels - sum(dead_channels)
energy_start_time_microseconds = struck_analysis_parameters.energy_start_time_microseconds
max_drift_time = struck_analysis_parameters.max_drift_time

do_sipm_filter = True

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

n_samples_to_avg = int(struck_analysis_parameters.n_baseline_samples)
print "n_samples_to_avg", n_samples_to_avg

#-----------------------------------------------------------
#----------------------------------------------------------

#Function to get the most recent tier1 file
def get_recent():
    # example name: SIS3316Raw_20160712204526_1.bin
    output  = commands.getstatusoutput("ls -rt tier1_SIS3316Raw_*.root | tail -n1")
    filename = output[1]
    print "--> using most recent NGM file, ", filename
    return filename


#Main Process Loop
def process_file(filename=None, n_plots_total=0):
    
    #If no file name is supplied find the most recent tier1 file in current directory
    if(filename == None): filename = get_recent()
    print "--> processing file", filename
    
    #Strip off the basename
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    plot_name = "%s_%s.pdf" % (basename, units) # the pdf file name
    pdf = PdfPages.PdfPages(plot_name)

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

    #Get the sampling frequency 
    sampling_freq_Hz = struck_analysis_parameters.get_clock_frequency_Hz_ngm(card0.clock_source_choice)
    print "sampling_freq_Hz: %.1f MHz" % (sampling_freq_Hz/1e6)
    #convert the start time for the average to sample number
    energy_start_time_samples = int(energy_start_time_microseconds*struck_analysis_parameters.microsecond*sampling_freq_Hz/struck_analysis_parameters.second)
    
    #Get the first entry to setup some random parameters
    tree.GetEntry(0) # use 0th entry to get some info that we don't expect to change... 
    trace_length_us = tree.HitTree.GetNSamples()/sampling_freq_Hz*1e6
    print "length in microseconds:", trace_length_us
    trigger_time = card0.pretriggerdelay_block[0]/sampling_freq_Hz*1e6
    print "trigger time: [microseconds]", trigger_time
    
    #Now loop over the entries in the tree were each entry is a WF
    i_entry = 0
    n_plots = 0
    while i_entry < n_entries:
        tree.GetEntry(i_entry)
        
        #Get timestamp
        timestamp_first = tree.HitTree.GetRawClock()
        wfm_length = tree.HitTree.GetNSamples()
        
        #Zero out Calculated Values
        chargeEnergy = 0.0
        sum_energy = 0.0
        sum_energy_light = 0.0
        n_high_rms = 0
        n_signals = 0
        n_strips = 0
        found_channels = []
        isdead_event = False
        timestamp_diff = 0.0        

        #initilize the sum waveforms for this event
        sum_sipm_wfm  = np.zeros(wfm_length)
        sum_wfm       = np.zeros(wfm_length)
        sum_wfm0      = np.zeros(wfm_length)
        sum_wfm1      = np.zeros(wfm_length) 
        
        #Loop over expected number of channels in a real event
        for i_channel in xrange(nchannels):
            #Already have the first entry so only get new ones
            if i_channel > 0 : tree.GetEntry(i_entry)
            
            #Figure out the hardware channel 
            slot = tree.HitTree.GetSlot()
            card_channel = tree.HitTree.GetChannel() # 0 to 16 for each card
            channel = card_channel + 16*slot # 0 to 31            

            #Check timestamp to assosiate WFs with events
            timestamp = tree.HitTree.GetRawClock()
            timestamp_diff = timestamp - timestamp_first
            if timestamp_diff > 0.5:
                print "Moving on to next event after finding next time stamp", i_entry, timestamp_diff, channel
                break
            
            if True: print i_entry, channel, timestamp #Debug 

            #Don't increment until after we confirm this entry is part of current event
            i_entry +=1

            #Sanity check to make sure we didn't already find this channel.  
            #Should probably never happen since the timestamp check should weed these out
            if channel in found_channels:
                print "Entry %i Channel %i" % (i_entry, channel)
                raw_input("Found a channel more than once is this ok????? Pause here")
            found_channels.append(channel)
            
            #Get information about the card
            card = sys_config.GetSlotParameters().GetParValueO("card",slot)
            gain = card.gain[card_channel]
            # gain: 1 = 2V; 0 = 5V
            voltage_range_mV = struck_analysis_parameters.get_voltage_range_mV_ngm(gain)
            multiplier = calibration_values[channel] # keV            
            
            if units_to_use == 1: # ADC units
                multiplier = 1.0
            elif units_to_use == 2: # mV
                multiplier = voltage_range_mV/pow(2,bits)
            if channel == pmt_channel:
                multiplier /= pmt_shrink_scale
            if sipm_channels_to_use[channel] > 0:
                multiplier = 1.3
            
            #Get the WFM
            graph = tree.HitTree.GetGraph()
            wfm   = np.array([graph.GetY()[isamp] for isamp in xrange(graph.GetN())])
            
            #Filter the SiPM WF if necceasry
            if sipm_channels_to_use[channel] > 0 and do_sipm_filter: 
                sipm_fft = np.fft.rfft(wfm)
                sipm_fft[600:] = 0
                #sipm_wfm_filter = np.fft.irfft(sipm_fft)
                wfm   =  np.fft.irfft(sipm_fft)
            if sipm_channels_to_use[channel] > 0:
                sum_sipm_wfm += wfm
            
            #Get baseline and energy
            baseline      =  np.mean(wfm[0:n_samples_to_avg])
            baseline_rms  =  np.std(wfm[0:n_samples_to_avg])
            energy        =  np.mean(wfm[energy_start_time_samples:])
            energy_rms    =  np.std(wfm[energy_start_time_samples:])
            energy        = (energy - baseline)*multiplier
            
            wfm-=baseline

            if channel == pmt_channel:
                i_sample = int(struck_analysis_parameters.n_baseline_samples + 27)
                energy   = (wfm[i_sample]  - baseline)*multiplier          
            if sipm_channels_to_use[channel] > 0:
                energy = (np.max(wfm) - baseline)*multiplier
            
            #Quick signal Finding on Charge Channels            
            signal_threshold = 5.0*baseline_rms/10.0
            rms_threshold = struck_analysis_parameters.rms_keV[channel] + struck_analysis_parameters.rms_keV_sigma[channel]*4.0
            
            if charge_channels_to_use[channel] > 0:
                if energy > signal_threshold:
                    if not is_for_paper: graph.SetLineWidth(4) # don't bold for paper
                    sum_energy += energy
                    n_signals +=1
                    n_strips += struck_analysis_parameters.channel_to_n_strips_map[channel]    
                if baseline_rms>  rms_threshold:
                    n_high_rms += 1
            if sipm_channels_to_use[channel] > 0:
                sum_energy_light += energy

            #Smooth the charge WFs
            if charge_channels_to_use[channel]>0:
                exo_wfm = EXODoubleWaveform(wfm, len(wfm))
                new_wfm = EXODoubleWaveform(exo_wfm)
                smoother = EXOSmoother()
                smoother.SetSmoothSize(10)
                smoother.Transform(exo_wfm,new_wfm)
                wfm = np.array([new_wfm.At(i) for i in xrange(new_wfm.GetLength())])
            #End smoothing section
            
            #Sum the charge WFMs
            if charge_channels_to_use[channel]>0:
                sum_wfm += wfm
                if slot == 0: sum_wfm0 += wfm
                if slot == 1: sum_wfm1 += wfm
            
            leg_entry= "%s  %.1f" % ( channel_map[channel], energy)
            if charge_channels_to_use[channel] > 0:
                if energy > signal_threshold:
                    leg_entry = r"%s $/leftarrow$" % leg_entry
            i_legend_entry = channel
            #legend_entries[i_legend_entry] = leg_entry
            
            plt.figure(1)
            # add an offset so the channels are drawn at different levels
            offset = channel*energy_offset
            time_sample = np.arange(len(wfm))*(1./(sampling_freq_Hz))*1.e6
            plt.plot(time_sample, (wfm)+offset, linewidth=2.0, label=leg_entry)

        #Check if the channel is a dead channel
        if isdead_event:
            print "Skipping event where we found a dead channel"
            continue
        
        #Check we found all the good channels we expected to find
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
        
        fig1 = plt.figure(1)
        plt.axvline(trigger_time, linewidth=3.0, linestyle='--', c='k')
        plt.axvline(trigger_time+max_drift_time, linewidth=3.0, linestyle='--', c='k')
        plt.xlabel(r"Time [$\mu$s]",fontsize=16)
        plt.ylabel("Energy [arb]"  ,fontsize=16)
        plt.legend()
        plt.show()
        pdf.savefig(fig1)
        n_plots += 1
        #raw_input()
        plt.clf()

        plt.figure(2)
        plt.plot(time_sample, sum_wfm,  label='sum charge'  , linewidth=2)
        plt.plot(time_sample, sum_wfm0, label='sum charge-1', linewidth=2)
        plt.plot(time_sample, sum_wfm1, label='sum charge-2', linewidth=2)
        plt.legend()
        plt.show()
        #raw_input()
        plt.clf()

        plt.figure(3)
        plt.plot(time_sample, sum_sipm_wfm, linewidth=2)
        plt.show()
        #raw_input()
        plt.clf()
        
        if n_plots > n_plots_total: 
            print "Breaking because got the plots"
            break

    pdf.close()


if __name__ == "__main__":

    n_plots_total = 2
    n_plots_so_far = 0
    
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            n_plots_so_far += process_file(filename, n_plots_total)
    else:
        process_file(n_plots_total=n_plots_total)
