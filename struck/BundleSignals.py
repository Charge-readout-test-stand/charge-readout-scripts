#!/usr/bin/env python

"""
Extract parameters (energy, risetime, etc.) from a waveform. 
"""


import os
import sys

# workaround for systems without EXO offline / CLHEP
microsecond = 1.0e3
second = 1.0e9
if os.getenv("EXOLIB") is not None:
    try:
        gSystem.Load("$EXOLIB/lib/libEXOROOT")
        from ROOT import CLHEP
        microsecond = CLHEP.microsecond
        second = CLHEP.second
    except ImportError:
        print "couldn't import CLHEP/ROOT"


import struck_analysis_parameters

#Bundle Signals together into 

def GetChType(ch):
    channel_map = struck_analysis_parameters.channel_map
    chtype = 0
    
    if 'X' in channel_map[ch]: chtype = 1
    elif 'Y' in channel_map[ch]: chtype = 2
    elif 'PMT' in channel_map[ch]: chtype = 0
    else: print "What happened??", channel_map[ch]
    
    return chtype

def BundleSignals(
    signal_map,
    energy,
    nbundles, 
    bundle_type, 
    signal_bundle_map,
    bundle_energy,
    bundle_nsigs
):

    #Constants from Struck Code
    channels = struck_analysis_parameters.channels
    n_chargechannels = struck_analysis_parameters.n_chargechannels
    pmt_channel = struck_analysis_parameters.pmt_channel
    n_channels = struck_analysis_parameters.n_channels
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
   
    #Loop over the signals found
    #Bundle X and Y channels sepeartely
    #Type 1=x and 2=y
    #Sum the energy of each bundle of channels
    #Energy weighted position??
    nbundlesX = 0
    nbundlesY = 0
    for i, isSignal in enumerate(signal_map):
        if isSignal > 0.5:
            
            #Is it an X or Y channel 
            chtype = GetChType(i)

            #Get Neighbor.  We always go through from left to right so only need
            #to check neighbor to the left.

            nindex = i-1

            if nindex >= 0 and nindex < n_channels and nindex != pmt_channel: 
                #Make sure not PMT channel, or over the edge
                #print "Compare types", chtype, GetChType(nindex)
                if chtype == GetChType(nindex):
                    #Must be same type of channel
                    if signal_map[nindex] > 0.5:
                        #Left neighbor saw a signal so 
                        #Bundle exists already. Add to that bundle
                        ibundle = signal_bundle_map[nindex]
                        signal_bundle_map[i] = ibundle
                        bundle_type[ibundle] = chtype
                        bundle_energy[ibundle] += energy[i]
                        bundle_nsigs[ibundle] += 1
                        continue

            #Bundle does not exist so create it
            signal_bundle_map[i] = nbundles[0] #Save the bundle this channel is assosiated with
            bundle_type[nbundles[0]] = chtype #X or Y
            bundle_energy[nbundles[0]] = energy[i] #Add in energy
            bundle_nsigs[nbundles[0]] = 1
            nbundles[0] += 1 #Iterate bundle
            if chtype==1: nbundlesX+=1
            elif chtype==2: nbundlesY+=1
        else:
            signal_bundle_map[i] = 999
    
    #if nbundles[0] > 0:
    #    print
    #    print signal_map
    #    print energy
    #    print nbundles
    #    print signal_bundle_map
    #    print bundle_type
    #    print bundle_energy
    #    print
    #    raw_input()
    return (
        nbundles,
        bundle_type,
        signal_bundle_map,
        bundle_energy,
        bundle_nsigs,
        nbundlesX,
        nbundlesY
    )



