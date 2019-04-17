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
import cPickle as pickle

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
sipm_twidth = 5.0
threshold = 550.0 # keV
energy_offset = 25000.0/nchannels
sum_offset = 51500

energy_offset_sipm = energy_offset*2.0#.1#*1.2

# if this is 1.0 there is no effect:
pmt_shrink_scale = 1.0 # shrink PMT signal by an additional factor so it doesn't set the graphical scale

units_to_use = 0 # 0=keV, 1=ADC units, 2=mV
# figure out which units we are using, to construct the file name
units = "keV"
if units_to_use == 1:
    units = "AdcUnits"
elif units_to_use == 2:
    units = "mV"

elow   = 150.0
ehigh  = 1300.0
ewidth = 20

calibration_values = struck_analysis_parameters.calibration_values    
channel_map = struck_analysis_parameters.channel_map
pmt_channel = struck_analysis_parameters.pmt_channel

rms_threshold = struck_analysis_parameters.rms_threshold

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
colors = struck_analysis_parameters.get_colors()

#n_samples_to_avg = int(struck_analysis_parameters.n_baseline_samples)
n_samples_to_avg = 200
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
    current_file = 0
    wfm_list = []
    energy_list = []

    while i_entry < n_entries:
        tree.GetEntry(i_entry)

        #Get timestamp
        timestamp_first = tree.HitTree.GetRawClock()
        wfm_length      = tree.HitTree.GetNSamples()
        
        #Zero out Calculated Values
        chargeEnergy = 0.0
        n_signals = 0
        n_strips = 0
        found_channels = []
        isdead_event = False
        timestamp_diff = 0.0        

        wfm_array = np.zeros((32,wfm_length))
        event_energy = 0

        #Loop over expected number of channels in a real event
        for i_channel in xrange(nchannels):
            #Already have the first entry so only get new ones
            if i_channel > 0 : tree.GetEntry(i_entry)
            
            #Figure out the hardware channel 
            slot         = tree.HitTree.GetSlot()
            card_channel = tree.HitTree.GetChannel() # 0 to 16 for each card
            channel      = card_channel + 16*slot # 0 to 31            

            if struck_analysis_parameters.do_invert:
                if channel%2==0: channel+=1
                else: channel-=1

            #if not charge_channels_to_use[channel]: continue
        
            #Check timestamp to assosiate WFs with events
            timestamp      = tree.HitTree.GetRawClock()
            timestamp_diff = timestamp - timestamp_first


            if timestamp_diff > 1.5:
                print "Moving on to next event after finding next time stamp", i_entry, timestamp_diff, channel
                break
            
            #Don't increment until after we confirm this entry is part of current event
            i_entry +=1
            
            if i_entry%1000==0:
                print "Working on %i entry " % i_entry

            #Sanity check to make sure we didn't already find this channel.  
            #Should probably never happen since the timestamp check should weed these out
            if channel in found_channels:
                print "Entry %i Channel %i" % (i_entry, channel)
                raw_input("Found a channel more than once is this ok????? Pause here")
            found_channels.append(channel)
            if not charge_channels_to_use[channel]: continue

            #Get information about the card
            card = sys_config.GetSlotParameters().GetParValueO("card",slot)
            gain = card.gain[card_channel]
            
            
            #Get the WFM
            graph = tree.HitTree.GetGraph()
            wfm   = np.array([graph.GetY()[isamp] for isamp in xrange(graph.GetN())])
            wfm   *= calibration_values[channel]

            #if channel==30: wfm=wfm*0.0
            if struck_analysis_parameters.do_invert:
                wfm *= -1.0

            #Get baseline and energy
            baseline      =  np.mean(wfm[0:n_samples_to_avg])
            baseline_rms  =  np.std(wfm[0:n_samples_to_avg])
            energy        =  np.mean(wfm[energy_start_time_samples:])
            energy_rms    =  np.std(wfm[energy_start_time_samples:])
            energy        =  (energy - baseline)
            sipm_amp      =  0.0
    
            wfm               -=baseline
            wfm_array[channel] = wfm

            #print channel, energy/baseline_rms, energy, baseline_rms, n_samples_to_avg
            #if True and np.max(np.abs(wfm))>70:
            #    plt.ion()
            #    plt.plot(wfm)
            #    plt.show()
            #    raw_input("Pause event")
            #    plt.clf()


            if (energy/(baseline_rms*np.sqrt(1.0/n_samples_to_avg))) > rms_threshold and charge_channels_to_use[channel]:
                n_signals+=1
                event_energy += energy
                #print "Found Sig"        
                if False:
                    plt.ion()
                    plt.plot(wfm)
                    plt.show()
                    if energy>500: raw_input("Pause event")
                    plt.clf()
                
        #print n_signals, isdead_event, len(found_channels)
        if n_signals < 0.5:
            continue

        #Check if the channel is a dead channel
        if isdead_event:
            print "Skipping event where we found a dead channel"
            continue

        #Check we found all the good channels we expected to find
        nfound = len(found_channels)
        if nfound < 32: continue

        energy_list.append(event_energy)
        
        #print "len energy", len(energy_list), event_energy
        if len(energy_list)%200==0:
            plt.ion()
            plt.figure(1)
            plt.clf()
            plt.hist(energy_list, bins=np.arange(elow,ehigh,ewidth))
            plt.show()
            raw_input("Pause quick spectrum")


    pfile = basename+"_part%i.p" % current_file
    pfile = pfile.replace("tier1", 'pickle')
    dfile = open(pfile, 'wb')
    pickle.dump(energy_list, dfile)
    dfile.close()
    
    plt.ion()
    plt.figure(1)
    plt.clf()
    plt.hist(energy_list, bins=np.arange(elow,ehigh,ewidth))
    plt.show()
    
    plt.savefig((basename+"_part%i.png" % current_file).replace("tier1", "spectrum_quick"))
    raw_input("Pause final spectrum")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        for filename in sys.argv[1:]:
            process_file(filename)
    else:
        process_file()
