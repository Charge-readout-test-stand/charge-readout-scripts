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
is_10th_LXe = True

import os
import math
import ROOT

# workaround for systems without EXO offline / CLHEP
microsecond = 1.0e3

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
        microsecond = CLHEP.microsecond
    except ImportError or AttributeError:
        print "couldn't import CLHEP/ROOT"

drift_length = 18.16 # mm, from solidworks for 7th LXe + 
drift_velocity = 2.0 # mm / microsecond  
if is_10th_LXe:
    drift_length = 33.23 # new anode standoffs Dec 2016
    drift_velocity = 1.85 # mm / microsecond  
max_drift_time = drift_length/drift_velocity

# drift time threshold for 99% signal collection, determined from ion screening
# and cathode effects:
drift_time_threshold = (drift_length - 5.3)/drift_velocity # microsecond


sampling_freq_Hz = 25.0e6 # digitizer sampling frequency, Hz
#FIXME--will be saved in trees so no longer needed

charge_channels_to_use = [0]*16
one_strip_channels = [0]*32
two_strip_channels = [0]*32
channel_to_n_strips_map = [1.0]*32
struck_to_mc_channel_map = {} # map struck channel to MC channel
if is_8th_LXe or is_9th_LXe:
    charge_channels_to_use = [0]*32

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

elif is_8th_LXe or is_9th_LXe:
    pmt_channel = 31
    channels = []
    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        charge_channels_to_use[i_channel] = 1
    charge_channels_to_use[pmt_channel] = 0
    charge_channels_to_use[0] = 0 # Y1-10 is dead
    #charge_channels_to_use[16] = 0 # X1-12 is noisy !!
    charge_channels_to_use[27] = 0 # X23/24 is dead
elif is_10th_LXe:
    pmt_channel = 0
    channels = []
    for i_channel, val in enumerate(charge_channels_to_use):
        if i_channel < 16:
            channels.append(i_channel)
        if i_channel > 1:
            charge_channels_to_use[i_channel] = 1

else:
    # channels for 5th LXe
    channels = [0,1,2,3,4,8]
    charge_channels_to_use[0] = 1
    charge_channels_to_use[1] = 1
    charge_channels_to_use[2] = 1
    charge_channels_to_use[3] = 1
    charge_channels_to_use[4] = 1

n_channels = len(channels) # channels that are active

## number of useful charge channels
n_chargechannels = sum(charge_channels_to_use)

# channel names for 6th LXe    
channel_map = {}
# early runs:
channel_map[0] = "X26"
channel_map[1] = "X27"
channel_map[2] = "X29"
channel_map[3] = "Y23"
channel_map[4] = "Y24"
channel_map[pmt_channel] = "PMT"
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

if is_8th_LXe or is_9th_LXe: 

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

    channel_to_n_strips_map[pmt_channel] = 0.0
    for channel, val in struck_to_mc_channel_map.items():
        n_strips = len(val)
        channel_to_n_strips_map[channel] = n_strips
        if n_strips == 1:
            one_strip_channels[channel] = 1
        elif n_strips == 2:
            two_strip_channels[channel] = 1
if is_9th_LXe:
    pulser_channel = 27
    channel_map[pulser_channel] = "pulser"

if is_10th_LXe:
    pulser_channel = 1
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


#MC Channels index starts at 0 so X26 = 25
#Y  Channles are offset by 30
#MC only has charge no PMT channel
#All MC channels are there but only use the 5 for sum energies

MCchannels = range(60)
MCn_channels = len(MCchannels)
MCcharge_channels_to_use = [0]*MCn_channels
mc_channel_map = {} # map MC channel to label
for struck_channel, label in channel_map.items():
    if is_8th_LXe or is_9th_LXe or is_10th_LXe: break # FIXME -- skip this for now
    is_y = False
    if "Y" in label:
        is_y = True
    elif "PMT" in label: continue
    mc_channel = int(label[1:]) -1
    if is_y: mc_channel += 30
    #print "channel %s: struck=%i | mc=%i" % (label, struck_channel, mc_channel)
    struck_to_mc_channel_map[struck_channel] = mc_channel
    mc_channel_map[mc_channel] = label
    MCcharge_channels_to_use[mc_channel] = 1

if is_8th_LXe or is_9th_LXe:
    MCcharge_channels_to_use = [1]*MCn_channels
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


decay_start_time = 20 #sample 500
decay_end_time = 32   #sample 800
decay_tau_guess = 200 #us

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

if is_10th_LXe: 
    for i_channel in xrange(len(channels)):
        calibration_values[i_channel] = 0.92 # initial guess

    # copied from 9th LXe for now
    calibration_values[8] = 2.428339 # +/- 0.006286 Y14
    calibration_values[7] = 1.912586 # +/- 0.003041 Y15
    calibration_values[6] = 1.818427 # +/- 0.002093 Y16
    calibration_values[5] = 1.914533 # +/- 0.002280 Y17
    calibration_values[4] = 0.964218 # +/- 0.001111 Y18
    calibration_values[3] = 0.917491 # +/- 0.001353 Y19
    calibration_values[2] = 0.955506 # +/- 0.001737 Y20

    calibration_values[15] = 0.939369 # +/- 0.002229 X14
    calibration_values[14] = 0.951769 # +/- 0.001637 X15
    calibration_values[13] = 1.836569 # +/- 0.002156 X16
    calibration_values[12] = 1.917633 # +/- 0.002155 X17
    calibration_values[11] = 1.911182 # +/- 0.002107 X18
    calibration_values[10] = 1.892692 # +/- 0.002967 X19
    calibration_values[9] = 0.936823 # +/- 0.001890 X20



resolution_guess = 0.06*570.0 #Instrinsic Charge Resolution at the 570 guess for fitting peak

# PMT calibration is from PMT-triggered data
# EMI 9531QB, 1200V PMT bias, 1700V cathode bias
#calibration_values[pmt_channel] = 0.4470588


# PMT calibration is from PMT-triggered data
# EMI 9921QB, 1250V PMT bias, 1700V cathode bias
# using Ako's readout chain
calibration_values[pmt_channel] = 0.4470588*3.0

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
if is_8th_LXe or is_9th_LXe or is_10th_LXe:

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

# from tier2to3_overnight.root, baseline_rms
n_baseline_samples = 200.0
# this is not really microseconds, but samples:
energy_gap_time_microseconds = 450*40/1000 # energy calc starts 450 samples after wfm start, in a normal 25-MS/s run
print "energy_gap_time_microseconds:", energy_gap_time_microseconds
print "energy_gap_time_samples:", energy_gap_time_microseconds*sampling_freq_Hz/1e6
baseline_average_time_microseconds = 4.0 # 100 samples at 25 MHz
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

if is_10th_LXe:
    # FIXME -- copied from 9th LXe

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

noiseLightCut = 20.0
noise_length = int(800)
if is_9th_LXe: 
    noise_length = int(800)
    noiseLightCut = 20.0

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

    #print "\nchannels used:"
    #for channel in channels:
    #    print "\t channel %i" % channel

    print "\npmt channel:", pmt_channel

    print "n_chargechannels:", n_chargechannels

    print "\nchannel | label | use | n strips"
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
        print "\t %2i | %-6s | %i  | %2i | %s" % (
            channel, 
            name,
            charge_channels_to_use[channel],
            channel_to_n_strips_map[channel],
            labels,
        )

    print "\nMC channel names:"
    for (channel, name) in mc_channel_map.items():
        print "\t channel %i: %s" % (channel, name)

    print "\nlinear calibration info:"
    for (channel, value) in calibration_values.items():
        print "\t channel %i: %.6f" % (channel, value)

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


