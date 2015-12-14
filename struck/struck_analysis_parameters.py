#!/usr/bin/env python

"""
These are some parameters used for LXe analyses

import this into your script with this line:
import struck_analysis_parameters

This file must be in the same directory as your script. 

notes:
* ortec preamp added 04 Dec for 6th LXe 
"""


try:
    from ROOT import gROOT
    from ROOT import gSystem
    gSystem.Load("$EXOLIB/lib/libEXOROOT")
    from ROOT import CLHEP
    microsecond = CLHEP.microsecond
except ImportError:
    print "couldn't import CLHEP/ROOT"
    microsecond = 1.0e3

is_6th_LXe = True


sampling_freq_Hz = 25.0e6 # digitizer sampling frequency, Hz

charge_channels_to_use = [0]*16

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


# charge calbration from these files for 5th LXe:
# tier3_LXe_Run1_1700VC_2chargechannels_609PM_60thresh_NotShaped_Amplified_GapTime20_2_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_5thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_8thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_330PM_7thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_238PM2_10thresh.root

# convert energies to keV by multiplying by these factors:
calibration_values = {}
calibration_values[0] = 5.827591
calibration_values[1] = 5.146835
calibration_values[2] = 5.331666
calibration_values[3] = 5.096831
calibration_values[4] = 5.586442

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
    return colors




def is_2Vinput(baseline_mean_file):
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

    print "\nchannels used:"
    for channel in channels:
        print "\t channel %i" % channel

    print "\npmt channel:", pmt_channel

    print "\ncharge channels to use:"
    print "n_chargechannels", n_chargechannels
    for channel, value  in enumerate(charge_channels_to_use):
        if value:
            print "\t channel %i" % channel

    print "\nchannel names:"
    for (channel, name) in channel_map.items():
        print "\t channel %i: %s" % (channel, name)

    print "\nlinear calibration info:"
    for (channel, value) in calibration_values.items():
        print "\t channel %i: %.6e" % (channel, value)

    print "\ndecay times:"
    for (channel, value) in decay_time_values.items():
        print "\t channel %i [microseconds]: %.1f" % (channel, value/microsecond)


    colors = get_colors()
    print "\ncolors:"
    for (i, color) in enumerate(colors):
        print "color %i:" % i, color



