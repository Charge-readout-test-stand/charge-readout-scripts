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
is_7th_LXe = True # March 2016
is_8th_LXe = False # August 2016

if True: # testing 8th LXe
    is_7th_LXe = False
    is_8th_LXe = True

import os
import math
import ROOT

# workaround for systems without EXO offline / CLHEP
microsecond = 1.0e3
if os.getenv("EXOLIB") is not None:
    print os.getenv("EXOLIB")
    try:
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
        from ROOT import CLHEP
        microsecond = CLHEP.microsecond
    except ImportError:
        print "couldn't import CLHEP/ROOT"

drift_length = 18.16 # mm, from solidworks for 7th LXe + 
drift_velocity = 2.0 # mm / microsecond  
max_drift_time = drift_length/drift_velocity

# drift time threshold for 99% signal collection, determined from ion screening
# and cathode effects:
drift_time_threshold = (drift_length - 5.3)/drift_velocity # microsecond


sampling_freq_Hz = 25.0e6 # digitizer sampling frequency, Hz
#FIXME--will be saved in trees so no longer needed

charge_channels_to_use = [0]*16
if is_8th_LXe:
    charge_channels_to_use = [0]*32

# in software, struck channels start from 0, not 1
pmt_channel = 8
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

elif is_8th_LXe:
    pmt_channel = 31
    channels = []
    for i_channel, val in enumerate(charge_channels_to_use):
        channels.append(i_channel)
        charge_channels_to_use[i_channel] = 1
    charge_channels_to_use[pmt_channel] = 0
    charge_channels_to_use[0] = 0 # Y1-10 is dead
    charge_channels_to_use[27] = 0 # X23/24 is dead
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
if is_8th_LXe: # FIXME with real values for 8th LXe
    for i_channel in xrange(n_chargechannels):

        # S/N 97, slot 0, Y channels
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

#MC Channels index starts at 0 so X26 = 25
#Y  Channles are offset by 30
#MC only has charge no PMT channel
#All MC channels are there but only use the 5 for sum energies
MCchannels = range(60)
MCn_channels = len(MCchannels)
MCcharge_channels_to_use = [0]*MCn_channels
mc_channel_map = {} # map MC channel to label
struck_to_mc_channel_map = {} # map struck channel to MC channel
for struck_channel, label in channel_map.items():
    is_y = False
    if "Y" in label:
        is_y = True
    elif "PMT" in label: continue
    if is_8th_LXe:
        mc_channel = struck_channel # FIXME?
    else:
        mc_channel = int(label[1:]) -1
    if is_y: mc_channel += 30
    #print "channel %s: struck=%i | mc=%i" % (label, struck_channel, mc_channel)
    struck_to_mc_channel_map[struck_channel] = mc_channel
    mc_channel_map[mc_channel] = label
    MCcharge_channels_to_use[mc_channel] = 1
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

if is_8th_LXe: # FIXME with real values
    #decay_time_values[i_channel] = 400.0
    decay_time_values[0] =  10000000000.000000*microsecond # Not Used
    decay_time_values[1] =  320.360331*microsecond # +/- 0.465237
    decay_time_values[2] =  339.897228*microsecond # +/- 0.418899
    decay_time_values[3] =  353.919547*microsecond # +/- 0.458101
    decay_time_values[4] =  338.589580*microsecond # +/- 0.372839
    decay_time_values[5] =  426.998773*microsecond # +/- 0.410735
    decay_time_values[6] =  396.597333*microsecond # +/- 0.184746
    decay_time_values[7] =  345.851315*microsecond # +/- 0.045632
    decay_time_values[8] =  319.276194*microsecond # +/- 0.090235
    decay_time_values[9] =  287.563948*microsecond # +/- 0.117011
    decay_time_values[10] =  316.431902*microsecond # +/- 0.179577
    decay_time_values[11] =  323.614588*microsecond # +/- 0.135862
    decay_time_values[12] =  321.055835*microsecond # +/- 0.080225
    decay_time_values[13] =  305.575836*microsecond # +/- 0.206716
    decay_time_values[14] =  333.068070*microsecond # +/- 0.449653
    decay_time_values[15] =  271.529300*microsecond # +/- 0.928347
    decay_time_values[16] =  210.630904*microsecond # +/- 0.351404
    decay_time_values[17] =  390.493199*microsecond # +/- 0.588650
    decay_time_values[18] =  376.382536*microsecond # +/- 0.568273
    decay_time_values[19] =  405.903742*microsecond # +/- 0.374340
    decay_time_values[20] =  420.609430*microsecond # +/- 0.344073
    decay_time_values[21] =  481.202071*microsecond # +/- 0.172892
    decay_time_values[22] =  439.828089*microsecond # +/- 0.265421
    decay_time_values[23] =  445.449339*microsecond # +/- 0.528471
    decay_time_values[24] =  424.413066*microsecond # +/- 0.491970
    decay_time_values[25] =  376.175312*microsecond # +/- 0.397313
    decay_time_values[26] =  396.422580*microsecond # +/- 0.580643
    decay_time_values[27] =  10000000000.000000*microsecond # Not Used
    decay_time_values[28] =  381.161856*microsecond # +/- 0.331977
    decay_time_values[29] =  383.438277*microsecond # +/- 0.183253
    decay_time_values[30] =  364.702498*microsecond # +/- 0.406951
    decay_time_values[31] =  1.5*microsecond # PMT



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

if is_8th_LXe: # FIXME with real values
    for i_channel in xrange(len(channels)):
        calibration_values[i_channel] = 2.5 # initial guess

    # values from fit_peak.py on  entire overnight data set, no rise time cuts, 22 Aug 2016

    calibration_values[1] = 1.042325 # +/- 0.005438
    calibration_values[2] = 1.006970 # +/- 0.005695
    calibration_values[3] = 1.087762 # +/- 0.004540

    # channels 4, 5, 6, 7 are old preamps
    calibration_values[4] = 4.339931 # +/- 0.016867
    calibration_values[5] = 2.096126 # +/- 0.006621
    calibration_values[6] = 1.980758 # +/- 0.004600
    calibration_values[7] = 2.094804 # +/- 0.005325
    calibration_values[8] = 1.059041 # +/- 0.002523
    calibration_values[9] = 1.018659 # +/- 0.002737
    calibration_values[10] = 1.042217 # +/- 0.003316
    calibration_values[11] = 1.063546 # +/- 0.003257
    calibration_values[12] = 1.137803 # +/- 0.003278
    calibration_values[13] = 1.086306 # +/- 0.005576
    calibration_values[14] = 1.113041 # +/- 0.007296
    calibration_values[15] = 1.030522 # +/- 0.010307
    calibration_values[16] = 1.292259 # +/- 0.118818
    calibration_values[17] = 1.059656 # +/- 0.004708
    calibration_values[18] = 1.031070 # +/- 0.003737
    calibration_values[19] = 1.046553 # +/- 0.003188
    calibration_values[20] = 1.991732 # +/- 0.004795
    calibration_values[21] = 2.089875 # +/- 0.006012
    calibration_values[22] = 2.078199 # +/- 0.004894
    calibration_values[23] = 2.243561 # +/- 0.006557
    calibration_values[24] = 0.994050 # +/- 0.003728
    calibration_values[25] = 1.036946 # +/- 0.003930
    calibration_values[26] = 1.082139 # +/- 0.004585
    calibration_values[28] = 1.141378 # +/- 0.003802
    calibration_values[29] = 1.074286 # +/- 0.004627
    calibration_values[30] = 2.146018 # +/- 0.009083



# PMT calibration is from PMT-triggered data
# EMI 9531QB, 1200V PMT bias, 1700V cathode bias
calibration_values[pmt_channel] = 0.4470588

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
if is_8th_LXe:

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
rms_keV = {}
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

if is_8th_LXe: # FIXME with real values
    for i_channel in xrange(len(channels)):
        # Fits are in /home/teststand/2016_08_15_8th_LXe_overnight/tier3_llnl/RMSNoise.pdf
        rms_keV[0] = 0.000000 # Not Used
        rms_keV[1] = 21.884211  # +/- 0.000404
        rms_keV[2] = 22.046994  # +/- 0.000402
        rms_keV[3] = 22.851264  # +/- 0.000434
        rms_keV[4] = 24.093610  # +/- 0.000459
        rms_keV[5] = 18.453813  # +/- 0.000359
        rms_keV[6] = 18.597299  # +/- 0.000348
        rms_keV[7] = 18.139466  # +/- 0.000391
        rms_keV[8] = 23.391371  # +/- 0.000451
        rms_keV[9] = 22.090947  # +/- 0.000418
        rms_keV[10] = 22.909268  # +/- 0.000418
        rms_keV[11] = 27.065265  # +/- 0.000520
        rms_keV[12] = 27.555379  # +/- 0.000540
        rms_keV[13] = 26.697423  # +/- 0.000513
        rms_keV[14] = 27.013082  # +/- 0.000510
        rms_keV[15] = 23.729536  # +/- 0.000731
        rms_keV[16] = 55.623759  # +/- 0.001411
        rms_keV[17] = 22.557860  # +/- 0.000409
        rms_keV[18] = 22.090909  # +/- 0.000411
        rms_keV[19] = 20.764772  # +/- 0.000388
        rms_keV[20] = 18.041777  # +/- 0.000346
        rms_keV[21] = 18.708775  # +/- 0.000365
        rms_keV[22] = 18.779505  # +/- 0.000366
        rms_keV[23] = 17.235608  # +/- 0.000354
        rms_keV[24] = 20.251229  # +/- 0.000369
        rms_keV[25] = 21.805247  # +/- 0.000394
        rms_keV[26] = 24.312676  # +/- 0.000443
        rms_keV[27] = 0.000000 # Not Used
        rms_keV[28] = 27.744116  # +/- 0.000555
        rms_keV[29] = 26.978450  # +/- 0.000536
        rms_keV[30] = 31.734798  # +/- 0.000780
        rms_keV[31] = 0.000000 # PMT



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

    #print "\nchannels used:"
    #for channel in channels:
    #    print "\t channel %i" % channel

    print "\npmt channel:", pmt_channel

    print "\ncharge channels to use:"
    print "n_chargechannels:", n_chargechannels
    for channel, value  in enumerate(charge_channels_to_use):
        if value:
            print "\t channel %i" % channel

    print "\nchannel names:"
    for (channel, name) in channel_map.items():
        print "\t channel %i: %s" % (channel, name)

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
        print "\t RMS channel %i: %.2f | contribution to energy1_pz: %.2f" % (channel, value, value*math.sqrt(2.0/100))
    print "average RMS noise: %.2f" % avg_rms_keV
    print "RMS contribution to chargeEnergy, chargeEnergy_rms_keV: %.4f" % chargeEnergy_rms_keV
    print "chargeEnergy_rms_keV/570  [%]:","%.2f" % (chargeEnergy_rms_keV/570.0*100)
    print "chargeEnergy_rms_keV/1064 [%]:","%.2f" % (chargeEnergy_rms_keV/1064.0*100)
    print "chargeEnergy_rms_keV/1164 [%]:","%.2f" % (chargeEnergy_rms_keV/1164.0*100)
    print "RMS contribution to energy1_pz, energy1_pz_rms_keV: %.2f" % energy1_pz_rms_keV 
    print "digitization noise contribution to energy1_pz, energy1_pz_digitization_noise_keV %.2f" % energy1_pz_digitization_noise_keV
    print "intrinsic resolution of 570 keV, from NEST [%]:", "%.2f" % (nest_resolution_570*100.0)
    expected_resolution_570 = math.sqrt( \
        (nest_resolution_570*570.0)**2 \
        + energy1_pz_digitization_noise_keV**2 \
        + energy1_pz_rms_keV**2 \
        + (570*0.01)**2 # 1% broadening after z cut
    )
    print "expected resolution of energy1_pz @ 570 keV [keV]: %.2f" % expected_resolution_570
    print "expected resolution of energy1_pz @ 570 keV [%]:","%.2f" % (expected_resolution_570/570.0*100.0)

    #colors = get_colors()
    #print "\ncolors:"
    #for (i, color) in enumerate(colors):
    #    print "color %i:" % i, color


