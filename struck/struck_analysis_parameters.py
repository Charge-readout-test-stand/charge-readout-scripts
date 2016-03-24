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
is_7th_LXe = True


try:
    from ROOT import gROOT
    from ROOT import gSystem
    gSystem.Load("$EXOLIB/lib/libEXOROOT")
    from ROOT import CLHEP
    microsecond = CLHEP.microsecond
except ImportError:
    print "couldn't import CLHEP/ROOT"
    microsecond = 1.0e3

drift_length = 18.16 # mm, from solidworks for 7th LXe + 
drift_velocity = 2.0 # mm / microsecond  

# drift time threshold for 99% signal collection, determined from ion screening
# and cathode effects:
drift_time_threshold = (drift_length - 5.3)/drift_velocity # microsecond


sampling_freq_Hz = 25.0e6 # digitizer sampling frequency, Hz
#FIXME--will be saved in trees so no longer needed

charge_channels_to_use = [0]*16

# in software, struck channels start from 0, not 1
pmt_channel = 8
if is_7th_LXe:
    pmt_channel = 9
if is_6th_LXe:
    # channels for 6th LXe
    channels = [0,1,2,3,4,5,8]
    charge_channels_to_use[0] = 1
    charge_channels_to_use[1] = 1
    charge_channels_to_use[2] = 1
    charge_channels_to_use[3] = 1
    charge_channels_to_use[4] = 1

elif is_7th_LXe:
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


else:
    # channels for 5th LXe
    channels = [0,1,2,3,4,8]
    charge_channels_to_use[0] = 1
    charge_channels_to_use[1] = 1
    charge_channels_to_use[2] = 1
    charge_channels_to_use[3] = 1
    charge_channels_to_use[4] = 1

n_channels = len(channels) # channels that are active

n_chargechannels = 0
for value in charge_channels_to_use:
    n_chargechannels += value  ## number of useful charge channels

# channel names for 6th LXe    
channel_map = {}
channel_map[0] = "X26"
channel_map[1] = "X27"
channel_map[2] = "X29"
channel_map[3] = "Y23"
channel_map[4] = "Y24"
if is_6th_LXe:
    channel_map[5] = "X2" # ortec preamp added 04 Dec for 6th LXe
channel_map[8] = "PMT"
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


#MC Channels index starts at 0 so X26 = 25
#Y  Channles are offset by 30
#MC only has charge no PMT channel
#All MC channels are there but only use the 5 for sum energies
MCchannels = range(60)
MCn_channels = len(MCchannels)

MCcharge_channels_to_use = [0]*60
MCcharge_channels_to_use[25] = 1
MCcharge_channels_to_use[26] = 1 
MCcharge_channels_to_use[28] = 1
MCcharge_channels_to_use[52] = 1
MCcharge_channels_to_use[53] = 1
n_MCchargechannels = sum(MCcharge_channels_to_use)
mc_channel_map = {}
mc_channel_map[25] = "X26"
mc_channel_map[26] = "X27"
mc_channel_map[28] = "X29"
mc_channel_map[52] = "Y23"
mc_channel_map[53] = "Y24"

def is_tree_MC(tree):
    """ test whether tree is of MC results or not"""
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


def get_negative_energy_cut(threshold=-20.0):
    """
    return a cut on events with too much negative energy on any one channel
    """

    selection = []
    for channel, value  in enumerate(charge_channels_to_use): 
        if value:
            cut = "(energy1_pz[%i]<%s)" % (
                channel, 
                threshold,
            )
            #print cut
            selection.append(cut)
            
    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses and add not
    selection = "!(%s)" % selection

    return selection


def get_short_drift_time_cut(
    energy_threshold=200.0,
    drift_time_cut=drift_time_threshold,
):
    """
    Cut any events with energy above threshold and too short a drift time
    """

    selection = []
    for channel, value  in enumerate(charge_channels_to_use): 
        if value:
            cut = "((energy1_pz[%i]>%s) && (rise_time_stop95[%i]-trigger_time<%s))" % (
                channel,
                energy_threshold,
                channel,
                drift_time_cut,
            )
            #print cut
            selection.append(cut)

    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses and add not
    selection = "!(%s)" % selection

    return selection



def get_long_drift_time_cut(
    energy_threshold=200.0,
    drift_time_cut=drift_time_threshold,
):
    """
    Select events with energy above threshold and long enough drift time
    """

    selection = []
    for channel, value  in enumerate(charge_channels_to_use): 
        if value:
            cut = "(energy1_pz[%i]>%s)&&(rise_time_stop95[%i]>%s)" % (
                channel, 
                energy_threshold,
                channel,
                drift_time_cut,
            )
            #print cut
            selection.append(cut)
            
    # join each channel requirement with or
    selection = " || ".join(selection)

    # enclose in parentheses
    selection = "(%s)" % selection

    return selection


def get_single_site_cmd(
    energy_threshold=100.0,
):
    """
    Only count energy from events above threshold
    """

    selection = []
    for channel, value  in enumerate(charge_channels_to_use): 
        if value:
            cut = "(energy1_pz[%i]>%s)*energy1_pz[%i]" % (
                channel, 
                energy_threshold,
                channel,
            )
            #print cut
            selection.append(cut)
            
    # join each channel requirement with or
    selection = " + ".join(selection)

    return selection



#Wvalue for Xenon
#From EXODimensions.hh
#const double W_VALUE_IONIZATION = 15.6*CLHEP::eV;
#const double W_VALUE_LXE_EV_PER_ELECTRON = 18.7*CLHEP::eV;
Wvalue = 18.7 #eV needed to make 1e-

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

if is_7th_LXe:
    decay_time_values[5] = 450.0*microsecond
    decay_time_values[6] = 450.0*microsecond
    decay_time_values[7] = 450.0*microsecond


# charge calbration from these files for 5th LXe:
# tier3_LXe_Run1_1700VC_2chargechannels_609PM_60thresh_NotShaped_Amplified_GapTime20_2_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_5thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_8thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_330PM_7thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_238PM2_10thresh.root

# convert energies to keV by multiplying by these factors:
# NOTE: for 2V input, need to divide by 2.5

calibration_values = {}
calibration_values[0] = 5.827591
calibration_values[1] = 5.146835
calibration_values[2] = 5.331666
calibration_values[3] = 5.096831
calibration_values[4] = 5.586442

if is_7th_LXe:

    # these are guesses (now better guesses 3/8/2016) 
    calibration_values[0] = 4.983489
    calibration_values[1] = 5.291246
    calibration_values[2] = 5.114710
    calibration_values[3] = 5.062006
    calibration_values[4] = 5.223209
    calibration_values[5] = 5.138381
    calibration_values[6] = 4.807294
    calibration_values[7] = 5.034257 

    # PMT
    calibration_values[9] = 2.12352


# PMT calibration is from PMT-triggered data
# EMI 9531QB, 1200V PMT bias, 1700V cathode bias
calibration_values[8] = 0.4470588

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

def get_colors():
    from ROOT import TColor
    
    colors = [
        TColor.kBlue, 
        TColor.kGreen+2, 
        TColor.kViolet+1,
        TColor.kRed, 
        TColor.kOrange+1,
        TColor.kMagenta,
    ]

    colors = [
        TColor.kRed, 
        TColor.kGreen+1, 
        TColor.kBlue, 
        TColor.kBlack, 
        TColor.kTeal, 
        TColor.kOrange+1, 
        #TColor.kPink, 
        TColor.kMagenta, 
        TColor.kCyan+1,
    ]
    return colors

# from tier2to3_overnight.root, baseline_rms
rms_keV = {}
rms_keV[0] = 18.137
rms_keV[1] = 17.557
rms_keV[2] = 17.805
rms_keV[3] = 17.137
rms_keV[4] = 18.182



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
    gROOT.SetBatch(True)

    print "\nsystem constants:"
    print "\t drift_length:", drift_length
    print "\t drift_velocity:", drift_velocity
    print "\t drift_time_threshold:", drift_time_threshold

    print "\nchannels used:"
    for channel in channels:
        print "\t channel %i" % channel

    print "\npmt channel:", pmt_channel

    print "\ncharge channels to use:"
    print "n_chargechannels:", n_chargechannels
    for channel, value  in enumerate(charge_channels_to_use):
        if value:
            print "\t channel %i" % channel

    print "\nchannel names:"
    for (channel, name) in channel_map.items():
        print "\t channel %i: %s" % (channel, name)

    print "\nlinear calibration info:"
    for (channel, value) in calibration_values.items():
        print "\t channel %i: %.6f" % (channel, value)

    print "\ndecay times:"
    for (channel, value) in decay_time_values.items():
        print "\t channel %i [microseconds]: %.1f" % (channel, value/microsecond)


    #colors = get_colors()
    #print "\ncolors:"
    #for (i, color) in enumerate(colors):
    #    print "color %i:" % i, color


    print "\nnegative energy cut:"
    print "\t", get_negative_energy_cut()

    print "\nshort drift time cut:"
    print "\t", get_short_drift_time_cut()

    print "\nlong drift time cut:"
    print "\t", get_long_drift_time_cut()

    print "\nget_single_site_cmd:"
    print "\t", get_single_site_cmd()
