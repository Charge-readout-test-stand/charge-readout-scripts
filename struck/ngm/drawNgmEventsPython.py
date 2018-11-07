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
import matplotlib.gridspec as gridspec
import matplotlib.cm as cmx
import matplotlib.colors as colors


#plt.ion()
plt.ioff()

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

plot_fft = False
cut_sipm_win = True
sipm_twidth = 5.0
threshold = 0.0 # keV
lthreshold = 2000.0
energy_offset = 25000.0/nchannels
#energy_offset = 300000.0/nchannels
sum_offset = 51500
smooth_charge = False

#energy_offset_sipm = energy_offset*2.0#.1#*1.2
energy_offset_sipm  = energy_offset*1.0
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

do_sipm_filter = struck_analysis_parameters.do_sipm_filter
sipm_low_pass  = struck_analysis_parameters.sipm_low_pass

channels = []    
for (channel, value) in enumerate(charge_channels_to_use):        
    print "Charge Channel to use", channel, value
    #if value is not 0: channels.append(channel)
    channels.append(channel)
print "there are %i charge channels" % len(channels)
if pmt_channel != None:
    channels.append(pmt_channel)
n_channels = len(channels)
#colors = struck_analysis_parameters.get_colors()

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

def get_color_map( n ):
    #jet = plt.get_cmap('jet')
    #jet  = plt.get_cmap("Set1")
    jet   = plt.get_cmap("prism")
    cNorm  = colors.Normalize(vmin=0, vmax=n-1)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)
    outmap = []
    for i in range(n):
        outmap.append( scalarMap.to_rgba(i) )
    return outmap

def ch_to_color(ch):
    ncols = len(struck_analysis_parameters.channel_map)
    col_list = get_color_map(ncols)
    col_min  = 0
    col_max  = ncols+1
    col_range = np.linspace(col_min,col_max,ncols)
    cindex = np.argmin(np.abs(col_range-ch))
    return col_list[cindex]


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
    
    #Time setup
    fig1 = plt.figure(1)
    gs1 = gridspec.GridSpec(1,1)
    gs1.update(left=0.1, right=0.6)
    ax0 = plt.subplot(gs1[0])

    gs2 = gridspec.GridSpec(1,1)
    gs2.update(left=0.61, right=0.91)
    ax1 = plt.subplot(gs2[0])

    #FFT Plot Setup
    fig2 = plt.figure(2)
    gs3 = gridspec.GridSpec(1,1)
    gs3.update(left=0.1, right=0.35)
    ax3 = plt.subplot(gs3[0])

    gs4 = gridspec.GridSpec(1,1)
    gs4.update(left=0.36, right=0.91)
    ax4 = plt.subplot(gs4[0])


    #Now loop over the entries in the tree were each entry is a WF
    i_entry = 0
    n_plots = 0
    #sum_wfm_average = np.zeros((nchannels, 300))
    sum_wfm_average  = None
    while i_entry < n_entries:
        tree.GetEntry(i_entry)

        #Get timestamp
        timestamp_first = tree.HitTree.GetRawClock()
        wfm_length = tree.HitTree.GetNSamples()
        
        if i_entry == 0: sum_wfm_average = np.zeros((nchannels, wfm_length))

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
        cmax = 0
        cmin = 0
        smax = 0
        smin = 0
        cmax_fft = 0
        cmin_fft = 0
        smax_fft = 0
        smin_fft = 0
        #sum_wfm_average = np.zeros((nchannels, wfm_length))

        #Loop over expected number of channels in a real event
        for i_channel in xrange(nchannels):
            #Already have the first entry so only get new ones
            if i_channel > 0 : tree.GetEntry(i_entry)
            
            #Figure out the hardware channel 
            slot = tree.HitTree.GetSlot()
            card_channel = tree.HitTree.GetChannel() # 0 to 16 for each card
            channel = card_channel + 16*slot # 0 to 31            

            #Every other channel is switched in the 16-bit digi and all channel signals are inverted
            if struck_analysis_parameters.do_invert:
                if channel %2 == 0: channel+=1
                else:               channel-=1

            #Check timestamp to assosiate WFs with events
            timestamp = tree.HitTree.GetRawClock()
            timestamp_diff = timestamp - timestamp_first
            if timestamp_diff > 0.5:
                print "Moving on to next event after finding next time stamp", i_entry, timestamp_diff, channel
                break
            
            if False: print i_entry, channel, timestamp #Debug 

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
                multiplier = 1.0
                #multiplier = 100
            
            #Get the WFM
            graph = tree.HitTree.GetGraph()
            wfm   = np.array([graph.GetY()[isamp] for isamp in xrange(graph.GetN())])
            if struck_analysis_parameters.do_invert: wfm = -1.0*wfm
            wfm_fft = np.fft.rfft(wfm)
            fft_freq = np.fft.rfftfreq(len(wfm), d=1./sampling_freq_Hz)
            fft_freq *= 1e-6
            
            power_spec = wfm_fft*np.conj(wfm_fft)

            if sipm_channels_to_use[channel] > 0:
                #sum_wfm_average[channel] += wfm
                if np.max(power_spec[1:]) > smax_fft: smax_fft = np.max(power_spec[1:])
                if np.min(power_spec[1:]) < smin_fft: smin_fft = np.min(power_spec[1:])
                ax4.plot(fft_freq, wfm_fft*np.conj(wfm_fft), linewidth=2.0, label="%s"%channel_map[channel])
                #plt.ion()
                #plt.figure(60)
                #plt.plot(fft_freq,wfm_fft*np.conj(wfm_fft))
                #plt.yscale('log')
                #plt.ylim(min(power_spec[2:]), max(power_spec[2:]))
                #plt.show()
                #raw_input()
            elif charge_channels_to_use[channel] > 0:
                if np.max(power_spec[1:]) > cmax_fft: cmax_fft = np.max(power_spec[1:])
                if np.min(power_spec[1:]) < cmin_fft: cmin_fft = np.min(power_spec[1:])
                ax3.plot(fft_freq, wfm_fft*np.conj(wfm_fft), linewidth=2.0, label="%s"%channel_map[channel])

            #Filter the SiPM WF if necceasry
            if sipm_channels_to_use[channel] > 0 and do_sipm_filter: 
                #plt.figure(109)
                #plt.ion()
                #plt.clf()
                #plt.plot(wfm)
                
                sipm_fft = np.fft.rfft(wfm)
                fft_freq_pass = np.logical_and(fft_freq > -1, fft_freq < sipm_low_pass)
                sipm_fft_filter = np.zeros_like(sipm_fft)
                sipm_fft_filter[fft_freq_pass] = sipm_fft[fft_freq_pass]
                wfm   =  np.fft.irfft(sipm_fft_filter)

                #plt.plot(wfm)
                #plt.show()
                #raw_input("PAUSE")

            if sipm_channels_to_use[channel] > 0:
                sum_sipm_wfm += wfm
                sum_wfm_average[channel] += wfm

            #Get baseline and energy
            baseline      =  np.mean(wfm[0:n_samples_to_avg])
            baseline_rms  =  np.std(wfm[0:n_samples_to_avg])
            energy        =  np.mean(wfm[energy_start_time_samples:])
            energy_rms    =  np.std(wfm[energy_start_time_samples:])
            energy        = (energy - baseline)*multiplier
            sipm_amp      = 0.0
    
            wfm-=baseline

            if channel == pmt_channel:
                i_sample = int(struck_analysis_parameters.n_baseline_samples + 27)
                energy   = (wfm[i_sample])*multiplier          
            if sipm_channels_to_use[channel] > 0:
                energy = (np.max(wfm[1000:1600]))*multiplier
                sipm_max = np.max(wfm[1000:1600])
                sipm_min = np.min(wfm[1000:1600])
                sipm_amp = sipm_max
                if np.abs(sipm_min) > sipm_max:
                    sipm_amp = sipm_min

            #Quick signal Finding on Charge Channels            
            signal_threshold = 5.0*baseline_rms*multiplier/10.0
            rms_threshold = struck_analysis_parameters.rms_keV[channel] + struck_analysis_parameters.rms_keV_sigma[channel]*4.0
            
            if charge_channels_to_use[channel] > 0:
                if energy > signal_threshold:
                    #if not is_for_paper: graph.SetLineWidth(4) # don't bold for paper
                    sum_energy += energy
                    n_signals +=1
                    n_strips += struck_analysis_parameters.channel_to_n_strips_map[channel]    
                if baseline_rms>  rms_threshold:
                    n_high_rms += 1
            if sipm_channels_to_use[channel] > 0:
                if abs(energy/baseline_rms) > 10.0:
                    sum_energy_light += energy

            #Smooth the charge WFs
            if charge_channels_to_use[channel]>0 and smooth_charge:
                exo_wfm = EXODoubleWaveform(wfm, len(wfm))
                new_wfm = EXODoubleWaveform(exo_wfm)
                smoother = EXOSmoother()
                smoother.SetSmoothSize(10)
                smoother.Transform(exo_wfm,new_wfm)
                wfm = np.array([new_wfm.At(i) for i in xrange(new_wfm.GetLength())])
                exo_wfm.IsA().Destructor(exo_wfm)
                new_wfm.IsA().Destructor(new_wfm)
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
            
            #plt.figure(1)
            # add an offset so the channels are drawn at different levels
            offset = channel*energy_offset
            time_sample = np.arange(len(wfm))*(1./(sampling_freq_Hz))*1.e6
            
            if charge_channels_to_use[channel] > 0:
                offset = energy_offset*np.sum(charge_channels_to_use[0:channel])
                wfm += offset
                if np.max(wfm) > cmax: cmax=np.max(wfm)
                if np.min(wfm) < cmin: cmin=np.min(wfm)
                ax0.plot(time_sample, wfm, linewidth=2.0, label=leg_entry, color=ch_to_color(channel))
                if energy > signal_threshold:
                    ax0.text(trigger_time/2.0, offset+energy_offset/2.0, "%.2f keV" % energy, size=10,
                             rotation=0, ha='center', va='center', fontweight='bold')#, 
                            #bbox=dict(boxstyle="square", ec='k', fc='w'))
                #else:
                #    ax0.text(trigger_time/2.0, offset+energy_offset/2.0, "%.2f keV" % energy, size=10,
                #                        rotation=0, ha='center', va='center')#, 
                                        #bbox=dict(boxstyle="square", ec='k', fc='w'))
            elif sipm_channels_to_use[channel] > 0:
                offset = energy_offset_sipm*np.sum(sipm_channels_to_use[0:channel])
                wfm += offset
                if np.max(wfm) > smax: smax=np.max(wfm)
                if np.min(wfm) < smin: smin=np.min(wfm)
                ax1.plot(time_sample, wfm, linewidth=2.0, label=leg_entry)
                ax1.text(trigger_time-sipm_twidth/2, offset+energy_offset_sipm/5.0, 
                         "%.2f" % sipm_amp, size=10,
                         rotation=0, ha='center', va='center')

                #plt.ion()
                #plt.figure(190)
                #plt.clf()
                #plt.title(leg_entry)
                #print channel, channel_map[channel]
                #plt.plot(time_sample, wfm, linewidth=2.0, label=leg_entry)
                #plt.show()
                #if "1-2" in channel_map[channel]: raw_input("PAUSE")



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
        
        if sum_energy < threshold or sum_energy_light < lthreshold: 
            ax0.cla()
            ax1.cla()
            ax3.cla()
            ax4.cla()
            continue
        
        plt.figure(1)
        ax0.set_title("Charge Energy=%.2f keV" % sum_energy)
        ax0.axvline(trigger_time, linewidth=3.0, linestyle='--', c='k')
        ax0.axvline(trigger_time+max_drift_time, linewidth=3.0, linestyle='--', c='k')
        ax0.set_xlabel(r"Time [$\mu$s]",fontsize=16)
    
        tick_name=[]
        tick_pos =[]
        for i_channel in xrange(nchannels):
            if charge_channels_to_use[i_channel] < 0.5: continue
            tick_name.append(channel_map[i_channel])
            offset = energy_offset*np.sum(charge_channels_to_use[:i_channel])
            tick_pos.append(offset)
        ax0.set_yticks(tick_pos)
        ax0.set_yticklabels(tick_name,rotation='horizontal', fontsize=12)
        ax0.set_xlim(min(time_sample),max(time_sample))
        ax0.set_ylim(cmin-1.0*energy_offset,cmax+1.0*energy_offset)

        tick_name=[]
        tick_pos =[]
        for i_channel in xrange(nchannels):
            if sipm_channels_to_use[i_channel] < 0.5: continue
            tick_name.append(channel_map[i_channel])
            offset = energy_offset_sipm*np.sum(sipm_channels_to_use[:i_channel])
            tick_pos.append(offset)

        ax1.set_title("Light Amp=%.2f" % sum_energy_light)
        ax1.yaxis.tick_right()
        ax1.set_yticks(tick_pos)
        ax1.set_yticklabels(tick_name,rotation='horizontal', fontsize=12)
        ax1.set_ylim(smin-0.2*energy_offset_sipm,smax+0.2*energy_offset_sipm)
        ax1.set_xlabel(r"Time [$\mu$s]",fontsize=16)
        #ax1.set_xlim(min(time_sample),max(time_sample))
        if cut_sipm_win:
            ax1.set_xlim(trigger_time-sipm_twidth, trigger_time+sipm_twidth)
        #ax1.axvline(trigger_time, c='k', linestyle='--', linewidth=2.0)

        pdf.savefig(fig1)
        n_plots += 1
        ax0.cla()
        ax1.cla()

        fig2=plt.figure(2)
        ax3.set_yscale('log')
        ax3.set_xscale('log')
        ax3.set_xlim(np.min(fft_freq),np.max(fft_freq))
        ax3.set_xlabel("Frequency [MHz]")
        ax3.set_ylim(cmin_fft,cmax_fft)
        ax3.set_title("Charge WF FFT PS")

        ax4.set_yscale('log')
        ax4.set_xscale('log')
        ax4.set_xlabel("Frequency [MHz]")
        ax4.set_xlim(np.min(fft_freq),np.max(fft_freq))
        ax4.set_ylim(smin_fft,smax_fft)
        ax4.set_title("SiPM WF FFT PS")
        ax4.axvline(sipm_low_pass, linewidth=2.5, linestyle='--', c='r')
        ax4.yaxis.tick_right()
        if plot_fft: pdf.savefig(fig2)
        
        
        #plt.plot(time_sample, sum_wfm,  label='sum charge'  , linewidth=2)
        #plt.plot(time_sample, sum_wfm0, label='sum charge-1', linewidth=2)
        #plt.plot(time_sample, sum_wfm1, label='sum charge-2', linewidth=2)
        #plt.legend()
        #plt.show()
        #pdf.savefig(fig2)
        #raw_input()
        #plt.clf()

        #fig3=plt.figure(3)
        #plt.plot(time_sample, sum_sipm_wfm, linewidth=2)
        #plt.show()
        #pdf.savefig(fig3)
        #raw_input()
        #plt.clf()
        
        if n_plots > n_plots_total: 
            print "Breaking because got the plots"
            break

    plt.ion()
    plt.figure(9)
    for i,sum_wfmi in enumerate(sum_wfm_average):
        if sipm_channels_to_use[i] < 0.5: continue
        new_wfm = (sum_wfmi/n_plots)
        new_wfm -= np.mean(new_wfm[:600])
        offi = np.sum(sipm_channels_to_use[:i])
        plt.plot(new_wfm + offi*200)
        print channel_map[i], np.argmax(new_wfm) ,np.max(new_wfm), np.argmin(new_wfm), np.min(new_wfm)
    plt.show()
    plt.savefig("avg_wfm_" + plot_name )
    raw_input()
    pdf.close()
    return n_plots

if __name__ == "__main__":

    n_plots_total  = 10
    n_plots_so_far = 0
    
    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            n_plots_so_far += process_file(filename, n_plots_total)
    else:
        process_file(n_plots_total=n_plots_total)
