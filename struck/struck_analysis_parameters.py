#!/usr/bin/env python

"""
These are some parameters used for LXe analyses

import this into your script with this line:
import struck_analysis_parameters

This file must be in the same directory as your script. 

notes:
* ortec preamp added 04 Dec for 6th LXe 
"""

# options
is_6th_LXe = False 
is_7th_LXe = False # March 2016
is_8th_LXe = False # August 2016
is_9th_LXe = False # Sept 2016
is_10th_LXe = False # Jan 2017
is_11th_LXe  = False # Jan/Feb 2017, with DT
is_11th_LXeB = False # Feb 2017, with VME
is_12th_LXe = False
is_13th_LXe = False
is_15th_LXe = False#15 and 16 are basically the same (SiPM runs with 16 bit digi)
is_17th_LXe = False# 17 - 21 all the same purity runs
is_22nd_LXe = False
is_23rd_LXe = False
is_24th_LXe = False
is_28th_LXe = False
is_29th_LXe = True
#Testing 
#is_11th_LXeB = True

import os
import sys
import math
import ROOT

# workaround for systems without EXO offline / CLHEP
microsecond = 1.0e3
second = 1.0e9

import subprocess
root_version = subprocess.check_output(['root-config --version'], shell=True)
isROOT6 = False
if '6.1.0' in root_version or '6.04/06' in root_version:
    print "Found ROOT 6"
    isROOT6 = True

if os.getenv("EXOLIB") is not None and not isROOT6:
    print os.getenv("EXOLIB")
    try:
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
        from ROOT import CLHEP
        if microsecond != CLHEP.microsecond: 
            print "WARNING: microsecond definition is wrong!!"
            sys.exit()
        if second != CLHEP.second: 
            print "WARNING: second definition is wrong!!"
            sys.exit()
        print "imported CLHEP/ROOT"
    #except ImportError or AttributeError:
    except (ImportError, AttributeError) as e:
        print "couldn't import CLHEP/ROOT"

drift_length = 18.16 # mm, from solidworks for 7th LXe + 
drift_velocity = 2.0 # mm / microsecond  

# drift time threshold for 99% signal collection, determined from ion screening
# and cathode effects:
drift_time_threshold = (drift_length - 5.3)/drift_velocity # microsecond

max_drift_time = drift_length/drift_velocity
#print "max_drift_time:", max_drift_time
if is_10th_LXe or is_11th_LXe or is_11th_LXeB or is_12th_LXe or is_13th_LXe or is_15th_LXe or is_17th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    drift_length = 33.23 # new anode standoffs Dec 2016
    if is_10th_LXe:
        drift_velocity = 1.79 # mm/microsecond
    drift_time_threshold = (drift_length - 14.3)/drift_velocity # microsecond
    max_drift_time = drift_length/drift_velocity
    if is_10th_LXe:
        max_drift_time += 2.0 # seems ok 
elif is_28th_LXe or is_29th_LXe:
    #Long TPC
    drift_length   = 140.0
    drift_velocity = 1.79 # mm/microsecond
    #drift_time_threshold = (drift_length - 14.3)/drift_velocity # microsecond
    max_drift_time = drift_length/drift_velocity

#print "max_drift_time:", max_drift_time


sampling_freq_Hz = 25.0e6 # digitizer sampling frequency, Hz
#FIXME--will be saved in trees so no longer needed

charge_channels_to_use = [0]*16
sipm_channels_to_use   = [0]*16
dead_channels          = [0]*16
one_strip_channels = [0]*32
two_strip_channels = [0]*32
channel_to_n_strips_map = [1.0]*32
struck_to_mc_channel_map = {} # map struck channel to MC channel
if is_8th_LXe or is_9th_LXe or is_11th_LXeB or is_12th_LXe or is_13th_LXe or is_15th_LXe or is_17th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe or is_28th_LXe or is_29th_LXe:
    charge_channels_to_use = [0]*32
    sipm_channels_to_use   = [0]*32 
    dead_channels          = [0]*32

do_sipm_filter = False
sipm_low_pass = None
do_invert     = False
if is_12th_LXe or is_13th_LXe:
    sipm_low_pass = 14.3
    if is_13th_LXe: sipm_low_pass = 9.5
    do_sipm_filter = True
elif is_15th_LXe:
    do_sipm_filter = True
    do_invert      = True
    sipm_low_pass=7.0
elif is_17th_LXe:
    do_invert      = True
elif is_22nd_LXe or is_23rd_LXe or is_24th_LXe or is_28th_LXe:
    #No need to filter anymore
    do_invert = True

# in software, struck channels start from 0, not 1
pmt_channel = 8
pulser_channel = None
if is_6th_LXe:
    # channels for 6th LXe
    channels = [0,1,2,3,4,5,8]
    charge_channels_to_use[0] = 1
    charge_channels_to_use[1] = 1
    charge_channels_to_use[2] = 1
    charge_channels_to_use[3] = 1
    charge_channels_to_use[4] = 1

elif is_7th_LXe:
    pmt_channel = 9
    # channels for 6th LXe
    channels = [0,1,2,3,4,5,6,7,9]
    charge_channels_to_use[0] = 1
    charge_channels_to_use[1] = 1
    charge_channels_to_use[2] = 1
    charge_channels_to_use[3] = 1
    charge_channels_to_use[4] = 1
    charge_channels_to_use[5] = 1
    charge_channels_to_use[6] = 1
    charge_channels_to_use[7] = 1

elif is_8th_LXe or is_9th_LXe or is_11th_LXeB:
    pmt_channel = 31
    channels = []
    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        charge_channels_to_use[i_channel] = 1
    charge_channels_to_use[pmt_channel] = 0
    if is_9th_LXe:
        charge_channels_to_use[0] = 0 # Y1-10 is dead
        #charge_channels_to_use[16] = 0 # X1-12 is noisy !!
        charge_channels_to_use[27] = 0 # X23/24 is dead
        pulser_channel = 27
    if is_11th_LXeB:
        pulser_channel = 30

elif is_10th_LXe or is_11th_LXe:
    pmt_channel = 0
    pulser_channel = 1
    channels = []
    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        if i_channel < 16:
            channels.append(i_channel)
        if i_channel > 1:
            charge_channels_to_use[i_channel] = 1
    #charge_channels_to_use[8] = 0 # Y14 changed mid-run

elif is_12th_LXe or is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    pmt_channel = None # now using SiPMs
    pulser_channel = None # won't have one probably?
    channels = []
    
    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        if i_channel < 9:
            #X-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0
        elif i_channel > 8 and i_channel < 14:
            #SiPMs
            charge_channels_to_use[i_channel] = 0
            sipm_channels_to_use[i_channel]   = 1
        elif i_channel > 13 and i_channel < 16:
            if is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe or is_28th_LXe or is_29th_LXe:
                charge_channels_to_use[i_channel] = 1 #Maybe not dead anymore??
                sipm_channels_to_use[i_channel]   = 0
                dead_channels[i_channel] = 0
            else:
                charge_channels_to_use[i_channel] = 0
                sipm_channels_to_use[i_channel]   = 0
                dead_channels[i_channel] = 1
        elif i_channel > 15 and i_channel < 25:
            #Y-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0
        elif i_channel > 24:
            #SiPMs
            charge_channels_to_use[i_channel] = 0 
            sipm_channels_to_use[i_channel]   = 1

elif is_28th_LXe:
    pmt_channel = None # now using SiPMs
    pulser_channel = None # won't have one probably?
    channels = []
   
    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        if i_channel < 9.5:
            #X-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0
        elif i_channel > 9.5 and i_channel < 15.5:
            #SiPMs
            charge_channels_to_use[i_channel] = 0
            sipm_channels_to_use[i_channel]   = 1
        elif i_channel > 15.5 and i_channel < 25.5:
            #Y-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0
        elif i_channel > 25.5:
            #SiPMs
            charge_channels_to_use[i_channel] = 0
            sipm_channels_to_use[i_channel]   = 1



elif is_29th_LXe:
    pmt_channel = None # now using SiPMs
    pulser_channel = None # won't have one probably?
    channels = []

    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        if i_channel < 14.5:
            #X-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0
        elif i_channel > 14.5 and i_channel < 15.5:
            #SiPMs
            charge_channels_to_use[i_channel] = 0
            sipm_channels_to_use[i_channel]   = 1
        elif i_channel > 15.5:
            #Y-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0


elif is_17th_LXe:
    pmt_channel = None # now using SiPMs
    pulser_channel = None # won't have one probably?
    channels = []
    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        if i_channel < 10:
            #X-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0
        elif i_channel > 15 and i_channel < 26:
            #Y-Charge
            charge_channels_to_use[i_channel] = 1
            sipm_channels_to_use[i_channel]   = 0
        elif i_channel == 15:
            charge_channels_to_use[i_channel] = 0
            sipm_channels_to_use[i_channel]   = 1
        else:
            charge_channels_to_use[i_channel] = 0
            sipm_channels_to_use[i_channel]   = 0
else:
    # channels for 5th LXe
    channels = [0,1,2,3,4,8]
    charge_channels_to_use[0] = 1
    charge_channels_to_use[1] = 1
    charge_channels_to_use[2] = 1
    charge_channels_to_use[3] = 1
    charge_channels_to_use[4] = 1

n_channels = len(channels) # channels that are active

if pulser_channel != None:
    charge_channels_to_use[pulser_channel] = 0

## number of useful charge channels
n_chargechannels = sum(charge_channels_to_use)
n_sipmchannels   = sum(sipm_channels_to_use)

# channel names for 6th LXe    
channel_map = {}
# early runs:
channel_map[0] = "X26"
channel_map[1] = "X27"
channel_map[2] = "X29"
channel_map[3] = "Y23"
channel_map[4] = "Y24"
if pmt_channel != None: channel_map[pmt_channel] = "PMT"
if is_6th_LXe:
    channel_map[5] = "X2" # ortec preamp added 04 Dec for 6th LXe
if is_7th_LXe:
    channel_map = {}
    # x channels
    channel_map[0] = "X16"
    channel_map[1] = "X17"
    channel_map[2] = "X18"
    channel_map[3] = "X19"
    # y channels
    channel_map[4] = "Y16"
    channel_map[5] = "Y17"
    channel_map[6] = "Y18"
    channel_map[7] = "Y19"

if is_8th_LXe or is_9th_LXe or is_11th_LXeB:

    # S/N 97, slot 0, Y channels
    struck_to_mc_channel_map[0] = [30,31,32,33,34,35,36,37,38,39]
    struck_to_mc_channel_map[1] = [40]
    struck_to_mc_channel_map[2] = [41]
    struck_to_mc_channel_map[3] = [42]
    struck_to_mc_channel_map[4] = [43]
    struck_to_mc_channel_map[5] = [44]
    struck_to_mc_channel_map[6] = [45]
    struck_to_mc_channel_map[7] = [46]
    struck_to_mc_channel_map[8] = [47]
    struck_to_mc_channel_map[9] = [48]
    struck_to_mc_channel_map[10] = [49]
    struck_to_mc_channel_map[11] = [50,51]
    struck_to_mc_channel_map[12] = [52,53]
    struck_to_mc_channel_map[13] = [54,55]
    struck_to_mc_channel_map[14] = [56,57]
    struck_to_mc_channel_map[15] = [58,59]
    channel_map[0] = "Y1-10"
    channel_map[1] = "Y11"
    channel_map[2] = "Y12"
    channel_map[3] = "Y13"
    channel_map[4] = "Y14"
    channel_map[5] = "Y15"
    channel_map[6] = "Y16"
    channel_map[7] = "Y17"
    channel_map[8] = "Y18"
    channel_map[9] = "Y19"
    channel_map[10] = "Y20"
    channel_map[11] = "Y21/22"
    channel_map[12] = "Y23/24"
    channel_map[13] = "Y25/26"
    channel_map[14] = "Y27/28"
    channel_map[15] = "Y29/30"

    # S/N 98, slot 1, X channels+PMT
    struck_to_mc_channel_map[16] = [0,1,2,3,4,5,6,7,8,9,10,11]
    struck_to_mc_channel_map[17] = [12]
    struck_to_mc_channel_map[18] = [13]
    struck_to_mc_channel_map[19] = [14]
    struck_to_mc_channel_map[20] = [15]
    struck_to_mc_channel_map[21] = [16]
    struck_to_mc_channel_map[22] = [17]
    struck_to_mc_channel_map[23] = [18]
    struck_to_mc_channel_map[24] = [19]
    struck_to_mc_channel_map[25] = [20]
    struck_to_mc_channel_map[26] = [21]
    struck_to_mc_channel_map[27] = [22,23]
    struck_to_mc_channel_map[28] = [24,25]
    struck_to_mc_channel_map[29] = [26,27]
    struck_to_mc_channel_map[30] = [28,29]
    channel_map[16] = "X1-12"
    channel_map[17] = "X13"
    channel_map[18] = "X14"
    channel_map[19] = "X15"
    channel_map[20] = "X16"
    channel_map[21] = "X17"
    channel_map[22] = "X18"
    channel_map[23] = "X19"
    channel_map[24] = "X20"
    channel_map[25] = "X21"
    channel_map[26] = "X22"
    channel_map[27] = "X23/24"
    channel_map[28] = "X25/26"
    channel_map[29] = "X27/28"
    channel_map[30] = "X29/30"
    channel_map[pmt_channel] = "PMT"

    if is_11th_LXeB:
        # Y6, X24 are grounded
        channel_map[27] = "X23" 
        struck_to_mc_channel_map[0] = [30,31,32,33,34,36,37,38,39]
        struck_to_mc_channel_map[27] = [22]
        struck_to_mc_channel_map[pulser_channel] = []

    channel_to_n_strips_map[pmt_channel] = 0.0
    for channel, val in struck_to_mc_channel_map.items():
        n_strips = len(val)
        channel_to_n_strips_map[channel] = n_strips
        if n_strips == 1:
            one_strip_channels[channel] = 1
        elif n_strips == 2:
            two_strip_channels[channel] = 1

if is_10th_LXe or is_11th_LXe:
    channel_map[15] = "X14"
    channel_map[14] = "X15"
    channel_map[13] = "X16"
    channel_map[12] = "X17"
    channel_map[11] = "X18"
    channel_map[10] = "X19"
    channel_map[9] = "X20"
    channel_map[8] = "Y14"
    channel_map[7] = "Y15"
    channel_map[6] = "Y16"
    channel_map[5] = "Y17"
    channel_map[4] = "Y18"
    channel_map[3] = "Y19"
    channel_map[2] = "Y20"
    channel_map[1] = "pulser"
    channel_map[0] = "PMT"

    struck_to_mc_channel_map[2] = [49]
    struck_to_mc_channel_map[3] = [48]
    struck_to_mc_channel_map[4] = [47]
    struck_to_mc_channel_map[5] = [46]
    struck_to_mc_channel_map[6] = [45]
    struck_to_mc_channel_map[7] = [44]
    struck_to_mc_channel_map[8] = [43]

    struck_to_mc_channel_map[9] = [19]
    struck_to_mc_channel_map[10] = [18]
    struck_to_mc_channel_map[11] = [17]
    struck_to_mc_channel_map[12] = [16]
    struck_to_mc_channel_map[13] = [15]
    struck_to_mc_channel_map[14] = [14]
    struck_to_mc_channel_map[15] = [13]

if is_28th_LXe:
    channel_map[0] = "X13"
    channel_map[1] = "X14"
    channel_map[2] = "X15"
    channel_map[3] = "X16"
    channel_map[4] = "X17"
    channel_map[5] = "X18"
    channel_map[6] = "X19"
    channel_map[7] = "X20"
    channel_map[8] = "X21"
    channel_map[9] = "X22"
    channel_map[10] = "2-3" #??
    channel_map[11] = "2-4" #??
    channel_map[12] = "2-5" #??
    channel_map[13] = "2-6" #??
    channel_map[14] = "2-6" #??
    channel_map[15] = "2-6" #??

    channel_map[16] = "Y11"
    channel_map[17] = "Y12"
    channel_map[18] = "Y13"
    channel_map[19] = "Y14"
    channel_map[20] = "Y15"
    channel_map[21] = "Y16"
    channel_map[22] = "Y17"
    channel_map[23] = "Y18"
    channel_map[24] = "Y19"
    channel_map[25] = "Y20"
    channel_map[26] = "1-2" #??
    channel_map[27] = "1-3" #?? 
    channel_map[28] = "1-4" #??
    channel_map[29] = "1-5" #??
    channel_map[30] = "1-6" #??
    channel_map[31] = "2-1" #??


if is_29th_LXe:
    channel_map[0] = "X1-12"
    channel_map[1] = "X13"
    channel_map[2] = "X14"
    channel_map[3] = "X15"
    channel_map[4] = "X16"
    channel_map[5] = "X17"
    channel_map[6] = "X18"
    channel_map[7] = "X19"
    channel_map[8] = "X20"
    channel_map[9] = "X21"
    channel_map[10] = "X22" #??
    channel_map[11] = "X23/24" #??
    channel_map[12] = "X25/26" #??
    channel_map[13] = "X28/27" #??
    channel_map[14] = "X29/30" #??
    channel_map[15] = "1-3" #??

    channel_map[16] = "Y1-10"
    channel_map[17] = "Y11"
    channel_map[18] = "Y12"
    channel_map[19] = "Y13"
    channel_map[20] = "Y14"
    channel_map[21] = "Y15"
    channel_map[22] = "Y16"
    channel_map[23] = "Y17"
    channel_map[24] = "Y18"
    channel_map[25] = "Y19"
    channel_map[26] = "Y20" #??
    channel_map[27] = "Y21/22" #?? 
    channel_map[28] = "Y23/24" #??
    channel_map[29] = "Y25/26" #??
    channel_map[30] = "Y27/28" #??
    channel_map[31] = "Y29/30" #??


if is_12th_LXe or is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    channel_map[0] = "Y12"
    channel_map[1] = "Y13"
    channel_map[2] = "Y14"
    channel_map[3] = "Y15"
    channel_map[4] = "Y16"
    channel_map[5] = "Y17"
    channel_map[6] = "Y18"
    channel_map[7] = "Y19"
    channel_map[8] = "Y20"
    channel_map[9] = "2-2"
    channel_map[10] = "2-3"
    channel_map[11] = "2-4"
    channel_map[12] = "2-5"
    channel_map[13] = "2-6"
    if is_12th_LXe:
        channel_map[14] = "Dead"
        channel_map[15] = "Dead"
    else:
        channel_map[14] = "Y11"
        channel_map[15] = "X22"
    #next unit
    channel_map[16] = "X13"
    channel_map[17] = "X14"
    channel_map[18] = "X15"
    channel_map[19] = "X16"
    channel_map[20] = "X17"
    channel_map[21] = "X18"
    channel_map[22] = "X19"
    channel_map[23] = "X20"
    channel_map[24] = "X21"
    channel_map[25] = "1-1"
    channel_map[26] = "1-2"
    channel_map[27] = "1-3"
    channel_map[28] = "1-4"
    channel_map[29] = "1-5"
    channel_map[30] = "1-6"
    channel_map[31] = "2-1"

    struck_to_mc_channel_map[0]  = [41]
    struck_to_mc_channel_map[1]  = [42]
    struck_to_mc_channel_map[2]  = [43]
    struck_to_mc_channel_map[3]  = [44]
    struck_to_mc_channel_map[4]  = [45]
    struck_to_mc_channel_map[5]  = [46]
    struck_to_mc_channel_map[6]  = [47]
    struck_to_mc_channel_map[7]  = [48]
    struck_to_mc_channel_map[8]  = [49]
    struck_to_mc_channel_map[9]  = []
    struck_to_mc_channel_map[10] = []
    struck_to_mc_channel_map[11] = []
    struck_to_mc_channel_map[12] = []
    struck_to_mc_channel_map[13] = []
    struck_to_mc_channel_map[14] = []
    struck_to_mc_channel_map[15] = []
    if is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe or is_28th_LXe or is_29th_LXe:
        struck_to_mc_channel_map[14] = [40]
        struck_to_mc_channel_map[15] = [21]
    struck_to_mc_channel_map[16] = [12]
    struck_to_mc_channel_map[17] = [13]
    struck_to_mc_channel_map[18] = [14]
    struck_to_mc_channel_map[19] = [15]
    struck_to_mc_channel_map[20] = [16]
    struck_to_mc_channel_map[21] = [17]
    struck_to_mc_channel_map[22] = [18]
    struck_to_mc_channel_map[23] = [19]
    struck_to_mc_channel_map[24] = [20]
    struck_to_mc_channel_map[25] = []
    struck_to_mc_channel_map[26] = []
    struck_to_mc_channel_map[27] = []
    struck_to_mc_channel_map[28] = []
    struck_to_mc_channel_map[29] = []
    struck_to_mc_channel_map[30] = []

if is_17th_LXe:
    
    channel_map[0] = "Y11"
    channel_map[1] = "Y12"
    channel_map[2] = "Y13"
    channel_map[3] = "Y14"
    channel_map[4] = "Y15"
    channel_map[5] = "Y16"
    channel_map[6] = "Y17"
    channel_map[7] = "Y18"
    channel_map[8] = "Y19"
    channel_map[9] = "Y20"
    channel_map[10] = ""
    channel_map[11] = ""
    channel_map[12] = ""
    channel_map[13] = ""
    channel_map[14] = ""
    channel_map[15] = ""

    channel_map[16] = "X13"
    channel_map[17] = "X14"
    channel_map[18] = "X15"
    channel_map[19] = "X16"
    channel_map[20] = "X17"
    channel_map[21] = "X18"
    channel_map[22] = "X19"
    channel_map[23] = "X20"
    channel_map[24] = "X21"
    channel_map[25] = "X22"
    channel_map[26] = ""
    channel_map[27] = ""
    channel_map[28] = ""
    channel_map[29] = ""
    channel_map[30] = ""
    channel_map[31] = ""



if pulser_channel != None:
    channel_map[pulser_channel] = "pulser"

#MC Channels index starts at 0 so X26 = 25
#Y  Channles are offset by 30
#MC only has charge no PMT channel
#All MC channels are there but only use the 5 for sum energies

MCchannels = range(60)
MCn_channels = len(MCchannels)
MCcharge_channels_to_use = [0]*MCn_channels
mc_channel_map = {} # map MC channel to label
for struck_channel, label in channel_map.items():
    if is_10th_LXe or is_11th_LXe or is_11th_LXeB or is_12th_LXe or is_13th_LXe or is_15th_LXe or is_17th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe or is_28th_LXe or is_29th_LXe: break # FIXME -- skip this for now
    is_y = False
    if "Y" in label:
        is_y = True
    elif "PMT" in label: continue
    mc_channel = int(label[1:]) -1
    if is_y: mc_channel += 30
    #print "channel %s: struck=%i | mc=%i" % (label, struck_channel, mc_channel)
    struck_to_mc_channel_map[struck_channel] = [mc_channel]
    mc_channel_map[mc_channel] = label
    MCcharge_channels_to_use[mc_channel] = 1

if is_8th_LXe or is_9th_LXe or is_11th_LXeB:
    MCcharge_channels_to_use = [1]*MCn_channels

    if is_11th_LXeB:
        # Y6, X24 are grounded
        MCcharge_channels_to_use[23] = 0
        MCcharge_channels_to_use[35] = 0

    else:
        # X23/24 is dead
        MCcharge_channels_to_use[22] = 0
        MCcharge_channels_to_use[23] = 0
        # Y1-10 is dead
        MCcharge_channels_to_use[30] = 0
        MCcharge_channels_to_use[31] = 0
        MCcharge_channels_to_use[32] = 0
        MCcharge_channels_to_use[33] = 0
        MCcharge_channels_to_use[34] = 0
        MCcharge_channels_to_use[35] = 0
        MCcharge_channels_to_use[36] = 0
        MCcharge_channels_to_use[37] = 0
        MCcharge_channels_to_use[38] = 0
        MCcharge_channels_to_use[39] = 0

if is_10th_LXe or is_11th_LXe:
    for struck_channel, mc_channel in struck_to_mc_channel_map.items():
        MCcharge_channels_to_use[mc_channel[0]] = 1
        mc_channel_map[mc_channel[0]] = channel_map[struck_channel]

n_MCchargechannels = sum(MCcharge_channels_to_use)

def is_tree_MC(tree):
    """ test whether tier3 tree is of MC results or not"""
    try:
        n_entries = tree.GetEntries()
    except:
        print "is_tree_MC(): couldn't call TTree:GetEntries()"
        return False
    if n_entries < 0:
        print "tree has 0 entries!"
        return False
    tree.GetEntry(0)
    try:
        tree.MCchargeEnergy
        return True
    except:
        return False

def get_voltage_range_mV_ngm(gain):
    voltage_range_mV = 2000.0 # mV
    if gain == 0:
        voltage_range_mV = 5000.0 # mV
    return voltage_range_mV

def get_clock_frequency_Hz_ngm(clock_source_choice):
    """
    return the clock frequency, in Hz, from the clock_source_choice saved in NGM
    output. 
    """

    sampling_frequency_Hz = 25.0e6 # our usual
    if clock_source_choice == 0:
        sampling_frequency_Hz = 250.0e6
    elif clock_source_choice == 1:
        sampling_frequency_Hz = 125.0e6
    elif clock_source_choice == 2:
        sampling_frequency_Hz = 62.5e6
    elif clock_source_choice == 3:
        sampling_frequency_Hz = 25.0e6
    else:
        print "*** WARNING: clock_source_choice unknown -- data collected at 25 MHz?"

    return sampling_frequency_Hz


#Wvalue for Xenon
#From EXODimensions.hh:
#const double W_VALUE_IONIZATION = 15.6*CLHEP::eV;
#const double W_VALUE_LXE_EV_PER_ELECTRON = 18.7*CLHEP::eV;
# from NumTE from 1 MeV electrons: 1e3/4.96561538461538439e+04 
#Wvalue = 20.138 #eV needed to make 1e- # from old SU LXe setup
#Wvalue = 22.1225754074916985 # eV, for gammas @ 936 V/cm, nEXO MC, 10k events
#22.1099058855006163; 10k nEXO MC events with different seed
# new physics list 11 May 2016:
#Wvalue = 21.1403194621 # eV, e-s @ 936 V/cm in SU LXe setup
Wvalue = 22.0043657088 # eV, gammas @ 936 V/cm in SU LXe setup, 46k events

# values from Peihao, 31 Oct 2015:
decay_time_values = {}
decay_time_values[0] = 850.0*microsecond
decay_time_values[1] = 725.0*microsecond
decay_time_values[2] = 775.0*microsecond
decay_time_values[3] = 750.0*microsecond
decay_time_values[4] = 450.0*microsecond

if is_6th_LXe:
    # Ortec 142-IH manual says 200 to 300 microseconds... we should measure this.
    decay_time_values[5] = 300.0*microsecond
    decay_time_values[pmt_channel] = 1e9*microsecond

if is_7th_LXe:
    # updated with fits to 7th LXe overnight -- 30 Mar 2016
    # results_tier1_overnight_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03-08_08-.txt

    decay_time_values[0] = 381.34*microsecond # +/- 2.81 
    decay_time_values[1] = 365.99*microsecond # +/- 1.49 
    decay_time_values[2] = 385.23*microsecond # +/- 2.25 
    decay_time_values[3] = 382.75*microsecond # +/- 3.16 
    decay_time_values[4] = 479.48*microsecond # +/- 2.71 
    decay_time_values[5] = 439.96*microsecond # +/- 1.24 
    decay_time_values[6] = 417.95*microsecond # +/- 1.77 
    decay_time_values[7] = 448.86*microsecond # +/- 2.91 
    decay_time_values[9] = 1.5*microsecond 


if is_8th_LXe or is_9th_LXe: 
    # vales from Mike's fits on 01 Sep 2016:
    decay_time_values[0] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[1] =  320.733754*microsecond # +/- 0.044737  
    decay_time_values[2] =  342.644148*microsecond # +/- 0.042634  
    decay_time_values[3] =  355.715102*microsecond # +/- 0.044866  
    decay_time_values[4] =  340.026733*microsecond # +/- 0.036063  
    decay_time_values[5] =  429.157709*microsecond # +/- 0.041498  
    decay_time_values[6] =  399.524179*microsecond # +/- 0.018644  
    decay_time_values[7] =  346.116071*microsecond # +/- 0.004414  
    decay_time_values[8] =  318.897087*microsecond # +/- 0.008708  
    decay_time_values[9] =  289.080601*microsecond # +/- 0.011302  
    decay_time_values[10] =  317.983729*microsecond # +/- 0.017282  
    decay_time_values[11] =  324.597043*microsecond # +/- 0.013243  
    decay_time_values[12] =  321.615598*microsecond # +/- 0.008053  
    decay_time_values[13] =  304.656336*microsecond # +/- 0.020892  
    decay_time_values[14] =  330.995039*microsecond # +/- 0.043602  
    decay_time_values[15] =  272.095954*microsecond # +/- 0.091542  
    decay_time_values[16] =  210.257989*microsecond # +/- 0.034711  
    decay_time_values[17] =  393.153743*microsecond # +/- 0.059977  
    decay_time_values[18] =  371.621090*microsecond # +/- 0.052355  
    decay_time_values[19] =  406.881221*microsecond # +/- 0.037426  
    decay_time_values[20] =  421.986974*microsecond # +/- 0.034585  
    decay_time_values[21] =  482.517037*microsecond # +/- 0.017129  
    decay_time_values[22] =  443.331886*microsecond # +/- 0.026606  
    decay_time_values[23] =  446.326772*microsecond # +/- 0.052082  
    decay_time_values[24] =  422.881920*microsecond # +/- 0.046550  
    decay_time_values[25] =  375.951362*microsecond # +/- 0.038738  
    decay_time_values[26] =  397.183271*microsecond # +/- 0.060732  
    decay_time_values[27] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[28] =  375.014276*microsecond # +/- 0.031501  
    decay_time_values[29] =  385.634064*microsecond # +/- 0.018183  
    decay_time_values[30] =  359.754388*microsecond # +/- 0.040198  
    decay_time_values[31] =  10000000000.000000*microsecond # Not Used  

if is_11th_LXeB:
    # Fits are in DecayTime_overnight_11thLXeB_v3.pdf 
    decay_time_values[0] =  220.177743*microsecond # +/- 0.019631 Y1-10
    decay_time_values[1] =  336.954510*microsecond # +/- 0.035747 Y11
    decay_time_values[2] =  342.909975*microsecond # +/- 0.033580 Y12
    decay_time_values[3] =  375.471621*microsecond # +/- 0.037684 Y13
    decay_time_values[4] =  364.445833*microsecond # +/- 0.028699 Y14
    decay_time_values[5] =  430.749504*microsecond # +/- 0.035263 Y15
    decay_time_values[6] =  401.468398*microsecond # +/- 0.019691 Y16
    decay_time_values[7] =  366.996051*microsecond # +/- 0.005235 Y17
    decay_time_values[8] =  314.864279*microsecond # +/- 0.008820 Y18
    decay_time_values[9] =  295.266593*microsecond # +/- 0.010130 Y19
    decay_time_values[10] =  316.139852*microsecond # +/- 0.016089 Y20
    decay_time_values[11] =  317.346648*microsecond # +/- 0.011693 Y21/22
    decay_time_values[12] =  313.040718*microsecond # +/- 0.007317 Y23/24
    decay_time_values[13] =  297.191957*microsecond # +/- 0.015426 Y25/26
    decay_time_values[14] =  324.727292*microsecond # +/- 0.026848 Y27/28
    decay_time_values[15] =  330.228038*microsecond # +/- 0.033613 Y29/30
    decay_time_values[16] =  218.350917*microsecond # +/- 0.018520 X1-12
    decay_time_values[17] =  373.164130*microsecond # +/- 0.024446 X13
    decay_time_values[18] =  385.112331*microsecond # +/- 0.032387 X14
    decay_time_values[19] =  395.731914*microsecond # +/- 0.043800 X15
    decay_time_values[20] =  428.013071*microsecond # +/- 0.024771 X16
    decay_time_values[21] =  454.867452*microsecond # +/- 0.014542 X17
    decay_time_values[22] =  436.329761*microsecond # +/- 0.022793 X18
    decay_time_values[23] =  421.476176*microsecond # +/- 0.037603 X19
    decay_time_values[24] =  393.562566*microsecond # +/- 0.030876 X20
    decay_time_values[25] =  381.182494*microsecond # +/- 0.034273 X21
    decay_time_values[26] =  392.642787*microsecond # +/- 0.043076 X22
    decay_time_values[27] =  395.270775*microsecond # +/- 0.044866 X23/24
    decay_time_values[28] =  362.852652*microsecond # +/- 0.021263 X25/26
    decay_time_values[29] =  362.903823*microsecond # +/- 0.013574 X27/28
    decay_time_values[30] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[31] =  10000000000.000000*microsecond # Not Used  

if is_29th_LXe:
    decay_time_values[0] =  218.350917*microsecond # +/- 0.018520 X1-12
    decay_time_values[1] =  373.164130*microsecond # +/- 0.024446 X13
    decay_time_values[2] =  385.112331*microsecond # +/- 0.032387 X14
    decay_time_values[3] =  395.731914*microsecond # +/- 0.043800 X15
    decay_time_values[4] =  428.013071*microsecond # +/- 0.024771 X16
    decay_time_values[5] =  454.867452*microsecond # +/- 0.014542 X17
    decay_time_values[6] =  436.329761*microsecond # +/- 0.022793 X18
    decay_time_values[7] =  421.476176*microsecond # +/- 0.037603 X19
    decay_time_values[8] =  393.562566*microsecond # +/- 0.030876 X20
    decay_time_values[9] =  381.182494*microsecond # +/- 0.034273 X21
    decay_time_values[10] =  392.642787*microsecond # +/- 0.043076 X22
    decay_time_values[11] =  395.270775*microsecond # +/- 0.044866 X23/24
    decay_time_values[12] =  362.852652*microsecond # +/- 0.021263 X25/26
    decay_time_values[13] =  362.903823*microsecond # +/- 0.013574 X27/28
    decay_time_values[14] =  362.903823*microsecond # +/- 0.013574 X29/30  ?????????????????????
    decay_time_values[15] =  10000000000.000000*microsecond # Not Used
    decay_time_values[16] =  220.177743*microsecond # +/- 0.019631 Y1-10
    decay_time_values[17] =  336.954510*microsecond # +/- 0.035747 Y11
    decay_time_values[18] =  342.909975*microsecond # +/- 0.033580 Y12
    decay_time_values[19] =  375.471621*microsecond # +/- 0.037684 Y13
    decay_time_values[20] =  364.445833*microsecond # +/- 0.028699 Y14
    decay_time_values[21] =  430.749504*microsecond # +/- 0.035263 Y15
    decay_time_values[22] =  401.468398*microsecond # +/- 0.019691 Y16
    decay_time_values[23] =  366.996051*microsecond # +/- 0.005235 Y17
    decay_time_values[24] =  314.864279*microsecond # +/- 0.008820 Y18
    decay_time_values[25] =  295.266593*microsecond # +/- 0.010130 Y19
    decay_time_values[26] =  316.139852*microsecond # +/- 0.016089 Y20
    decay_time_values[27] =  317.346648*microsecond # +/- 0.011693 Y21/22
    decay_time_values[28] =  313.040718*microsecond # +/- 0.007317 Y23/24
    decay_time_values[29] =  297.191957*microsecond # +/- 0.015426 Y25/26
    decay_time_values[30] =  324.727292*microsecond # +/- 0.026848 Y27/28
    decay_time_values[31] =  330.228038*microsecond # +/- 0.033613 Y29/30

if is_10th_LXe or is_11th_LXe:
    # Fits are in DecayTime_overnight10thLXe_v3.pdf 
    decay_time_values[0] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[1] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[2] =  130.661344*microsecond # +/- 0.006022 Y20
    decay_time_values[3] =  133.947099*microsecond # +/- 0.005033 Y19
    decay_time_values[4] =  132.431729*microsecond # +/- 0.003500 Y18
    decay_time_values[5] =  150.581211*microsecond # +/- 0.001877 Y17
    decay_time_values[6] =  137.815828*microsecond # +/- 0.004132 Y16
    decay_time_values[7] =  141.324616*microsecond # +/- 0.006453 Y15
    decay_time_values[8] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[9] =  137.174582*microsecond # +/- 0.007347 X20
    decay_time_values[10] =  141.004072*microsecond # +/- 0.006563 X19
    decay_time_values[11] =  139.068536*microsecond # +/- 0.003624 X18
    decay_time_values[12] =  126.817805*microsecond # +/- 0.002625 X17
    decay_time_values[13] =  139.283740*microsecond # +/- 0.003826 X16
    decay_time_values[14] =  135.320872*microsecond # +/- 0.009996 X15
    decay_time_values[15] =  136.730159*microsecond # +/- 0.008309 X14

if is_28th_LXe:
    decay_time_values[0] = 373.164130*microsecond # +/- 0.024446 X13
    decay_time_values[1] =  385.112331*microsecond # +/- 0.032387 X14
    decay_time_values[2] =  395.731914*microsecond # +/- 0.043800 X15
    decay_time_values[3] =  428.013071*microsecond # +/- 0.024771 X16
    decay_time_values[4] =  454.867452*microsecond # +/- 0.014542 X17
    decay_time_values[5] =  436.329761*microsecond # +/- 0.022793 X18
    decay_time_values[6] =  421.476176*microsecond # +/- 0.037603 X19
    decay_time_values[7] =  393.562566*microsecond # +/- 0.030876 X20
    decay_time_values[8] =  381.182494*microsecond # +/- 0.034273 X21
    decay_time_values[9] =  392.642787*microsecond # +/- 0.043076 X22
    decay_time_values[10] =  10000000000.000000*microsecond # Not Used
    decay_time_values[11] =  10000000000.000000*microsecond # Not Used
    decay_time_values[12] =  10000000000.000000*microsecond # Not Used
    decay_time_values[13] =  10000000000.000000*microsecond # Not Used
    decay_time_values[14] =  10000000000.000000*microsecond # Not Used
    decay_time_values[15] =  10000000000.000000*microsecond # Not Used

    decay_time_values[16] =  336.954510*microsecond # +/- 0.035747 Y11
    decay_time_values[17] =   342.909975*microsecond # +/- 0.033580 Y12
    decay_time_values[18] =   375.471621*microsecond # +/- 0.037684 Y13
    decay_time_values[19] =   364.445833*microsecond # +/- 0.028699 Y14
    decay_time_values[20] =   430.749504*microsecond # +/- 0.035263 Y15
    decay_time_values[21] =   401.468398*microsecond # +/- 0.019691 Y16
    decay_time_values[22] =   366.996051*microsecond # +/- 0.005235 Y17
    decay_time_values[23] =   314.864279*microsecond # +/- 0.008820 Y18
    decay_time_values[24] =   295.266593*microsecond # +/- 0.010130 Y19
    decay_time_values[25] =   316.139852*microsecond # +/- 0.016089 Y20
    decay_time_values[26] =  10000000000.000000*microsecond # Not Used
    decay_time_values[27] =  10000000000.000000*microsecond # Not Used
    decay_time_values[28] =  10000000000.000000*microsecond # Not Used
    decay_time_values[29] =  10000000000.000000*microsecond # Not Used
    decay_time_values[30] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[31] =  10000000000.000000*microsecond # Not Used


if is_12th_LXe or is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    decay_time_values[0] =   342.909975*microsecond # +/- 0.033580 Y12
    decay_time_values[1] =   375.471621*microsecond # +/- 0.037684 Y13
    decay_time_values[2] =   364.445833*microsecond # +/- 0.028699 Y14
    decay_time_values[3] =   430.749504*microsecond # +/- 0.035263 Y15
    decay_time_values[4] =   401.468398*microsecond # +/- 0.019691 Y16
    decay_time_values[5] =   366.996051*microsecond # +/- 0.005235 Y17
    decay_time_values[6] =   314.864279*microsecond # +/- 0.008820 Y18
    decay_time_values[7] =   295.266593*microsecond # +/- 0.010130 Y19
    decay_time_values[8] =   316.139852*microsecond # +/- 0.016089 Y20 
    decay_time_values[9] =   10000000000.000000*microsecond # Not Used
    decay_time_values[10] =  10000000000.000000*microsecond # Not Used
    decay_time_values[11] =  10000000000.000000*microsecond # Not Used
    decay_time_values[12] =  10000000000.000000*microsecond # Not Used
    decay_time_values[13] =  10000000000.000000*microsecond # Not Used
    decay_time_values[14] =  10000000000.000000*microsecond # Not Used
    decay_time_values[15] =  10000000000.000000*microsecond # Not Used
    if is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
        decay_time_values[14] =  336.954510*microsecond # +/- 0.035747 Y11
        decay_time_values[15] =  392.642787*microsecond # +/- 0.043076 X22
    decay_time_values[16] =  373.164130*microsecond # +/- 0.024446 X13
    decay_time_values[17] =  385.112331*microsecond # +/- 0.032387 X14
    decay_time_values[18] =  395.731914*microsecond # +/- 0.043800 X15
    decay_time_values[19] =  428.013071*microsecond # +/- 0.024771 X16
    decay_time_values[20] =  454.867452*microsecond # +/- 0.014542 X17
    decay_time_values[21] =  436.329761*microsecond # +/- 0.022793 X18
    decay_time_values[22] =  421.476176*microsecond # +/- 0.037603 X19
    decay_time_values[23] =  393.562566*microsecond # +/- 0.030876 X20
    decay_time_values[24] =  381.182494*microsecond # +/- 0.034273 X21
    decay_time_values[25] =  392.642787*microsecond # +/- 0.043076 X22
    decay_time_values[26] =  10000000000.000000*microsecond # Not Used
    decay_time_values[27] =  10000000000.000000*microsecond # Not Used
    decay_time_values[28] =  10000000000.000000*microsecond # Not Used
    decay_time_values[29] =  10000000000.000000*microsecond # Not Used
    decay_time_values[30] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[31] =  10000000000.000000*microsecond # Not Used

if is_17th_LXe:
    decay_time_values[0] =  336.954510*microsecond # +/- 0.035747 Y11  
    decay_time_values[1] =   342.909975*microsecond # +/- 0.033580 Y12
    decay_time_values[2] =   375.471621*microsecond # +/- 0.037684 Y13
    decay_time_values[3] =   364.445833*microsecond # +/- 0.028699 Y14
    decay_time_values[4] =   430.749504*microsecond # +/- 0.035263 Y15
    decay_time_values[5] =   401.468398*microsecond # +/- 0.019691 Y16
    decay_time_values[6] =   366.996051*microsecond # +/- 0.005235 Y17
    decay_time_values[7] =   314.864279*microsecond # +/- 0.008820 Y18
    decay_time_values[8] =   295.266593*microsecond # +/- 0.010130 Y19
    decay_time_values[9] =   316.139852*microsecond # +/- 0.016089 Y20 
    decay_time_values[10] =  10000000000.000000*microsecond # Not Used
    decay_time_values[11] =  10000000000.000000*microsecond # Not Used
    decay_time_values[12] =  10000000000.000000*microsecond # Not Used
    decay_time_values[13] =  10000000000.000000*microsecond # Not Used
    decay_time_values[14] =  10000000000.000000*microsecond # Not Used
    decay_time_values[15] =  10000000000.000000*microsecond # Not Used
    
    decay_time_values[16] =  373.164130*microsecond # +/- 0.024446 X13
    decay_time_values[17] =  385.112331*microsecond # +/- 0.032387 X14
    decay_time_values[18] =  395.731914*microsecond # +/- 0.043800 X15
    decay_time_values[19] =  428.013071*microsecond # +/- 0.024771 X16
    decay_time_values[20] =  454.867452*microsecond # +/- 0.014542 X17
    decay_time_values[21] =  436.329761*microsecond # +/- 0.022793 X18
    decay_time_values[22] =  421.476176*microsecond # +/- 0.037603 X19
    decay_time_values[23] =  393.562566*microsecond # +/- 0.030876 X20
    decay_time_values[24] =  381.182494*microsecond # +/- 0.034273 X21
    decay_time_values[25] =  392.642787*microsecond # +/- 0.043076 X22
    decay_time_values[26] =  10000000000.000000*microsecond # Not Used
    decay_time_values[27] =  10000000000.000000*microsecond # Not Used
    decay_time_values[28] =  10000000000.000000*microsecond # Not Used
    decay_time_values[29] =  10000000000.000000*microsecond # Not Used
    decay_time_values[30] =  10000000000.000000*microsecond # Not Used  
    decay_time_values[31] =  10000000000.000000*microsecond # Not Used

# charge calbration from these files for 5th LXe:
# tier3_LXe_Run1_1700VC_2chargechannels_609PM_60thresh_NotShaped_Amplified_GapTime20_2_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_5thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_8thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_330PM_7thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_238PM2_10thresh.root

# convert energies to keV by multiplying by these factors:
# NOTE: for 2V input, need to divide by 2.5

struck_energy_multiplier = 0.96 # match struck calibration to MC TE calib
#struck_energy_multiplier = 1.0 # match struck calibration to MC TE calib
channel_pos_y = {}
channel_pos_x = {}
calibration_values = {}
calibration_values[0] = 5.827591
calibration_values[1] = 5.146835
calibration_values[2] = 5.331666
calibration_values[3] = 5.096831
calibration_values[4] = 5.586442

if is_7th_LXe:

    # updated 19 May 2016 after calibration with drift-time cut 6.43 to 9.0 microseconds
    # fit_results_570_No_cuts_overnight7thLXe2016_05_19_13_54_09_.txt
    # cat fit.out | grep calibration_values
    calibration_values[0] = 4.806178 # +/- 0.014936
    calibration_values[1] = 5.045101 # +/- 0.013461
    calibration_values[2] = 4.932245 # +/- 0.016006
    calibration_values[3] = 4.846766 # +/- 0.019288
    calibration_values[4] = 5.203141 # +/- 0.016417
    calibration_values[5] = 5.004507 # +/- 0.013618
    calibration_values[6] = 4.740380 # +/- 0.014216
    calibration_values[7] = 4.938769 # +/- 0.020818

    # PMT
    calibration_values[9] = 2.12352

if is_8th_LXe: 
    for i_channel in xrange(len(channels)):
        calibration_values[i_channel] = 2.5 # initial guess

    # can 7 (channels 4, 5, 6, 7 = Y14, Y15, Y16, Y17) is old preamps
    # can 2 (channels 20, 21, 22, 23 = X16, X17, X18, X19) is old preamps
    # calibration values from fit_peak.py 
    # on entire overnight data set, with rise time cuts, 31 Aug 2016
    # from new_calib_570_overnight8thLXe_v22016_08_31_15_40_48_.txt

    calibration_values[1] = 0.941202 # +/- 0.006842
    calibration_values[2] = 0.910808 # +/- 0.005103
    calibration_values[3] = 0.994761 # +/- 0.004914
    calibration_values[4] = 3.959773 # +/- 0.016096
    calibration_values[5] = 1.917820 # +/- 0.005818
    calibration_values[6] = 1.825965 # +/- 0.004064
    calibration_values[7] = 1.908706 # +/- 0.004006
    calibration_values[8] = 0.964900 # +/- 0.001936
    calibration_values[9] = 0.915300 # +/- 0.002505
    calibration_values[10] = 0.946391 # +/- 0.002979
    calibration_values[11] = 0.956886 # +/- 0.002104
    calibration_values[12] = 1.030227 # +/- 0.002073
    calibration_values[13] = 0.976099 # +/- 0.003473
    calibration_values[14] = 1.000098 # +/- 0.006787
    calibration_values[15] = 0.923127 # +/- 0.011730
    calibration_values[16] = 1.020810 # +/- 0.006806
    calibration_values[17] = 0.965269 # +/- 0.004444
    calibration_values[18] = 0.941890 # +/- 0.003407
    calibration_values[19] = 0.961320 # +/- 0.002962
    calibration_values[20] = 1.831759 # +/- 0.003718
    calibration_values[21] = 1.923281 # +/- 0.003483
    calibration_values[22] = 1.912008 # +/- 0.003792
    calibration_values[23] = 2.066341 # +/- 0.005921
    calibration_values[24] = 0.908744 # +/- 0.003232
    calibration_values[25] = 0.943060 # +/- 0.003862
    calibration_values[26] = 1.001475 # +/- 0.005421
    calibration_values[28] = 1.031480 # +/- 0.002665
    calibration_values[29] = 0.963934 # +/- 0.001759
    calibration_values[30] = 1.923727 # +/- 0.005794


if is_9th_LXe: 
    for i_channel in xrange(len(channels)):
        calibration_values[i_channel] = 0.92 # initial guess

    # can 7 (channels 4, 5, 6, 7 = Y14, Y15, Y16, Y17) is old preamps
    # can 2 (channels 20, 21, 22, 23 = X16, X17, X18, X19) is old preamps
    # calibration values from fit_peak.py with rise-time and single-strip cuts 

    # basename: 570_No_cuts_step_overnight_9thLXe_v1_2016_10_03_12_33_05_ 
    # selection: (nsignals==1) && (!(rise_time_stop95_sum-trigger_time < 6.43 || rise_time_stop95_sum-trigger_time > 9.0)) 
    # channel_selection: (nsignals==1) && (!(rise_time_stop95_sum-trigger_time < 6.43 || rise_time_stop95_sum-trigger_time > 9.0)) 
    # calibration_values[all] = 0.997689 # +/- 0.000315 all
    calibration_values[1] = 0.929761 # +/- 0.003398 Y11
    calibration_values[2] = 0.916165 # +/- 0.003835 Y12
    calibration_values[3] = 0.980632 # +/- 0.002732 Y13
    calibration_values[4] = 2.428339 # +/- 0.006286 Y14
    calibration_values[5] = 1.912586 # +/- 0.003041 Y15
    calibration_values[6] = 1.818427 # +/- 0.002093 Y16
    calibration_values[7] = 1.914533 # +/- 0.002280 Y17
    calibration_values[8] = 0.964218 # +/- 0.001111 Y18
    calibration_values[9] = 0.917491 # +/- 0.001353 Y19
    calibration_values[10] = 0.955506 # +/- 0.001737 Y20
    calibration_values[11] = 0.956040 # +/- 0.001239 Y21/22
    calibration_values[12] = 1.032623 # +/- 0.001158 Y23/24
    calibration_values[13] = 0.962927 # +/- 0.001926 Y25/26
    calibration_values[14] = 1.043044 # +/- 0.004276 Y27/28
    calibration_values[15] = 0.902715 # +/- 0.005045 Y29/30
    calibration_values[16] = 1.006127 # +/- 0.006022 X1-12
    calibration_values[17] = 0.961838 # +/- 0.002642 X13
    calibration_values[18] = 0.939369 # +/- 0.002229 X14
    calibration_values[19] = 0.951769 # +/- 0.001637 X15
    calibration_values[20] = 1.836569 # +/- 0.002156 X16
    calibration_values[21] = 1.917633 # +/- 0.002155 X17
    calibration_values[22] = 1.911182 # +/- 0.002107 X18
    calibration_values[23] = 1.892692 # +/- 0.002967 X19
    calibration_values[24] = 0.936823 # +/- 0.001890 X20
    calibration_values[25] = 0.925640 # +/- 0.002206 X21
    calibration_values[26] = 0.988795 # +/- 0.003182 X22
    calibration_values[28] = 1.060951 # +/- 0.001503 X25/26
    calibration_values[29] = 0.966761 # +/- 0.001092 X27/28
    calibration_values[30] = 1.926988 # +/- 0.003290 X29/30

if is_10th_LXe or is_11th_LXe: 
    for i_channel in xrange(len(channels)):
        calibration_values[i_channel] = 0.92 # initial guess
    calibration_values[pulser_channel] = 0.018511 # make the pulser 100 keV when warm 24 Jan 2017

    # basename: 570_No_cuts_overnight10thLXe_v1_2017_01_20_13_59_31_ 
    # selection: (nsignals==1) && (!(rise_time_stop95_sum-trigger_time < 10.5754189944 || rise_time_stop95_sum-trigger_time > 20.0)) 
    # channel_selection: (nsignals==1) && (!(rise_time_stop95_sum-trigger_time < 10.5754189944 || rise_time_stop95_sum-trigger_time > 20.0)) 
    # calibration_values[all] = 1.000163 # +/- 0.002924 all
    calibration_values[2] = 0.920205 # +/- 0.005547 Y20
    calibration_values[3] = 0.897660 # +/- 0.003838 Y19
    calibration_values[4] = 0.942238 # +/- 0.004160 Y18
    calibration_values[5] = 1.823772 # +/- 0.008439 Y17
    calibration_values[6] = 1.735314 # +/- 0.007285 Y16
    calibration_values[7] = 1.894545 # +/- 0.010724 Y15
    calibration_values[8] = 2.172412 # +/- 0.030666 Y14
    calibration_values[9] = 0.866036 # +/- 0.004423 X20
    calibration_values[10] = 1.799525 # +/- 0.007884 X19
    calibration_values[11] = 1.843981 # +/- 0.008291 X18
    calibration_values[12] = 1.940034 # +/- 0.010628 X17
    calibration_values[13] = 1.745394 # +/- 0.006663 X16
    calibration_values[14] = 0.927497 # +/- 0.005200 X15
    calibration_values[15] = 0.941125 # +/- 0.006729 X14


if is_11th_LXeB: 

    for i_channel in xrange(len(channels)):
        calibration_values[i_channel] = 0.92 # initial guess

    # can 7 (channels 4, 5, 6, 7 = Y14, Y15, Y16, Y17) is old preamps
    # can 2 (channels 20, 21, 22, 23 = X16, X17, X18, X19) is old preamps

    # basename: 570_DC_nsig1_noPulser_overnight_11thLXe_v1_2017_02_03_15_18_05_ 
    # selection: (nsignals==1) && rise_time_stop95_sum-trigger_time >= 10.5754189944
    # && rise_time_stop95_sum-trigger_time <= 20.5642458101 && !is_pulser 
    # channel_selection: (nsignals==1) && rise_time_stop95_sum-trigger_time >=
    # 10.5754189944 && rise_time_stop95_sum-trigger_time <= 20.5642458101 &&
    # !is_pulser 
    # calibration_values[all] = 1.071396 # +/- 0.001313 all
    calibration_values[0] = 1.124574 # +/- 0.008460 Y1-10
    calibration_values[1] = 0.999629 # +/- 0.007652 Y11
    calibration_values[2] = 0.985199 # +/- 0.011359 Y12
    calibration_values[3] = 1.035688 # +/- 0.005218 Y13
    calibration_values[4] = 2.570478 # +/- 0.022494 Y14
    calibration_values[5] = 2.057025 # +/- 0.011570 Y15
    calibration_values[6] = 1.961670 # +/- 0.008979 Y16
    calibration_values[7] = 2.023030 # +/- 0.011141 Y17
    calibration_values[8] = 1.034512 # +/- 0.004743 Y18
    calibration_values[9] = 0.989389 # +/- 0.005858 Y19
    calibration_values[10] = 1.013754 # +/- 0.005928 Y20
    calibration_values[11] = 1.024040 # +/- 0.004533 Y21/22
    calibration_values[12] = 1.130982 # +/- 0.007040 Y23/24
    calibration_values[13] = 1.038541 # +/- 0.005904 Y25/26
    calibration_values[14] = 1.069890 # +/- 0.008625 Y27/28
    calibration_values[15] = 0.947477 # +/- 0.008198 Y29/30
    calibration_values[16] = 1.080784 # +/- 0.006723 X1-12
    calibration_values[17] = 1.006839 # +/- 0.004704 X13
    calibration_values[18] = 0.988350 # +/- 0.005978 X14
    calibration_values[19] = 1.026779 # +/- 0.006602 X15
    calibration_values[20] = 1.949497 # +/- 0.007094 X16
    calibration_values[21] = 2.066524 # +/- 0.008312 X17
    calibration_values[22] = 2.030872 # +/- 0.008091 X18
    calibration_values[23] = 2.018855 # +/- 0.008083 X19
    calibration_values[24] = 0.971441 # +/- 0.004438 X20
    calibration_values[25] = 0.984041 # +/- 0.004598 X21
    calibration_values[26] = 1.043984 # +/- 0.005659 X22
    calibration_values[27] = 1.041238 # +/- 0.006443 X23/24
    calibration_values[28] = 1.082616 # +/- 0.004944 X25/26
    calibration_values[29] = 1.019562 # +/- 0.003483 X27/28

    calibration_values[pulser_channel] = 0.018511 # make the pulser 100 keV when warm 24 Jan 2017


if is_29th_LXe:
    calibration_values[0] = 1.080784 # +/- 0.006723 X1-12
    calibration_values[1] = 1.006839 # +/- 0.004704 X13
    calibration_values[2] = 0.988350 # +/- 0.005978 X14
    calibration_values[3] = 1.026779 # +/- 0.006602 X15
    calibration_values[4] = 1.949497 # +/- 0.007094 X16
    calibration_values[5] = 2.066524 # +/- 0.008312 X17
    calibration_values[6] = 2.030872 # +/- 0.008091 X18
    calibration_values[7] = 2.018855 # +/- 0.008083 X19
    calibration_values[8] = 0.971441 # +/- 0.004438 X20
    calibration_values[9] = 0.984041 # +/- 0.004598 X21
    calibration_values[10] = 1.043984 # +/- 0.005659 X22
    calibration_values[11] = 1.041238 # +/- 0.006443 X23/24
    calibration_values[12] = 1.082616 # +/- 0.004944 X25/26
    calibration_values[13] = 1.019562 # +/- 0.003483 X27/28
    calibration_values[14] = 1.926988 # +/- 0.003290 X29/30
    calibration_values[15] = 1.000000 # it really doesn't matter I guess 1-3
    calibration_values[16] = 1.124574 # +/- 0.008460 Y1-10
    calibration_values[17] = 0.999629 # +/- 0.007652 Y11
    calibration_values[18] = 0.985199 # +/- 0.011359 Y12
    calibration_values[19] = 1.035688 # +/- 0.005218 Y13
    calibration_values[20] = 2.570478 # +/- 0.022494 Y14
    calibration_values[21] = 2.057025 # +/- 0.011570 Y15
    calibration_values[22] = 1.961670 # +/- 0.008979 Y16
    calibration_values[23] = 2.023030 # +/- 0.011141 Y17
    calibration_values[24] = 1.034512 # +/- 0.004743 Y18
    calibration_values[25] = 0.989389 # +/- 0.005858 Y19
    calibration_values[26] = 1.013754 # +/- 0.005928 Y20
    calibration_values[27] = 1.024040 # +/- 0.004533 Y21/22
    calibration_values[28] = 1.130982 # +/- 0.007040 Y23/24
    calibration_values[29] = 1.038541 # +/- 0.005904 Y25/26
    calibration_values[30] = 1.069890 # +/- 0.008625 Y27/28
    calibration_values[31] = 0.947477 # +/- 0.008198 Y29/30


if is_12th_LXe:
    calibration_values[0]  = 1.039055   # +/-  Y12 
    calibration_values[1]  = 1.119925   # +/-  Y13
    calibration_values[2]  = 2.570478*1.5   # +/-  Y14   (Bad Fit)
    calibration_values[3]  = 2.246636   # +/-  Y15
    calibration_values[4]  = 2.146142   #  +/- Y16
    calibration_values[5]  = 2.216303   # +/-  Y17
    calibration_values[6]  = 1.123176   # +/-  Y18
    calibration_values[7]  = 1.071333   # +/-  Y19
    calibration_values[8]  = 1.094867   # +/-  Y20
    calibration_values[9]  = 1.0
    calibration_values[10] = 1.0
    calibration_values[11] = 1.0
    calibration_values[12] = 1.0
    calibration_values[13] = 1.0
    calibration_values[14] = 1.0
    calibration_values[15] = 1.0
    calibration_values[16] = 1.082268 # +/-  X13
    calibration_values[17] = 0.878766*1.3 # +/-  X14 (Bad Fit)
    calibration_values[18] = 1.069808 # +/-  X15
    calibration_values[19] = 2.117263 # +/-  X16
    calibration_values[20] = 2.284341 # +/-  X17
    calibration_values[21] = 2.199645 # +/-  X18
    calibration_values[22] = 2.177320 # +/-  X19
    calibration_values[23] = 1.052999 # +/-  X20
    calibration_values[24] = 1.080689 # +/-  X21
    calibration_values[25] = 1.0
    calibration_values[26] = 1.0
    calibration_values[27] = 1.0
    calibration_values[28] = 1.0
    calibration_values[29] = 1.0
    calibration_values[30] = 1.0
    calibration_values[31] = 1.0

if is_13th_LXe:
    #Calibraitons 13th combining all 3 day runs with differen SiPM bias
    calibration_values[0] = 1.039173 # +/- 0.036779 Y12
    calibration_values[1] = 1.123437 # +/- 0.038555 Y13
    calibration_values[2] = 2.937023 # +/- 0.001754 Y14
    calibration_values[3] = 2.260158 # +/- 0.017537 Y15
    calibration_values[4] = 2.089076 # +/- 0.025162 Y16
    calibration_values[5] = 2.129663 # +/- 0.028330 Y17
    calibration_values[6] = 1.090685 # +/- 0.025185 Y18
    calibration_values[7] = 1.097663 # +/- 0.456941 Y19
    calibration_values[8] = 1.062616 # +/- 0.044031 Y20
    calibration_values[9] = 1.000000 # +/- None 2-2
    calibration_values[10] = 1.000000 # +/- None 2-3
    calibration_values[11] = 1.000000 # +/- None 2-4
    calibration_values[12] = 1.000000 # +/- None 2-5
    calibration_values[13] = 1.000000 # +/- None 2-6
    calibration_values[14] = 1.1638   # +/- 0.072026 Y11
    calibration_values[15] = 1.1173   # +/- 0.060159 X22
    calibration_values[16] = 1.106813 # +/- 0.102014 X13
    calibration_values[17] = 1.088395 # +/- 0.024772 X14
    calibration_values[18] = 1.0945   # +/- 0.133791 X15
    calibration_values[19] = 2.094149 # +/- 0.032667 X16
    calibration_values[20] = 2.2960   # +/- 0.041331 X17
    calibration_values[21] = 2.199645 # +/- 0.001754 X18
    calibration_values[22] = 2.182251 # +/- 0.051105 X19
    calibration_values[23] = 1.064134 # +/- 0.022905 X20
    calibration_values[24] = 1.085066 # +/- 0.034761 X21
    calibration_values[25] = 1.000000 # +/- None 1-1
    calibration_values[26] = 1.000000 # +/- None 1-2
    calibration_values[27] = 1.000000 # +/- None 1-3
    calibration_values[28] = 1.000000 # +/- None 1-4
    calibration_values[29] = 1.000000 # +/- None 1-5
    calibration_values[30] = 1.000000 # +/- None 1-6
    calibration_values[31] = 1.000000 # +/- None 2-1

bit_mult = 1.0/4.0
if is_15th_LXe or is_22nd_LXe:
    #Calibraitons 13th combining all 3 day runs with differen SiPM bias
    calibration_values[0] = 1.039173*bit_mult # +/- 0.036779 Y12
    calibration_values[1] = 1.123437*bit_mult # +/- 0.038555 Y13
    calibration_values[2] = 2.937023*bit_mult # +/- 0.001754 Y14
    calibration_values[3] = 2.260158*bit_mult # +/- 0.017537 Y15
    calibration_values[4] = 2.089076*bit_mult # +/- 0.025162 Y16
    calibration_values[5] = 2.129663*bit_mult # +/- 0.028330 Y17
    calibration_values[6] = 1.090685*bit_mult # +/- 0.025185 Y18
    calibration_values[7] = 1.097663*bit_mult # +/- 0.456941 Y19
    calibration_values[8] = 1.062616*bit_mult # +/- 0.044031 Y20
    
    calibration_values[9]  = 1./106.03 # +/- None 2-2
    calibration_values[10] = 1./103.16 # +/- None 2-3
    calibration_values[11] = 1./101.73 # +/- None 2-4
    calibration_values[12] = 1./98.63  # +/- None 2-5
    calibration_values[13] = 1./105.15 # +/- None 2-6
    
    calibration_values[14] = 1.1638*bit_mult   # +/- 0.072026 Y11
    calibration_values[15] = 1.1173*bit_mult   # +/- 0.060159 X22
    calibration_values[16] = 1.106813*bit_mult # +/- 0.102014 X13
    calibration_values[17] = 1.088395*bit_mult # +/- 0.024772 X14
    calibration_values[18] = 1.0945*bit_mult   # +/- 0.133791 X15
    calibration_values[19] = 2.094149*bit_mult # +/- 0.032667 X16
    calibration_values[20] = 2.2960*bit_mult   # +/- 0.041331 X17
    calibration_values[21] = 2.199645*bit_mult # +/- 0.001754 X18
    calibration_values[22] = 2.182251*bit_mult # +/- 0.051105 X19
    calibration_values[23] = 1.064134*bit_mult # +/- 0.022905 X20
    calibration_values[24] = 1.085066*bit_mult # +/- 0.034761 X21
    
    calibration_values[25] = 1./110.77 # +/- None 1-1
    calibration_values[26] = 1./102.23 # +/- None 1-2
    calibration_values[27] = 1./134.24 # +/- None 1-3
    calibration_values[28] = 1./143.59 # +/- None 1-4
    calibration_values[29] = 1./99.67  # +/- None 1-5
    calibration_values[30] = 1./99.14  # +/- None 1-6
    calibration_values[31] = 1./109.29 # +/- None 2-1

if is_23rd_LXe:
    calibration_values[0] = 0.286942 # +/- 0.057702 Y12
    calibration_values[1] = 0.304919 # +/- 0.060999 Y13
    calibration_values[2] = 0.687591 # +/- 0.044724 Y14
    calibration_values[3] = 0.595840 # +/- 0.014837 Y15
    calibration_values[4] = 0.555692 # +/- 0.042051 Y16
    calibration_values[5] = 0.564293 # +/- 0.016769 Y17
    calibration_values[6] = 0.296624 # +/- 0.018159 Y18
    calibration_values[7] = 0.280179 # +/- 0.026824 Y19
    calibration_values[8] = 0.301202 # +/- 0.044918 Y20


    calibration_values[9]  = 1./106.03 # +/- None 2-2
    calibration_values[10] = 1./103.16 # +/- None 2-3
    calibration_values[11] = 1./101.73 # +/- None 2-4
    calibration_values[12] = 1./98.63  # +/- None 2-5
    calibration_values[13] = 1./105.15 # +/- None 2-6

    calibration_values[14] = 0.293263 # +/- 0.175352 Y11
    calibration_values[15] = 0.304134 # +/- 0.039376 X22
    calibration_values[16] = 0.291087 # +/- 0.043461 X13
    calibration_values[17] = 0.299281 # +/- 0.025870 X14
    calibration_values[18] = 0.291379 # +/- 0.022309 X15
    calibration_values[19] = 0.568134 # +/- 0.013282 X16
    calibration_values[20] = 0.602422 # +/- 0.018926 X17
    calibration_values[21] = 0.590972 # +/- 0.027108 X18
    calibration_values[22] = 0.588194 # +/- 0.020150 X19
    calibration_values[23] = 0.285307 # +/- 0.027691 X20
    calibration_values[24] = 0.287427 # +/- 0.020365 X21


    calibration_values[25] = 1./110.77 # +/- None 1-1
    calibration_values[26] = 1./102.23 # +/- None 1-2
    calibration_values[27] = 1./134.24 # +/- None 1-3
    calibration_values[28] = 1./143.59 # +/- None 1-4
    calibration_values[29] = 1./99.67  # +/- None 1-5
    calibration_values[30] = 1./99.14  # +/- None 1-6
    calibration_values[31] = 1./109.29 # +/- None 2-1

if is_24th_LXe:

    calibration_values[0] = 0.315464 # +/- 0.131446 Y12
    calibration_values[1] = 0.345048 # +/- 0.051110 Y13
    calibration_values[2] = 0.797658 # +/- 0.044617 Y14
    calibration_values[3] = 0.677462 # +/- 0.034290 Y15
    calibration_values[4] = 0.635660 # +/- 0.031079 Y16
    calibration_values[5] = 0.639245 # +/- 0.023345 Y17
    calibration_values[6] = 0.333230 # +/- 0.037649 Y18
    calibration_values[7] = 0.319001 # +/- 0.036188 Y19
    calibration_values[8] = 0.339477 # +/- 0.023041 Y20

    calibration_values[9]  = 1./106.03 # +/- None 2-2
    calibration_values[10] = 1./103.16 # +/- None 2-3
    calibration_values[11] = 1./101.73 # +/- None 2-4
    calibration_values[12] = 1./98.63  # +/- None 2-5
    calibration_values[13] = 1./105.15 # +/- None 2-6

    calibration_values[14] = 0.323736 # +/- 0.134267 Y11
    calibration_values[15] = 0.347937 # +/- 0.050970 X22
    calibration_values[16] = 0.329404 # +/- 0.042190 X13
    calibration_values[17] = 0.333578 # +/- 0.039041 X14
    calibration_values[18] = 0.336020 # +/- 0.061671 X15
    calibration_values[19] = 0.636551 # +/- 0.036947 X16
    calibration_values[20] = 0.683377 # +/- 0.027382 X17
    calibration_values[21] = 0.664754 # +/- 0.030490 X18
    calibration_values[22] = 0.674815 # +/- 0.035191 X19
    calibration_values[23] = 0.320533 # +/- 0.046747 X20
    calibration_values[24] = 0.321199 # +/- 0.024817 X21

    calibration_values[25] = 1./110.77 # +/- None 1-1
    calibration_values[26] = 1./102.23 # +/- None 1-2
    calibration_values[27] = 1./134.24 # +/- None 1-3
    calibration_values[28] = 1./143.59 # +/- None 1-4
    calibration_values[29] = 1./99.67  # +/- None 1-5
    calibration_values[30] = 1./99.14  # +/- None 1-6
    calibration_values[31] = 1./109.29 # +/- None 2-1

if is_28th_LXe:
    calibration_values[0] = 0.329404 # +/- 0.042190 X13
    calibration_values[1] = 0.333578 # +/- 0.039041 X14
    calibration_values[2] = 0.336020 # +/- 0.061671 X15
    calibration_values[3] = 0.636551 # +/- 0.036947 X16
    calibration_values[4] = 0.683377 # +/- 0.027382 X17
    calibration_values[5] = 0.664754 # +/- 0.030490 X18
    calibration_values[6] = 0.674815 # +/- 0.035191 X19
    calibration_values[7] = 0.320533 # +/- 0.046747 X20
    calibration_values[8] = 0.321199 # +/- 0.024817 X21
    calibration_values[9] = 0.347937 # +/- 0.050970 X22
    calibration_values[10] = 1./103.16 # +/- None 2-3
    calibration_values[11] = 1./101.73 # +/- None 2-4
    calibration_values[12] = 1./98.63  # +/- None 2-5
    calibration_values[13] = 1./105.15 # +/- None 2-6
    calibration_values[14] = 1./100.0 # +/- 0.134267 Y11
    calibration_values[15] = 1./100.0 # +/- 0.050970 X22

    calibration_values[16] = 0.323736 # +/- 0.134267 Y1    
    calibration_values[17] = 0.315464 # +/- 0.131446 Y12
    calibration_values[18] = 0.345048 # +/- 0.051110 Y13
    calibration_values[19] = 0.797658 # +/- 0.044617 Y14
    calibration_values[20] = 0.677462 # +/- 0.034290 Y15
    calibration_values[21] = 0.635660 # +/- 0.031079 Y16
    calibration_values[22] = 0.639245 # +/- 0.023345 Y17
    calibration_values[23] = 0.333230 # +/- 0.037649 Y18
    calibration_values[24] = 0.319001 # +/- 0.036188 Y19
    calibration_values[25] = 0.339477 # +/- 0.023041 Y20
    calibration_values[26] = 1./110.77 # +/- None 1-1
    calibration_values[27] = 1./102.23 # +/- None 1-2
    calibration_values[28] = 1./134.24 # +/- None 1-3
    calibration_values[29] = 1./143.59 # +/- None 1-4
    calibration_values[30] = 1./99.67  # +/- None 1-5
    calibration_values[31] = 1./99.14  # +/- None 1-6


if is_17th_LXe:
    #Calibraitons 13th combining all 3 day runs with differen SiPM bias
    calibration_values[0] = 1.1638*bit_mult   # +/- 0.072026 Y11
    calibration_values[1] = 1.039173*bit_mult # +/- 0.036779 Y12
    calibration_values[2] = 1.123437*bit_mult # +/- 0.038555 Y13
    calibration_values[3] = 2.937023*bit_mult # +/- 0.001754 Y14
    calibration_values[4] = 2.260158*bit_mult # +/- 0.017537 Y15
    calibration_values[5] = 2.089076*bit_mult # +/- 0.025162 Y16
    calibration_values[6] = 2.129663*bit_mult # +/- 0.028330 Y17
    calibration_values[7] = 1.090685*bit_mult # +/- 0.025185 Y18
    calibration_values[8] = 1.097663*bit_mult # +/- 0.456941 Y19
    calibration_values[9] = 1.062616*bit_mult # +/- 0.044031 Y20
   
    calibration_values[10] = 1 # +/- None 2-2
    calibration_values[11] = 1 # +/- None 2-3
    calibration_values[12] = 1 # +/- None 2-4
    calibration_values[13] = 1  # +/- None 2-5
    calibration_values[14] = 1 # +/- None 2-6
    calibration_values[15] = 1 # +/- None 2-6
    
    calibration_values[16] = 1.106813*bit_mult # +/- 0.102014 X13
    calibration_values[17] = 1.088395*bit_mult # +/- 0.024772 X14
    calibration_values[18] = 1.0945*bit_mult   # +/- 0.133791 X15
    calibration_values[19] = 2.094149*bit_mult # +/- 0.032667 X16
    calibration_values[20] = 2.2960*bit_mult   # +/- 0.041331 X17
    calibration_values[21] = 2.199645*bit_mult # +/- 0.001754 X18
    calibration_values[22] = 2.182251*bit_mult # +/- 0.051105 X19
    calibration_values[23] = 1.064134*bit_mult # +/- 0.022905 X20
    calibration_values[24] = 1.085066*bit_mult # +/- 0.034761 X21
    calibration_values[25] = 1.1173*bit_mult   # +/- 0.060159 X22   

    calibration_values[26] = 1. # +/- None 1-2
    calibration_values[27] = 1. # +/- None 1-3
    calibration_values[28] = 1 # +/- None 1-4
    calibration_values[29] = 1  # +/- None 1-5
    calibration_values[30] = 1  # +/- None 1-6
    calibration_values[31] = 1. # +/- None 2-1


if is_12th_LXe or is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    channel_pos_y[0] = -10.5 #Y12
    channel_pos_y[1] =  -7.5 #Y13
    channel_pos_y[2] = -4.5  #Y14
    channel_pos_y[3] =  -1.5 #Y15
    channel_pos_y[4] =  1.5  #Y16
    channel_pos_y[5] =  4.5  #Y17
    channel_pos_y[6] =  7.5  #Y18
    channel_pos_y[7] =  10.5 #Y19
    channel_pos_y[8] =  13.5 #Y20
    channel_pos_y[9]  =  0.0  
    channel_pos_y[10] =  0.0 
    channel_pos_y[11] =  0.0  
    channel_pos_y[12] =  0.0 
    channel_pos_y[13] =  0.0  
    channel_pos_y[14] =  0.0  #Dead
    channel_pos_y[15] =  0.0  #Dead
    if is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
        channel_pos_y[14] =  -13.5  #Y11
        channel_pos_y[15] =  0.0  #X22
    channel_pos_y[16] =  0.0 #X13
    channel_pos_y[17] =  0.0 #X14
    channel_pos_y[18] =  0.0 #X15
    channel_pos_y[19] =  0.0 #X16
    channel_pos_y[20] =  0.0 #X17
    channel_pos_y[21] =  0.0 #X18
    channel_pos_y[22] =  0.0 #X19
    channel_pos_y[23] =  0.0 #X20
    channel_pos_y[24] =  0.0 #X21
    channel_pos_y[25] =  0.0 
    channel_pos_y[26] =  0.0
    channel_pos_y[27] =  0.0  
    channel_pos_y[28] =  0.0
    channel_pos_y[29] =  0.0  
    channel_pos_y[30] =  0.0
    channel_pos_y[31] =  0.0
    
    channel_pos_x[0]  =  0.0 #Y12
    channel_pos_x[1]  =  0.0 #Y13
    channel_pos_x[2]  =  0.0  #Y14
    channel_pos_x[3]  =  0.0 #Y15
    channel_pos_x[4]  =  0.0  #Y16
    channel_pos_x[5]  =  0.0  #Y17
    channel_pos_x[6]  =  0.0  #Y18
    channel_pos_x[7]  =  0.0 #Y19
    channel_pos_x[8]  =  0.0 #Y20
    channel_pos_x[9]  =  0.0 
    channel_pos_x[10] =  0.0 
    channel_pos_x[11] =  0.0 
    channel_pos_x[12] =  0.0 
    channel_pos_x[13] =  0.0  
    channel_pos_x[14] =  0.0  #Dead
    channel_pos_x[15] =  0.0  #Dead
    if is_13th_LXe or is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
        channel_pos_x[14] =  0.0  #Y11
        channel_pos_x[15] =  19.5  #X22
    channel_pos_x[16] =  -7.5 #X13
    channel_pos_x[17] =  -4.5 #X14
    channel_pos_x[18] =  -1.5 #X15
    channel_pos_x[19] =  1.5 #X16
    channel_pos_x[20] =  4.5 #X17
    channel_pos_x[21] =  7.5 #X18
    channel_pos_x[22] =  10.5 #X19
    channel_pos_x[23] =  13.5 #X20
    channel_pos_x[24] =  16.5 #X21
    channel_pos_x[25] =  0.0  
    channel_pos_x[26] =  0.0
    channel_pos_x[27] =  0.0  
    channel_pos_x[28] =  0.0
    channel_pos_x[29] =  0.0
    channel_pos_x[30] =  0.0

if is_28th_LXe:
    channel_pos_x[0] =  -7.5 #X13
    channel_pos_x[1] =  -4.5 #X14
    channel_pos_x[2] =  -1.5 #X15
    channel_pos_x[3] =  1.5 #X16
    channel_pos_x[4] =  4.5 #X17
    channel_pos_x[5] =  7.5 #X18
    channel_pos_x[6] =  10.5 #X19
    channel_pos_x[7] =  13.5 #X20
    channel_pos_x[8] =  16.5 #X21
    channel_pos_x[9] =  19.5  #X22
    channel_pos_x[10] =  0.0
    channel_pos_x[11] =  0.0
    channel_pos_x[12] =  0.0
    channel_pos_x[13] =  0.0
    channel_pos_x[14] =  0.0  
    channel_pos_x[15] =  0.0  
    channel_pos_x[16] =  0.0
    channel_pos_x[17] =  0.0
    channel_pos_x[18] =  0.0
    channel_pos_x[19] =  0.0
    channel_pos_x[20] =  0.0
    channel_pos_x[21] =  0.0
    channel_pos_x[22] =  0.0
    channel_pos_x[23] =  0.0
    channel_pos_x[24] =  0.0
    channel_pos_x[25] =  0.0
    channel_pos_x[26] =  0.0
    channel_pos_x[27] =  0.0
    channel_pos_x[28] =  0.0
    channel_pos_x[29] =  0.0
    channel_pos_x[30] =  0.0
    channel_pos_x[31] =  0.0
    
    
    channel_pos_y[0] =  0.0
    channel_pos_y[1] =  0.0
    channel_pos_y[2] =  0.0
    channel_pos_y[3] =  0.0
    channel_pos_y[4] =  0.0
    channel_pos_y[5] =  0.0
    channel_pos_y[6] =  0.0
    channel_pos_y[7] =  0.0
    channel_pos_y[8] =  0.0
    channel_pos_y[9] =  0.0
    channel_pos_y[10] =  0.0
    channel_pos_y[11] =  0.0
    channel_pos_y[12] =  0.0
    channel_pos_y[13] =  0.0
    channel_pos_y[14] =  0.0
    channel_pos_y[15] =  0.0

    channel_pos_y[16] =  -13.5#Y11
    channel_pos_y[17] = -10.5 #Y12
    channel_pos_y[18] =  -7.5 #Y13
    channel_pos_y[19] = -4.5  #Y14
    channel_pos_y[20] =  -1.5 #Y15
    channel_pos_y[21] =  1.5  #Y16
    channel_pos_y[22] =  4.5  #Y17
    channel_pos_y[23] =  7.5  #Y18
    channel_pos_y[24] =  10.5 #Y19
    channel_pos_y[25] =  13.5 #Y20
    channel_pos_y[26] =  0.0  
    channel_pos_y[27] =  0.0
    channel_pos_y[28] =  0.0
    channel_pos_y[29] =  0.0
    channel_pos_y[30] =  0.0
    channel_pos_y[31] =  0.0

if is_29th_LXe:
    channel_pos_x[0] =  -27.0	#X1-12
    channel_pos_x[1] =  -7.5 	#X13
    channel_pos_x[2] =  -4.5 	#X14
    channel_pos_x[3] =  -1.5 	#X15
    channel_pos_x[4] =  1.5 	#X16
    channel_pos_x[5] =  4.5 	#X17
    channel_pos_x[6] =  7.5 	#X18
    channel_pos_x[7] =  10.5 	#X19
    channel_pos_x[8] =  13.5 	#X20
    channel_pos_x[9] =  16.5 	#X21
    channel_pos_x[10] =  19.5  	#X22
    channel_pos_x[11] =  24.0	#X23/24
    channel_pos_x[12] =  30.0	#X25/26
    channel_pos_x[13] =  36.0	#X27/28
    channel_pos_x[14] =  42.0	#X29/30
    channel_pos_x[15] =  0.0  
    channel_pos_x[16] =  0.0  
    channel_pos_x[17] =  0.0
    channel_pos_x[18] =  0.0
    channel_pos_x[19] =  0.0
    channel_pos_x[20] =  0.0
    channel_pos_x[21] =  0.0
    channel_pos_x[22] =  0.0
    channel_pos_x[23] =  0.0
    channel_pos_x[24] =  0.0
    channel_pos_x[25] =  0.0
    channel_pos_x[26] =  0.0
    channel_pos_x[27] =  0.0
    channel_pos_x[28] =  0.0
    channel_pos_x[29] =  0.0
    channel_pos_x[30] =  0.0
    channel_pos_x[31] =  0.0
    
    
    channel_pos_y[0] =  0.0
    channel_pos_y[1] =  0.0
    channel_pos_y[2] =  0.0
    channel_pos_y[3] =  0.0
    channel_pos_y[4] =  0.0
    channel_pos_y[5] =  0.0
    channel_pos_y[6] =  0.0
    channel_pos_y[7] =  0.0
    channel_pos_y[8] =  0.0
    channel_pos_y[9] =  0.0
    channel_pos_y[10] =  0.0
    channel_pos_y[11] =  0.0
    channel_pos_y[12] =  0.0
    channel_pos_y[13] =  0.0
    channel_pos_y[14] =  0.0
    channel_pos_y[15] =  0.0

    channel_pos_y[16] =  -30.0#Y1-10
    channel_pos_y[17] =  -13.5#Y11
    channel_pos_y[18] = -10.5 #Y12
    channel_pos_y[19] =  -7.5 #Y13
    channel_pos_y[20] = -4.5  #Y14
    channel_pos_y[21] =  -1.5 #Y15
    channel_pos_y[22] =  1.5  #Y16
    channel_pos_y[23] =  4.5  #Y17
    channel_pos_y[24] =  7.5  #Y18
    channel_pos_y[25] =  10.5 #Y19
    channel_pos_y[26] =  13.5 #Y20
    channel_pos_y[27] =  18.0 #Y21/22  
    channel_pos_y[28] =  24.0 #Y23/24
    channel_pos_y[29] =  30.0 #Y25/26
    channel_pos_y[30] =  36.0 #Y27/28
    channel_pos_y[31] =  42.0 #Y29/30

resolution_guess = 0.06*570.0 #Instrinsic Charge Resolution at the 570 guess for fitting peak

# PMT calibration is from PMT-triggered data
# EMI 9531QB, 1200V PMT bias, 1700V cathode bias
#calibration_values[pmt_channel] = 0.4470588


# PMT calibration is from PMT-triggered data
# EMI 9921QB, 1250V PMT bias, 1700V cathode bias
# using Ako's readout chain
if pmt_channel != None: calibration_values[pmt_channel] = 0.4470588*3.0

if is_6th_LXe:
    calibration_values[0] = 5.388958
    calibration_values[1] = 5.072361
    calibration_values[2] = 5.243364 
    calibration_values[3] = 5.026291
    calibration_values[4] = 5.273221 

    # a guess
    calibration_values[5] = 1.0/1.40734817170111285e+02*570.0/0.725

    # PMT calibration from correlation with charge energy
    # EMI 9531QB, 1300V PMT bias, 1700V cathode bias
    calibration_values[8] = 2.12352

colors = [
    ROOT.kBlue, 
    ROOT.kGreen+2, 
    ROOT.kViolet+1,
    ROOT.kRed, 
    ROOT.kOrange+1,
    ROOT.kMagenta,
]

if is_7th_LXe:
    colors = [
        ROOT.kMagenta, 
        ROOT.kMagenta+2, 
        ROOT.kRed, 
        ROOT.kOrange+1, 
        ROOT.kGreen+2, 
        ROOT.kCyan+1,
        ROOT.kBlue, 
        ROOT.kBlue+2, 
        #ROOT.kTeal, 
        ROOT.kGray+2, 
    ]

# construct colors from RGB vals:
else:
    # http://tools.medialab.sciences-po.fr/iwanthue
    rgb_json = \
    [[255,122,158],
    [224,0,81],
    [156,37,45],
    [255,175,155],
    [248,91,48],
    [143,71,0],
    [216,112,0],
    [247,186,123],
    [255,179,87],
    [109,76,36],
    [130,100,0],
    [191,165,0],
    [180,172,116],
    [141,138,0],
    [202,205,59],
    [165,214,79],
    [91,141,0],
    [65,90,28],
    [114,215,74],
    [71,216,93],
    [153,212,156],
    [0,146,57],
    [1,196,172],
    [1,86,157],
    [2,119,235],
    [107,109,248],
    [150,72,207],
    [215,147,255],
    [146,15,146],
    [118,64,104],
    [255,143,203],
    [194,0,116]] 

    colors = []
    color = ROOT.TColor()
    for i_color, rgb in enumerate(rgb_json):
        val =  color.GetColor(rgb[0], rgb[1], rgb[2])
        #print i_color, rgb, val
        colors.append(val)

def get_colors():
    return colors


noiseLightCut = 20.0
noise_length = int(800)
if is_10th_LXe or is_11th_LXe: 
    noise_length = int(1050)
    noiseLightCut = 20.0
if is_12th_LXe or is_13th_LXe or is_15th_LXe or is_17th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    noise_length = int(5250)
    noiseLightCut = 20.0
elif  is_28th_LXe or is_29th_LXe:
    noise_length = int(13000)
    noiseLightCut = 20.0

# from tier2to3_overnight.root, baseline_rms
n_baseline_samples = 200.0 # 2x n samples
energy_start_time_microseconds = 450.0*40/1000 # energy calc starts 450 samples after wfm start, in a normal 25-MS/s run
if is_10th_LXe:
    energy_start_time_microseconds = 850.0*40/1000 # energy calc starts 850 samples
baseline_average_time_microseconds = 4.0 # 100 samples at 25 MHz = 4 microsecond
if is_11th_LXe or is_11th_LXeB:
    n_baseline_samples = 275.0 # 2x n samples
    energy_start_time_microseconds = (1050.0 - n_baseline_samples)*40/1000 # energy calc starts 850 samples
baseline_average_time_microseconds = (n_baseline_samples/2.0*40.0/1000) # 200 samples at 25 MHz = 8 microseconds
if is_12th_LXe or is_13th_LXe or is_15th_LXe or is_17th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    #sampling_freq_Hz = 125.0e6 #saved in tree so don't need
    samp_period = 8 #ns (125MHz)
    wf_length = 5250.0
    #WRONG right now
    n_baseline_samples = 5*275.0 # 2x n samples
    energy_start_time_microseconds = (wf_length - n_baseline_samples)*samp_period/1000 # energy calc starts 850 samples
    #Factor of 1/2 here
    baseline_average_time_microseconds = (n_baseline_samples/2.0*samp_period/1000) # 200 samples at 25 MHz = 8 microseconds
elif is_28th_LXe or is_29th_LXe:
    samp_period = 8 #ns (125MHz)
    wf_length   = 13000
    #n_baseline_samples = 5*275.0 # 2x n samples
    n_baseline_samples = 1000
    energy_start_time_microseconds = (wf_length - n_baseline_samples)*samp_period/1000 # energy calc starts 850 samples
    baseline_average_time_microseconds = (n_baseline_samples/2.0*samp_period/1000) # 200 samples at 25 MHz = 8 microseconds

#energy_start_time_samples = int(energy_start_time_microseconds*microsecond*sampling_freq_Hz/second)

#print "energy_start_time_microseconds:", energy_start_time_microseconds

decay_start_time_microseconds = energy_start_time_microseconds #sample 500 for 800-sample wfm
decay_end_time_microseconds = (energy_start_time_microseconds + baseline_average_time_microseconds*2) #sample 800
decay_tau_guess = 200 #us

rms_keV = {}
rms_keV_sigma = {}
rms_keV[0] = 18.137
rms_keV[1] = 17.557
rms_keV[2] = 17.805
rms_keV[3] = 17.137
rms_keV[4] = 18.182

if is_7th_LXe:
    # from findAverageWfmNoise.py:
    rms_keV[0] = 22.32325
    rms_keV[1] = 22.52304
    rms_keV[2] = 21.84460
    rms_keV[3] = 21.01474
    rms_keV[4] = 19.32956
    rms_keV[5] = 18.58932
    rms_keV[6] = 18.66388
    rms_keV[7] = 19.21589


#Threshold to be a signal 5*RMS
rms_threshold = 5.0

if is_8th_LXe: 
    # Fits are in /home/teststand/2016_08_15_8th_LXe_overnight/tier3_llnl/RMSNoise.pdf
    rms_keV[0] = 0.000000 # Not Used 
    rms_keV[1] = 20.995596*calibration_values[1]  # +/- 0.000388  
    rms_keV[2] = 21.894430*calibration_values[2]  # +/- 0.000399  
    rms_keV[3] = 21.007420*calibration_values[3]  # +/- 0.000400  
    rms_keV[4] = 5.551739*calibration_values[4]  # +/- 0.000113  
    rms_keV[5] = 8.803907*calibration_values[5]  # +/- 0.000176  
    rms_keV[6] = 9.389167*calibration_values[6]  # +/- 0.000184  
    rms_keV[7] = 8.659650*calibration_values[7]  # +/- 0.000201  
    rms_keV[8] = 22.087330*calibration_values[8]  # +/- 0.000426  
    rms_keV[9] = 21.686294*calibration_values[9]  # +/- 0.000410  
    rms_keV[10] = 21.981299*calibration_values[10]  # +/- 0.000402  
    rms_keV[11] = 25.448166*calibration_values[11]  # +/- 0.000490  
    rms_keV[12] = 24.218385*calibration_values[12]  # +/- 0.000481  
    rms_keV[13] = 24.576492*calibration_values[13]  # +/- 0.000474  
    rms_keV[14] = 24.269800*calibration_values[14]  # +/- 0.000462  
    rms_keV[15] = 23.026472*calibration_values[15]  # +/- 0.000710  
    rms_keV[16] = 43.044320*calibration_values[16]  # +/- 0.001096  
    rms_keV[17] = 21.287944*calibration_values[17]  # +/- 0.000387  
    rms_keV[18] = 21.425270*calibration_values[18]  # +/- 0.000399  
    rms_keV[19] = 19.841148*calibration_values[19]  # +/- 0.000371  
    rms_keV[20] = 9.058564*calibration_values[20]  # +/- 0.000183  
    rms_keV[21] = 8.952226*calibration_values[21]  # +/- 0.000181  
    rms_keV[22] = 9.036681*calibration_values[22]  # +/- 0.000187  
    rms_keV[23] = 7.682366*calibration_values[23]  # +/- 0.000163  
    rms_keV[24] = 20.372451*calibration_values[24]  # +/- 0.000371  
    rms_keV[25] = 21.028353*calibration_values[25]  # +/- 0.000381  
    rms_keV[26] = 22.467277*calibration_values[26]  # +/- 0.000411  
    rms_keV[27] = 0.000000 # Not Used 
    rms_keV[28] = 24.307752*calibration_values[28]  # +/- 0.000488  
    rms_keV[29] = 25.113164*calibration_values[29]  # +/- 0.000504  
    rms_keV[30] = 14.788121*calibration_values[30]  # +/- 0.000373  
    rms_keV[31] = 0.000000 # Not Used 


if is_9th_LXe: 

    # Fits are in RMSNoise_overnight_9thLXe_v0.pdf 
    rms_keV[0] = 7.989843*calibration_values[0]  # +/- 0.000089 
    rms_keV_sigma[0] = 0.439870*calibration_values[0] # +/- 0.000063
    rms_keV[1] = 20.447405*calibration_values[1]  # +/- 0.000220 
    rms_keV_sigma[1] = 1.093195*calibration_values[1] # +/- 0.000156
    rms_keV[2] = 20.969644*calibration_values[2]  # +/- 0.000226 
    rms_keV_sigma[2] = 1.120212*calibration_values[2] # +/- 0.000160
    rms_keV[3] = 20.671686*calibration_values[3]  # +/- 0.000226 
    rms_keV_sigma[3] = 1.121889*calibration_values[3] # +/- 0.000160
    rms_keV[4] = 7.544668*calibration_values[4]  # +/- 0.000095 
    rms_keV_sigma[4] = 0.471945*calibration_values[4] # +/- 0.000067
    rms_keV[5] = 8.683733*calibration_values[5]  # +/- 0.000110 
    rms_keV_sigma[5] = 0.545730*calibration_values[5] # +/- 0.000078
    rms_keV[6] = 9.242321*calibration_values[6]  # +/- 0.000115 
    rms_keV_sigma[6] = 0.570915*calibration_values[6] # +/- 0.000081
    rms_keV[7] = 8.717167*calibration_values[7]  # +/- 0.000151 
    rms_keV_sigma[7] = 0.749143*calibration_values[7] # +/- 0.000107
    rms_keV[8] = 21.366966*calibration_values[8]  # +/- 0.000241 
    rms_keV_sigma[8] = 1.196606*calibration_values[8] # +/- 0.000171
    rms_keV[9] = 20.577530*calibration_values[9]  # +/- 0.000236 
    rms_keV_sigma[9] = 1.172323*calibration_values[9] # +/- 0.000167
    rms_keV[10] = 21.326033*calibration_values[10]  # +/- 0.000229 
    rms_keV_sigma[10] = 1.138030*calibration_values[10] # +/- 0.000162
    rms_keV[11] = 25.145735*calibration_values[11]  # +/- 0.000283 
    rms_keV_sigma[11] = 1.403506*calibration_values[11] # +/- 0.000200
    rms_keV[12] = 23.639935*calibration_values[12]  # +/- 0.000293 
    rms_keV_sigma[12] = 1.453611*calibration_values[12] # +/- 0.000207
    rms_keV[13] = 24.594816*calibration_values[13]  # +/- 0.000280 
    rms_keV_sigma[13] = 1.388630*calibration_values[13] # +/- 0.000198
    rms_keV[14] = 21.846698*calibration_values[14]  # +/- 0.000253 
    rms_keV_sigma[14] = 1.256562*calibration_values[14] # +/- 0.000179
    rms_keV[15] = 18.967606*calibration_values[15]  # +/- 0.000222 
    rms_keV_sigma[15] = 1.102184*calibration_values[15] # +/- 0.000157
    rms_keV[16] = 42.969472*calibration_values[16]  # +/- 0.000624 
    rms_keV_sigma[16] = 3.095251*calibration_values[16] # +/- 0.000441
    rms_keV[17] = 20.987097*calibration_values[17]  # +/- 0.000225 
    rms_keV_sigma[17] = 1.117466*calibration_values[17] # +/- 0.000159
    rms_keV[18] = 21.208325*calibration_values[18]  # +/- 0.000234 
    rms_keV_sigma[18] = 1.159832*calibration_values[18] # +/- 0.000165
    rms_keV[19] = 20.525007*calibration_values[19]  # +/- 0.000221 
    rms_keV_sigma[19] = 1.097417*calibration_values[19] # +/- 0.000156
    rms_keV[20] = 8.989174*calibration_values[20]  # +/- 0.000116 
    rms_keV_sigma[20] = 0.576075*calibration_values[20] # +/- 0.000082
    rms_keV[21] = 8.841458*calibration_values[21]  # +/- 0.000135 
    rms_keV_sigma[21] = 0.671244*calibration_values[21] # +/- 0.000096
    rms_keV[22] = 9.029190*calibration_values[22]  # +/- 0.000121 
    rms_keV_sigma[22] = 0.597769*calibration_values[22] # +/- 0.000085
    rms_keV[23] = 8.596233*calibration_values[23]  # +/- 0.000106 
    rms_keV_sigma[23] = 0.524314*calibration_values[23] # +/- 0.000075
    rms_keV[24] = 18.118557*calibration_values[24]  # +/- 0.000203 
    rms_keV_sigma[24] = 1.007719*calibration_values[24] # +/- 0.000144
    rms_keV[25] = 20.930787*calibration_values[25]  # +/- 0.000223 
    rms_keV_sigma[25] = 1.105085*calibration_values[25] # +/- 0.000158
    rms_keV[26] = 22.084362*calibration_values[26]  # +/- 0.000236 
    rms_keV_sigma[26] = 1.167919*calibration_values[26] # +/- 0.000167
    rms_keV[27] = 3.605056*calibration_values[27]  # +/- 0.000957 
    rms_keV_sigma[27] = 4.718354*calibration_values[27] # +/- 0.000677
    rms_keV[28] = 23.245143*calibration_values[28]  # +/- 0.000262 
    rms_keV_sigma[28] = 1.301311*calibration_values[28] # +/- 0.000186
    rms_keV[29] = 23.988151*calibration_values[29]  # +/- 0.000301 
    rms_keV_sigma[29] = 1.493171*calibration_values[29] # +/- 0.000213
    rms_keV[30] = 13.949614*calibration_values[30]  # +/- 0.000215 
    rms_keV_sigma[30] = 1.063978*calibration_values[30] # +/- 0.000152
    rms_keV[31] = 2.829068*calibration_values[31]  # +/- 0.000609 
    rms_keV_sigma[31] = 3.021563*calibration_values[31] # +/- 0.000431

if is_10th_LXe or is_11th_LXe:
    # Fits are in RMSNoise_overnight10thLXe_v0.pdf 
    rms_keV[0] = 2.942688*calibration_values[0]  # +/- 0.000961 PMT
    rms_keV_sigma[0] = 3.384893*calibration_values[0] # +/- 0.000680 PMT
    rms_keV[1] = 3.064697*calibration_values[1]  # +/- 0.002321 pulser
    rms_keV_sigma[1] = 8.052965*calibration_values[1] # +/- 0.001641 pulser
    rms_keV[2] = 21.721502*calibration_values[2]  # +/- 0.000340 Y20
    rms_keV_sigma[2] = 1.198424*calibration_values[2] # +/- 0.000241 Y20
    rms_keV[3] = 20.953917*calibration_values[3]  # +/- 0.000351 Y19
    rms_keV_sigma[3] = 1.234869*calibration_values[3] # +/- 0.000248 Y19
    rms_keV[4] = 21.753272*calibration_values[4]  # +/- 0.000389 Y18
    rms_keV_sigma[4] = 1.369417*calibration_values[4] # +/- 0.000275 Y18
    rms_keV[5] = 8.874405*calibration_values[5]  # +/- 0.000219 Y17
    rms_keV_sigma[5] = 0.772094*calibration_values[5] # +/- 0.000155 Y17
    rms_keV[6] = 9.125251*calibration_values[6]  # +/- 0.000170 Y16
    rms_keV_sigma[6] = 0.597629*calibration_values[6] # +/- 0.000120 Y16
    rms_keV[7] = 8.378714*calibration_values[7]  # +/- 0.000159 Y15
    rms_keV_sigma[7] = 0.560048*calibration_values[7] # +/- 0.000112 Y15
    rms_keV[8] = 4.929535*calibration_values[8]  # +/- 0.000438 Y14
    rms_keV_sigma[8] = 1.544388*calibration_values[8] # +/- 0.000310 Y14
    rms_keV[9] = 20.382899*calibration_values[9]  # +/- 0.000319 X20
    rms_keV_sigma[9] = 1.124425*calibration_values[9] # +/- 0.000226 X20
    rms_keV[10] = 8.575742*calibration_values[10]  # +/- 0.000154 X19
    rms_keV_sigma[10] = 0.541603*calibration_values[10] # +/- 0.000109 X19
    rms_keV[11] = 8.823364*calibration_values[11]  # +/- 0.000176 X18
    rms_keV_sigma[11] = 0.620655*calibration_values[11] # +/- 0.000125 X18
    rms_keV[12] = 12.049491*calibration_values[12]  # +/- 0.000590 X17
    rms_keV_sigma[12] = 2.077846*calibration_values[12] # +/- 0.000417 X17
    rms_keV[13] = 8.868694*calibration_values[13]  # +/- 0.000172 X16
    rms_keV_sigma[13] = 0.604950*calibration_values[13] # +/- 0.000121 X16
    rms_keV[14] = 20.753262*calibration_values[14]  # +/- 0.000328 X15
    rms_keV_sigma[14] = 1.155172*calibration_values[14] # +/- 0.000232 X15
    rms_keV[15] = 20.543442*calibration_values[15]  # +/- 0.000324 X14
    rms_keV_sigma[15] = 1.139844*calibration_values[15] # +/- 0.000229 X14
     
if is_11th_LXeB: 

    # Fits are in RMSNoise_overnight_11thLXe_v1.pdf 
    rms_keV[0] = 38.427647*calibration_values[0]  # +/- 0.001051 Y1-10
    rms_keV_sigma[0] = 2.888755*calibration_values[0] # +/- 0.000743 Y1-10
    rms_keV[1] = 20.427801*calibration_values[1]  # +/- 0.000405 Y11
    rms_keV_sigma[1] = 1.114368*calibration_values[1] # +/- 0.000287 Y11
    rms_keV[2] = 21.353911*calibration_values[2]  # +/- 0.000411 Y12
    rms_keV_sigma[2] = 1.130243*calibration_values[2] # +/- 0.000291 Y12
    rms_keV[3] = 20.443485*calibration_values[3]  # +/- 0.000412 Y13
    rms_keV_sigma[3] = 1.131377*calibration_values[3] # +/- 0.000291 Y13
    rms_keV[4] = 7.574701*calibration_values[4]  # +/- 0.000162 Y14
    rms_keV_sigma[4] = 0.444984*calibration_values[4] # +/- 0.000114 Y14
    rms_keV[5] = 8.640510*calibration_values[5]  # +/- 0.000203 Y15
    rms_keV_sigma[5] = 0.557909*calibration_values[5] # +/- 0.000144 Y15
    rms_keV[6] = 9.159058*calibration_values[6]  # +/- 0.000206 Y16
    rms_keV_sigma[6] = 0.566259*calibration_values[6] # +/- 0.000146 Y16
    rms_keV[7] = 8.740374*calibration_values[7]  # +/- 0.000263 Y17
    rms_keV_sigma[7] = 0.723035*calibration_values[7] # +/- 0.000186 Y17
    rms_keV[8] = 21.398611*calibration_values[8]  # +/- 0.000435 Y18
    rms_keV_sigma[8] = 1.195448*calibration_values[8] # +/- 0.000308 Y18
    rms_keV[9] = 20.882513*calibration_values[9]  # +/- 0.000432 Y19
    rms_keV_sigma[9] = 1.186432*calibration_values[9] # +/- 0.000305 Y19
    rms_keV[10] = 21.770624*calibration_values[10]  # +/- 0.000423 Y20
    rms_keV_sigma[10] = 1.161899*calibration_values[10] # +/- 0.000299 Y20
    rms_keV[11] = 24.990441*calibration_values[11]  # +/- 0.000511 Y21/22
    rms_keV_sigma[11] = 1.404009*calibration_values[11] # +/- 0.000361 Y21/22
    rms_keV[12] = 23.780802*calibration_values[12]  # +/- 0.000510 Y23/24
    rms_keV_sigma[12] = 1.400996*calibration_values[12] # +/- 0.000360 Y23/24
    rms_keV[13] = 25.045486*calibration_values[13]  # +/- 0.000513 Y25/26
    rms_keV_sigma[13] = 1.410798*calibration_values[13] # +/- 0.000363 Y25/26
    rms_keV[14] = 23.916775*calibration_values[14]  # +/- 0.000490 Y27/28
    rms_keV_sigma[14] = 1.346593*calibration_values[14] # +/- 0.000346 Y27/28
    rms_keV[15] = 20.805862*calibration_values[15]  # +/- 0.000429 Y29/30
    rms_keV_sigma[15] = 1.178856*calibration_values[15] # +/- 0.000303 Y29/30
    rms_keV[16] = 43.001056*calibration_values[16]  # +/- 0.001174 X1-12
    rms_keV_sigma[16] = 3.227455*calibration_values[16] # +/- 0.000830 X1-12
    rms_keV[17] = 20.401463*calibration_values[17]  # +/- 0.000406 X13
    rms_keV_sigma[17] = 1.114925*calibration_values[17] # +/- 0.000287 X13
    rms_keV[18] = 20.924138*calibration_values[18]  # +/- 0.000413 X14
    rms_keV_sigma[18] = 1.135735*calibration_values[18] # +/- 0.000292 X14
    rms_keV[19] = 20.451969*calibration_values[19]  # +/- 0.000405 X15
    rms_keV_sigma[19] = 1.111658*calibration_values[19] # +/- 0.000286 X15
    rms_keV[20] = 8.854004*calibration_values[20]  # +/- 0.000205 X16
    rms_keV_sigma[20] = 0.564320*calibration_values[20] # +/- 0.000145 X16
    rms_keV[21] = 8.830371*calibration_values[21]  # +/- 0.000222 X17
    rms_keV_sigma[21] = 0.610696*calibration_values[21] # +/- 0.000157 X17
    rms_keV[22] = 8.898265*calibration_values[22]  # +/- 0.000207 X18
    rms_keV_sigma[22] = 0.569978*calibration_values[22] # +/- 0.000147 X18
    rms_keV[23] = 8.610739*calibration_values[23]  # +/- 0.000191 X19
    rms_keV_sigma[23] = 0.524468*calibration_values[23] # +/- 0.000135 X19
    rms_keV[24] = 20.090180*calibration_values[24]  # +/- 0.000396 X20
    rms_keV_sigma[24] = 1.087208*calibration_values[24] # +/- 0.000280 X20
    rms_keV[25] = 20.767843*calibration_values[25]  # +/- 0.000400 X21
    rms_keV_sigma[25] = 1.099497*calibration_values[25] # +/- 0.000283 X21
    rms_keV[26] = 21.655278*calibration_values[26]  # +/- 0.000419 X22
    rms_keV_sigma[26] = 1.152086*calibration_values[26] # +/- 0.000296 X22
    rms_keV[27] = 20.806659*calibration_values[27]  # +/- 0.000402 X23/24
    rms_keV_sigma[27] = 1.103967*calibration_values[27] # +/- 0.000284 X23/24
    rms_keV[28] = 23.729976*calibration_values[28]  # +/- 0.000480 X25/26
    rms_keV_sigma[28] = 1.319759*calibration_values[28] # +/- 0.000340 X25/26
    rms_keV[29] = 24.925436*calibration_values[29]  # +/- 0.000527 X27/28
    rms_keV_sigma[29] = 1.449296*calibration_values[29] # +/- 0.000373 X27/28
    rms_keV[30] = 2.623402*calibration_values[30]  # +/- 0.000074 pulser
    rms_keV_sigma[30] = 0.202326*calibration_values[30] # +/- 0.000052 pulser
    rms_keV[31] = 2.861805*calibration_values[31]  # +/- 0.001108 PMT
    rms_keV_sigma[31] = 3.044990*calibration_values[31] # +/- 0.000784 PMT

if is_12th_LXe or is_13th_LXe:
    #if is_15th_LXe: 
    #    rms_threshold=30
    #WRONG Add RMS noise
    rms_keV[0] = 21.353911*calibration_values[0]  # +/- 0.000411 Y12
    rms_keV_sigma[0] = 1.130243*calibration_values[0] # +/- 0.000291 Y12
    rms_keV[1] = 20.443485*calibration_values[1]  # +/- 0.000412 Y13
    rms_keV_sigma[1] = 1.131377*calibration_values[1] # +/- 0.000291 Y13
    rms_keV[2] = 7.574701*calibration_values[2]  # +/- 0.000162 Y14
    rms_keV_sigma[2] = 0.444984*calibration_values[2] # +/- 0.000114 Y14
    rms_keV[3] = 8.640510*calibration_values[3]  # +/- 0.000203 Y15
    rms_keV_sigma[3] = 0.557909*calibration_values[3] # +/- 0.000144 Y15
    rms_keV[4] = 9.159058*calibration_values[4]  # +/- 0.000206 Y16
    rms_keV_sigma[4] = 0.566259*calibration_values[4] # +/- 0.000146 Y16
    rms_keV[5] = 8.740374*calibration_values[5]  # +/- 0.000263 Y17
    rms_keV_sigma[5] = 0.723035*calibration_values[5] # +/- 0.000186 Y17
    rms_keV[6] = 21.398611*calibration_values[6]  # +/- 0.000435 Y18
    rms_keV_sigma[6] = 1.195448*calibration_values[6] # +/- 0.000308 Y18
    rms_keV[7] = 20.882513*calibration_values[7]  # +/- 0.000432 Y19
    rms_keV_sigma[7] = 1.186432*calibration_values[7] # +/- 0.000305 Y19
    rms_keV[8] = 21.770624*calibration_values[8]  # +/- 0.000423 Y20
    rms_keV_sigma[8] = 1.161899*calibration_values[8] # +/- 0.000299 Y20
    rms_keV[9] = 21.770624*calibration_values[9]  #S1
    rms_keV_sigma[9] = 1.161899*calibration_values[9] #S1
    rms_keV[10] = 21.770624*calibration_values[10]  #S2
    rms_keV_sigma[10] = 1.161899*calibration_values[10] #S2
    rms_keV[11] = 21.770624*calibration_values[11]  #S3
    rms_keV_sigma[11] = 1.161899*calibration_values[11] #S3
    rms_keV[12] = 21.770624*calibration_values[12]  #S4
    rms_keV_sigma[12] = 1.161899*calibration_values[12] #S4
    rms_keV[13] = 21.770624*calibration_values[13]  #S5
    rms_keV_sigma[13] = 1.161899*calibration_values[13] #S5
    rms_keV[14] = 19.178577*calibration_values[14]
    rms_keV_sigma[14] = 1.161899*calibration_values[14] #Dead
    rms_keV[15] = 22.838138*calibration_values[15]
    rms_keV_sigma[15] = 1.161899*calibration_values[15] #Dead

    rms_keV[16] = 20.401463*calibration_values[16]  # +/- 0.000406 X13
    rms_keV_sigma[16] = 1.114925*calibration_values[16] # +/- 0.000287 X13
    rms_keV[17] = 20.924138*calibration_values[17]  # +/- 0.000413 X14
    rms_keV_sigma[17] = 1.135735*calibration_values[17] # +/- 0.000292 X14
    rms_keV[18] = 20.451969*calibration_values[18]  # +/- 0.000405 X15
    rms_keV_sigma[18] = 1.111658*calibration_values[18] # +/- 0.000286 X15
    rms_keV[19] = 8.854004*calibration_values[19]  # +/- 0.000205 X16
    rms_keV_sigma[19] = 0.564320*calibration_values[19] # +/- 0.000145 X16
    rms_keV[20] = 8.830371*calibration_values[20]  # +/- 0.000222 X17
    rms_keV_sigma[20] = 0.610696*calibration_values[20] # +/- 0.000157 X17
    rms_keV[21] = 8.898265*calibration_values[21]  # +/- 0.000207 X18
    rms_keV_sigma[21] = 0.569978*calibration_values[21] # +/- 0.000147 X18
    rms_keV[22] = 8.610739*calibration_values[22]  # +/- 0.000191 X19
    rms_keV_sigma[22] = 0.524468*calibration_values[22] # +/- 0.000135 X19
    rms_keV[23] = 20.090180*calibration_values[23]  # +/- 0.000396 X20
    rms_keV_sigma[23] = 1.087208*calibration_values[23] # +/- 0.000280 X20
    rms_keV[24] = 20.767843*calibration_values[24]  # +/- 0.000400 X21
    rms_keV_sigma[24] = 1.099497*calibration_values[24] # +/- 0.000283 X21
    rms_keV[25] = 8.854004*calibration_values[25]  # S6
    rms_keV_sigma[25] = 0.564320*calibration_values[25] # S6
    rms_keV[26] = 8.830371*calibration_values[26]  # S7
    rms_keV_sigma[26] = 0.610696*calibration_values[26] # S7
    rms_keV[27] = 8.898265*calibration_values[27]  # S8
    rms_keV_sigma[27] = 0.569978*calibration_values[27] # S8
    rms_keV[28] = 8.610739*calibration_values[28]  # S9
    rms_keV_sigma[28] = 0.524468*calibration_values[28] # S9
    rms_keV[29] = 20.090180*calibration_values[29]  # S10
    rms_keV_sigma[29] = 1.087208*calibration_values[29] # S10
    rms_keV[30] = 20.090180*calibration_values[30]  # S11
    rms_keV_sigma[30] = 1.087208*calibration_values[30] # S11
    rms_keV[31] = 20.090180*calibration_values[31]  # S12
    rms_keV_sigma[31] = 1.087208*calibration_values[31] # S12

if is_15th_LXe or is_17th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe:
    if is_15th_LXe or is_22nd_LXe or is_23rd_LXe or is_24th_LXe: 
        rms_threshold=15   
    if is_17th_LXe:
        rms_threshold=15
    rms_keV[0] = 71.370726*calibration_values[0]
    rms_keV_sigma[0] = 2.856899*calibration_values[0]
    rms_keV[1] = 68.185964*calibration_values[1]
    rms_keV_sigma[1] = 3.281952*calibration_values[1]
    rms_keV[2] = 32.503679*calibration_values[2]
    rms_keV_sigma[2] = 3.974189*calibration_values[2]
    rms_keV[3] = 28.561532*calibration_values[3]
    rms_keV_sigma[3] = 3.927301*calibration_values[3]
    rms_keV[4] = 30.836379*calibration_values[4]
    rms_keV_sigma[4] = 3.787103*calibration_values[4]
    rms_keV[5] = 30.423390*calibration_values[5]
    rms_keV_sigma[5] = 3.739511*calibration_values[5]
    rms_keV[6] = 70.462898*calibration_values[6]
    rms_keV_sigma[6] = 3.945288*calibration_values[6]
    rms_keV[7] = 69.005958*calibration_values[7]
    rms_keV_sigma[7] = 3.001437*calibration_values[7]
    rms_keV[8] = 71.766057*calibration_values[8]
    rms_keV_sigma[8] = 3.252423*calibration_values[8]
    rms_keV[9] = 16.402702*calibration_values[9]
    rms_keV_sigma[9] = 24.874279*calibration_values[9]
    rms_keV[10] = 15.223629*calibration_values[10]
    rms_keV_sigma[10] = 20.244436*calibration_values[10]
    rms_keV[11] = 12.537945*calibration_values[11]
    rms_keV_sigma[11] = 14.940363*calibration_values[11]
    rms_keV[12] = 9.687942*calibration_values[12]
    rms_keV_sigma[12] = 10.754759*calibration_values[12]
    rms_keV[13] = 8.855581*calibration_values[13]
    rms_keV_sigma[13] = 9.169881*calibration_values[13]
    rms_keV[14] = 66.419212*calibration_values[14]
    rms_keV_sigma[14] = 3.125357*calibration_values[14]
    rms_keV[15] = 68.022054*calibration_values[15]
    rms_keV_sigma[15] = 3.066233*calibration_values[15]
    rms_keV[16] = 68.435204*calibration_values[16]
    rms_keV_sigma[16] = 4.205055*calibration_values[16]

    rms_keV[17] = 68.872339*calibration_values[17]
    rms_keV_sigma[17] = 4.363039*calibration_values[17]
    rms_keV[18] = 68.651074*calibration_values[18]
    rms_keV_sigma[18] = 3.954244*calibration_values[18]
    rms_keV[19] = 29.540442*calibration_values[19]
    rms_keV_sigma[19] = 1.627477*calibration_values[19]
    rms_keV[20] = 28.979288*calibration_values[20]
    rms_keV_sigma[20] = 1.529885*calibration_values[20]
    rms_keV[21] = 29.560161*calibration_values[21]
    rms_keV_sigma[21] = 1.733649*calibration_values[21]
    rms_keV[22] = 28.392439*calibration_values[22]
    rms_keV_sigma[22] = 1.408389*calibration_values[22]
    rms_keV[23] = 64.262399*calibration_values[23]
    rms_keV_sigma[23] = 3.890123*calibration_values[23]
    rms_keV[24] = 66.877379*calibration_values[24]
    rms_keV_sigma[24] = 2.853026*calibration_values[24]
    rms_keV[25] = 11.042730*calibration_values[25]
    rms_keV_sigma[25] = 13.427616*calibration_values[25]
    rms_keV[26] = 15.623281*calibration_values[26]
    rms_keV_sigma[26] = 12.866316*calibration_values[26]
    rms_keV[27] = 7.780458*calibration_values[27]
    rms_keV_sigma[27] = 6.602754*calibration_values[27]
    rms_keV[28] = 7.538115*calibration_values[28]
    rms_keV_sigma[28] = 4.464493*calibration_values[28]
    rms_keV[29] = 9.284102*calibration_values[29]
    rms_keV_sigma[29] = 5.683785*calibration_values[29]
    rms_keV[30] = 8.567710*calibration_values[30]
    rms_keV_sigma[30] = 5.621719*calibration_values[30]
    rms_keV[31] = 13.837136*calibration_values[31]
    rms_keV_sigma[31] = 25.425298*calibration_values[31]

if is_28th_LXe:
    rms_threshold=15

    rms_keV[0] = 71.370726*calibration_values[0]
    rms_keV_sigma[0] = 2.856899*calibration_values[0]
    rms_keV[1] = 68.185964*calibration_values[1]
    rms_keV_sigma[1] = 3.281952*calibration_values[1]
    rms_keV[2] = 32.503679*calibration_values[2]
    rms_keV_sigma[2] = 3.974189*calibration_values[2]
    rms_keV[3] = 28.561532*calibration_values[3]
    rms_keV_sigma[3] = 3.927301*calibration_values[3]
    rms_keV[4] = 30.836379*calibration_values[4]
    rms_keV_sigma[4] = 3.787103*calibration_values[4]
    rms_keV[5] = 30.423390*calibration_values[5]
    rms_keV_sigma[5] = 3.739511*calibration_values[5]
    rms_keV[6] = 70.462898*calibration_values[6]
    rms_keV_sigma[6] = 3.945288*calibration_values[6]
    rms_keV[7] = 69.005958*calibration_values[7]
    rms_keV_sigma[7] = 3.001437*calibration_values[7]
    rms_keV[8] = 71.766057*calibration_values[8]
    rms_keV_sigma[8] = 3.252423*calibration_values[8]
    rms_keV[9] = 16.402702*calibration_values[9]
    rms_keV_sigma[9] = 24.874279*calibration_values[9]
    rms_keV[10] = 15.223629*calibration_values[10]
    rms_keV_sigma[10] = 20.244436*calibration_values[10]
    rms_keV[11] = 12.537945*calibration_values[11]
    rms_keV_sigma[11] = 14.940363*calibration_values[11]
    rms_keV[12] = 9.687942*calibration_values[12]
    rms_keV_sigma[12] = 10.754759*calibration_values[12]
    rms_keV[13] = 8.855581*calibration_values[13]
    rms_keV_sigma[13] = 9.169881*calibration_values[13]
    rms_keV[14] = 66.419212*calibration_values[14]
    rms_keV_sigma[14] = 3.125357*calibration_values[14]
    rms_keV[15] = 68.022054*calibration_values[15]
    rms_keV_sigma[15] = 3.066233*calibration_values[15]
    rms_keV[16] = 68.435204*calibration_values[16]
    rms_keV_sigma[16] = 4.205055*calibration_values[16]

    rms_keV[17] = 68.872339*calibration_values[17]
    rms_keV_sigma[17] = 4.363039*calibration_values[17]
    rms_keV[18] = 68.651074*calibration_values[18]
    rms_keV_sigma[18] = 3.954244*calibration_values[18]
    rms_keV[19] = 29.540442*calibration_values[19]
    rms_keV_sigma[19] = 1.627477*calibration_values[19]
    rms_keV[20] = 28.979288*calibration_values[20]
    rms_keV_sigma[20] = 1.529885*calibration_values[20]
    rms_keV[21] = 29.560161*calibration_values[21]
    rms_keV_sigma[21] = 1.733649*calibration_values[21]
    rms_keV[22] = 28.392439*calibration_values[22]
    rms_keV_sigma[22] = 1.408389*calibration_values[22]
    rms_keV[23] = 64.262399*calibration_values[23]
    rms_keV_sigma[23] = 3.890123*calibration_values[23]
    rms_keV[24] = 66.877379*calibration_values[24]
    rms_keV_sigma[24] = 2.853026*calibration_values[24]
    rms_keV[25] = 11.042730*calibration_values[25]
    rms_keV_sigma[25] = 13.427616*calibration_values[25]
    rms_keV[26] = 15.623281*calibration_values[26]
    rms_keV_sigma[26] = 12.866316*calibration_values[26]
    rms_keV[27] = 7.780458*calibration_values[27]
    rms_keV_sigma[27] = 6.602754*calibration_values[27]
    rms_keV[28] = 7.538115*calibration_values[28]
    rms_keV_sigma[28] = 4.464493*calibration_values[28]
    rms_keV[29] = 9.284102*calibration_values[29]
    rms_keV_sigma[29] = 5.683785*calibration_values[29]
    rms_keV[30] = 8.567710*calibration_values[30]
    rms_keV_sigma[30] = 5.621719*calibration_values[30]
    rms_keV[31] = 13.837136*calibration_values[31]
    rms_keV_sigma[31] = 25.425298*calibration_values[31]



if is_29th_LXe:
    rms_threshold=15

    rms_keV[1] = 71.370726*calibration_values[1]
    rms_keV_sigma[1] = 2.856899*calibration_values[1]
    rms_keV[2] = 68.185964*calibration_values[2]
    rms_keV_sigma[2] = 3.281952*calibration_values[2]
    rms_keV[3] = 32.503679*calibration_values[3]
    rms_keV_sigma[3] = 3.974189*calibration_values[3]
    rms_keV[4] = 28.561532*calibration_values[4]
    rms_keV_sigma[4] = 3.927301*calibration_values[4]
    rms_keV[5] = 30.836379*calibration_values[5]
    rms_keV_sigma[5] = 3.787103*calibration_values[5]
    rms_keV[6] = 30.423390*calibration_values[6]
    rms_keV_sigma[6] = 3.739511*calibration_values[6]
    rms_keV[7] = 70.462898*calibration_values[7]
    rms_keV_sigma[7] = 3.945288*calibration_values[7]
    rms_keV[8] = 69.005958*calibration_values[8]
    rms_keV_sigma[8] = 3.001437*calibration_values[8]
    rms_keV[9] = 71.766057*calibration_values[9]
    rms_keV_sigma[9] = 3.252423*calibration_values[9]
    rms_keV[10] = 16.402702*calibration_values[10]
    rms_keV_sigma[10] = 24.874279*calibration_values[10]
    								#random values
    rms_keV[11] = 15.223629*calibration_values[11]		#
    rms_keV_sigma[11] = 20.244436*calibration_values[11]	#
    rms_keV[12] = 12.537945*calibration_values[12]		#
    rms_keV_sigma[12] = 14.940363*calibration_values[12]	#
    rms_keV[13] = 9.687942*calibration_values[13]		#
    rms_keV_sigma[13] = 10.754759*calibration_values[13]	#
    rms_keV[14] = 8.855581*calibration_values[14]		#
    rms_keV_sigma[14] = 9.169881*calibration_values[14]		#
    rms_keV[15] = 66.419212*calibration_values[15]		#
    rms_keV_sigma[15] = 3.125357*calibration_values[15]		#
    rms_keV[16] = 68.022054*calibration_values[16]		#
    rms_keV_sigma[16] = 3.066233*calibration_values[16]		#

    rms_keV[17] = 68.435204*calibration_values[17]
    rms_keV_sigma[17] = 4.205055*calibration_values[17]
    rms_keV[18] = 68.872339*calibration_values[18]
    rms_keV_sigma[18] = 4.363039*calibration_values[18]
    rms_keV[19] = 68.651074*calibration_values[19]
    rms_keV_sigma[19] = 3.954244*calibration_values[19]
    rms_keV[20] = 29.540442*calibration_values[20]
    rms_keV_sigma[20] = 1.627477*calibration_values[20]
    rms_keV[21] = 28.979288*calibration_values[21]
    rms_keV_sigma[21] = 1.529885*calibration_values[21]
    rms_keV[22] = 29.560161*calibration_values[22]
    rms_keV_sigma[22] = 1.733649*calibration_values[22]
    rms_keV[23] = 28.392439*calibration_values[23]
    rms_keV_sigma[23] = 1.408389*calibration_values[23]
    rms_keV[24] = 64.262399*calibration_values[24]
    rms_keV_sigma[24] = 3.890123*calibration_values[24]
    rms_keV[25] = 66.877379*calibration_values[25]
    rms_keV_sigma[25] = 2.853026*calibration_values[25]
    rms_keV[26] = 11.042730*calibration_values[26]
    rms_keV_sigma[26] = 13.427616*calibration_values[26]
    rms_keV[27] = 15.623281*calibration_values[27]
    rms_keV_sigma[27] = 12.866316*calibration_values[27]

    rms_keV[28] = 7.780458*calibration_values[28]		#random values
    rms_keV_sigma[28] = 6.602754*calibration_values[28]		#
    rms_keV[29] = 7.538115*calibration_values[29]		#
    rms_keV_sigma[29] = 4.464493*calibration_values[29]		#
    rms_keV[30] = 9.284102*calibration_values[30]		#
    rms_keV_sigma[30] = 5.683785*calibration_values[30]		#
    rms_keV[31] = 8.567710*calibration_values[31]		#
    rms_keV_sigma[31] = 5.621719*calibration_values[31]		#
    rms_keV[0] = 13.837136*calibration_values[0]		#
    rms_keV_sigma[0] = 25.425298*calibration_values[0]		#




tileCh_to_PreCh = {}
if is_8th_LXe or is_9th_LXe:
    tileCh_to_PreCh[0] = 16
    tileCh_to_PreCh[1] = 16
    tileCh_to_PreCh[2] = 16
    tileCh_to_PreCh[3] = 16
    tileCh_to_PreCh[4] = 16
    tileCh_to_PreCh[5] = 16
    tileCh_to_PreCh[6] = 16
    tileCh_to_PreCh[7] = 16
    tileCh_to_PreCh[8] = 16
    tileCh_to_PreCh[9] = 16
    tileCh_to_PreCh[10] = 16
    tileCh_to_PreCh[11] = 16
    tileCh_to_PreCh[12] = 17
    tileCh_to_PreCh[13] = 18
    tileCh_to_PreCh[14] = 19
    tileCh_to_PreCh[15] = 20
    tileCh_to_PreCh[16] = 21
    tileCh_to_PreCh[17] = 22
    tileCh_to_PreCh[18] = 23
    tileCh_to_PreCh[19] = 24
    tileCh_to_PreCh[20] = 25
    tileCh_to_PreCh[21] = 26
    tileCh_to_PreCh[22] = 27
    tileCh_to_PreCh[23] = 27
    tileCh_to_PreCh[24] = 28
    tileCh_to_PreCh[25] = 28
    tileCh_to_PreCh[26] = 29
    tileCh_to_PreCh[27] = 29
    tileCh_to_PreCh[28] = 30
    tileCh_to_PreCh[29] = 30
    tileCh_to_PreCh[30] = 0
    tileCh_to_PreCh[31] = 0
    tileCh_to_PreCh[32] = 0
    tileCh_to_PreCh[33] = 0
    tileCh_to_PreCh[34] = 0
    tileCh_to_PreCh[35] = 0
    tileCh_to_PreCh[36] = 0
    tileCh_to_PreCh[37] = 0
    tileCh_to_PreCh[38] = 0
    tileCh_to_PreCh[39] = 0
    tileCh_to_PreCh[40] = 1
    tileCh_to_PreCh[41] = 2
    tileCh_to_PreCh[42] = 3
    tileCh_to_PreCh[43] = 4
    tileCh_to_PreCh[44] = 5
    tileCh_to_PreCh[45] = 6
    tileCh_to_PreCh[46] = 7
    tileCh_to_PreCh[47] = 8
    tileCh_to_PreCh[48] = 9
    tileCh_to_PreCh[49] = 10
    tileCh_to_PreCh[50] = 11
    tileCh_to_PreCh[51] = 11
    tileCh_to_PreCh[52] = 12
    tileCh_to_PreCh[53] = 12
    tileCh_to_PreCh[54] = 13
    tileCh_to_PreCh[55] = 13
    tileCh_to_PreCh[56] = 14
    tileCh_to_PreCh[57] = 14
    tileCh_to_PreCh[58] = 15
    tileCh_to_PreCh[59] = 15

if is_28th_LXe:
    tileCh_to_PreCh[0]  = 0
    tileCh_to_PreCh[1]  = 0
    tileCh_to_PreCh[2]  = 0
    tileCh_to_PreCh[3]  = 0
    tileCh_to_PreCh[4]  = 0
    tileCh_to_PreCh[5]  = 0
    tileCh_to_PreCh[6]  = 0
    tileCh_to_PreCh[7]  = 0
    tileCh_to_PreCh[8]  = 0
    tileCh_to_PreCh[9]  = 0
    tileCh_to_PreCh[10] = 0
#==============================
    tileCh_to_PreCh[11] = 0
    tileCh_to_PreCh[12] = 1
    tileCh_to_PreCh[13] = 2
    tileCh_to_PreCh[14] = 3
    tileCh_to_PreCh[15] = 4
    tileCh_to_PreCh[16] = 5
    tileCh_to_PreCh[17] = 6
    tileCh_to_PreCh[18] = 7
    tileCh_to_PreCh[19] = 8
    tileCh_to_PreCh[20] = 9
#==============================
    tileCh_to_PreCh[21] = 0
    tileCh_to_PreCh[22] = 0
    tileCh_to_PreCh[23] = 0
    tileCh_to_PreCh[24] = 0
    tileCh_to_PreCh[25] = 0
    tileCh_to_PreCh[26] = 0
    tileCh_to_PreCh[27] = 0
    tileCh_to_PreCh[28] = 0
    tileCh_to_PreCh[29] = 0
    tileCh_to_PreCh[30] = 0

    tileCh_to_PreCh[31] = 0
    tileCh_to_PreCh[32] = 0
    tileCh_to_PreCh[33] = 0
    tileCh_to_PreCh[34] = 0
    tileCh_to_PreCh[35] = 0
    tileCh_to_PreCh[36] = 0
    tileCh_to_PreCh[37] = 0
    tileCh_to_PreCh[38] = 0
    tileCh_to_PreCh[39] = 0
    tileCh_to_PreCh[40] = 0
#==================================
    tileCh_to_PreCh[41] = 16
    tileCh_to_PreCh[42] = 17
    tileCh_to_PreCh[43] = 18
    tileCh_to_PreCh[44] = 19
    tileCh_to_PreCh[45] = 20
    tileCh_to_PreCh[46] = 21
    tileCh_to_PreCh[47] = 22
    tileCh_to_PreCh[48] = 23
    tileCh_to_PreCh[49] = 24
    tileCh_to_PreCh[50] = 25
#==================================
    tileCh_to_PreCh[51] = 0
    tileCh_to_PreCh[52] = 0
    tileCh_to_PreCh[53] = 0
    tileCh_to_PreCh[54] = 0
    tileCh_to_PreCh[55] = 0
    tileCh_to_PreCh[56] = 0
    tileCh_to_PreCh[57] = 0
    tileCh_to_PreCh[58] = 0
    tileCh_to_PreCh[59] = 0   




avg_rms_keV = sum(rms_keV.values())/len(rms_keV)

# contributions to chargeEnergy, energy1_pz:
chargeEnergy_rms_keV = 0.0
energy1_pz_digitization_noise_keV = 0.0
for channel, value in enumerate(charge_channels_to_use):
    if value:
        rms = rms_keV[channel]*math.sqrt(2.0/n_baseline_samples)
        chargeEnergy_rms_keV += math.pow(rms,2.0)
        dig_rms = calibration_values[channel]*0.5 # 0.5 ADC units
        energy1_pz_digitization_noise_keV += math.pow(dig_rms, 2.0)
chargeEnergy_rms_keV = math.sqrt(chargeEnergy_rms_keV)
energy1_pz_rms_keV = avg_rms_keV*math.sqrt(2.0/n_baseline_samples) 
energy1_pz_digitization_noise_keV = math.sqrt(energy1_pz_digitization_noise_keV)/n_chargechannels

# from NEST MC:
# /nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/electron_570keV_Ralph/MC/
nest_resolution_570 = 1.46847e+03/2.71292e+04

def is_2Vinput(baseline_mean_file): #FIXME--will be included in the tree so no longer needed
    """
    If using 2V input (instead of 5V), divide calibration by 2.5
    Argument: average baseline mean from a file, for a given charge channel
    This only identifies amplified channels with 2V input
    """
    if baseline_mean_file < 6500:
        return True
    return False


#This doesn't seem reliable...
def is_amplified(baseline_mean_file, baseline_rms_file):
    """
    If not amplified, multiply calibration by 4.0 (10x gain, 2V input) 
    Arguments: average baseline mean and RMS from a file, for a given charge
    channel
    """
    print "WARNING: identifying amplification is risky!!"
    if baseline_mean_file >= 6500:
        if baseline_rms_file < 6.0:
            return False
    return True


if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)

    print "\nsystem constants:"
    print "\t drift_length:", drift_length
    print "\t drift_velocity:", drift_velocity
    print "\t drift_time_threshold:", drift_time_threshold
    print "\t max_drift_time:", max_drift_time

    print "\nprocessing parameters:"
    print "\t baseline_average_time_microseconds:", baseline_average_time_microseconds
    print "\t baseline_average_time [samples @ 25 MHz]:", baseline_average_time_microseconds*microsecond*sampling_freq_Hz/second
    print "\t baseline_average_time [samples @ 125 MHz]:", baseline_average_time_microseconds*microsecond*sampling_freq_Hz*5/second
    print "\t energy_start_time_microseconds:", energy_start_time_microseconds
    print "\t energy_start_time [samples at 25 MHz]:", energy_start_time_microseconds*microsecond*sampling_freq_Hz/second
    print "\t energy_start_time [samples at 125 MHz]:", energy_start_time_microseconds*microsecond*sampling_freq_Hz*5/second
    print "\t decay_start_time_microseconds:", decay_start_time_microseconds
    print "\t decay_end_time_microseconds:", decay_end_time_microseconds
    print "\t decay_start_time_microseconds [samples @ 25 MHz]:", decay_start_time_microseconds*microsecond*sampling_freq_Hz/second
    print "\t decay_end_time [samples @ 25 MHz]:", decay_end_time_microseconds*microsecond*sampling_freq_Hz/second

    #print "\nchannels used:"
    #for channel in channels:
    #    print "\t channel %i" % channel

    print "\nchannel     | label  | use | n strips | labels from struck_to_mc_channel_map"
    for (channel, name) in channel_map.items():
        labels = []
        try:
            for strip in struck_to_mc_channel_map[channel]:
                if strip < 30:
                    label = "X%i" % (strip+1)
                else:
                    label = "Y%i" % (strip-30+1)
                labels.append(label)
            labels = ", ".join(labels)
        except: pass
        if len(labels) == 0: labels = ""
        print "\t %2i | %-6s |  %i  | %2i | %s" % (
            channel, 
            name,
            charge_channels_to_use[channel],
            channel_to_n_strips_map[channel],
            labels,
        )

    print "pmt channel:", pmt_channel
    if pulser_channel:
        print "pulser channel:", pulser_channel
    print "n_chargechannels:", n_chargechannels

    # count functional strips:
    n_strips = 0
    print "counting strips in struck_to_mc_channel_map..."
    for channel, val in struck_to_mc_channel_map.items():
        if charge_channels_to_use[channel] == 0: continue
        n_strips += len(val)
        print "\t %i, %s, %i" % (channel, channel_map[channel], len(val))
    print "n_strips:", n_strips

    if len(mc_channel_map) > 0:
        print "\nMC channel names:"
        for (channel, name) in mc_channel_map.items():
            print "\t channel %i: %s" % (channel, name)
    else:
        print "\nNo MC channel names!!"

    print "\nlinear calibration info:"
    for (channel, value) in calibration_values.items():
        print "\t channel %i %s: %.6f" % (channel, channel_map[channel], value)

    print "\ndecay times:"
    for (channel, value) in decay_time_values.items():
        print "\t channel %i [microseconds]: %.1f" % (channel, value/microsecond)

    print "\nRMS noise (keV):"
    for (channel, value) in rms_keV.items():
        print "\t RMS ch %i %s: %.2f | contribution to energy1_pz: %.2f" % (channel, channel_map[channel], value, value*math.sqrt(2.0/n_baseline_samples))

    print "\nMore noise info:"
    print "\taverage RMS noise: %.2f" % avg_rms_keV
    print "\tRMS contribution to chargeEnergy, chargeEnergy_rms_keV: %.4f" % chargeEnergy_rms_keV
    print "\tchargeEnergy_rms_keV/570  [%]:","%.2f" % (chargeEnergy_rms_keV/570.0*100)
    print "\tchargeEnergy_rms_keV/1064 [%]:","%.2f" % (chargeEnergy_rms_keV/1064.0*100)
    print "\tchargeEnergy_rms_keV/1164 [%]:","%.2f" % (chargeEnergy_rms_keV/1164.0*100)
    print "\tRMS contribution to energy1_pz, energy1_pz_rms_keV: %.2f" % energy1_pz_rms_keV 
    print "\tdigitization noise contribution to energy1_pz, energy1_pz_digitization_noise_keV %.2f" % energy1_pz_digitization_noise_keV
    print "\tintrinsic resolution of 570 keV, from NEST [%]:", "%.2f" % (nest_resolution_570*100.0)
    expected_resolution_570 = math.sqrt( \
        (nest_resolution_570*570.0)**2 \
        + energy1_pz_digitization_noise_keV**2 \
        + energy1_pz_rms_keV**2 \
        + (570*0.01)**2 # 1% broadening after z cut
    )
    print "\texpected resolution of energy1_pz @ 570 keV [keV]: %.2f" % expected_resolution_570
    print "\texpected resolution of energy1_pz @ 570 keV [%]:","%.2f" % (expected_resolution_570/570.0*100.0)

    #colors = get_colors()
    #print "\ncolors:"
    #for (i, color) in enumerate(colors):
    #    print "color %i:" % i, color


