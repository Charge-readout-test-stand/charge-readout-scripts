#!/usr/bin/env python

"""
These are some parameters used for 5th LXe analysis

import this into your script with this line:
import struck_analysis_parameters

This file must be in the same directory as your script. 
"""


try:
    from ROOT import gROOT
    gROOT.SetBatch(True)
    from ROOT import gSystem
    gSystem.Load("$EXOLIB/lib/libEXOROOT")
    from ROOT import CLHEP
    microsecond = CLHEP.microsecond
except ImportError:
    print "couldn't import CLHEP/ROOT"
    microsecond = 1.0e3


# channels for 5th LXe
channels = [0,1,2,3,4,8]

# values from Peihao, 31 Oct 2015:
decay_time_values = {}
decay_time_values[0] = 850.0*microsecond
decay_time_values[1] = 725.0*microsecond
decay_time_values[2] = 775.0*microsecond
decay_time_values[3] = 750.0*microsecond
decay_time_values[4] = 450.0*microsecond
decay_time_values[8] = 1e9*microsecond # FIXME -- should skip PZ for PMT


# calbration from these files:
# tier3_LXe_Run1_1700VC_2chargechannels_609PM_60thresh_NotShaped_Amplified_GapTime20_2_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_5thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_315PM_8thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_330PM_7thresh_0.root
# tier3_LXe_Run1_1700VC_5chargechannels_238PM2_10thresh.root

# convert energy to keV
calibration_values = {}
calibration_values[0] = 1.0/3.76194501827427302e+02*570.0/0.26
calibration_values[1] = 1.0/1.84579440737210035e+02*570.0/0.6
calibration_values[2] = 1.0/1.90907907272149885e+02*570.0/0.56
calibration_values[3] = 1.0/2.94300492610837466e+02*570.0/0.38
calibration_values[4] = 1.0/1.40734817170111285e+02*570.0/0.725



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

    print "\nlinear calibration info:"
    for (channel, value) in calibration_values.items():
        print "\t channel %i: %.6e" % (channel, value)

    print "\ndecay times:"
    for (channel, value) in decay_time_values.items():
        print "\t channel %i [microseconds]: %.1f" % (channel, value/microsecond)

