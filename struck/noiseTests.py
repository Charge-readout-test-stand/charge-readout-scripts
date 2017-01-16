"""
test different gap & shaping times
"""

import os
import sys
import glob
import commands
import ROOT

import struck_analysis_parameters
#import generateTier3Files
import my_generateTier3Files as generateTier3Files
import wfmProcessing

def baseline_process_file(filename):
    """
    Process tier3 files, vary n_baseline_samples
    takes ~ 4 minutes on aztec if we consider up to 1000 NGM events
    """
    print "--> processing", filename

    default_baseline_average_time_microseconds = struck_analysis_parameters.baseline_average_time_microseconds
    result_files = []

    # different numbers of baseline samples
    for i in xrange(15):
        struck_analysis_parameters.baseline_average_time_microseconds = default_baseline_average_time_microseconds + (i-7)*0.5
        print "i=%i | baseline_average_time_microseconds = %.1f, default = %.1f" % (
            i, 
            struck_analysis_parameters.baseline_average_time_microseconds,
            default_baseline_average_time_microseconds,
        )

        generateTier3Files.process_file(filename)

        out_file_name = wfmProcessing.create_outfile_name(filename)
        new_out_file_name = "%s_%04i_baseline_time.root" % (
            os.path.splitext(out_file_name)[0],
            struck_analysis_parameters.baseline_average_time_microseconds*1e3,
        )
        cmd = "mv %s %s" % (out_file_name, new_out_file_name)
        print cmd
        output = commands.getstatusoutput(cmd)
        if output[0] != 0: print output[1]
        print output[1]
        result_files.append(new_out_file_name)

    return result_files

def gap_process_file(filename):
    """
    Process tier3 files, vary energy_gap_time_microseconds
    """
    print "--> processing", filename

    default_energy_gap_time_microseconds = struck_analysis_parameters.n_energy_gap_time_microseconds
    result_files = []

    # different values of energy_gap_time_microseconds
    for i in xrange(5):
        struck_analysis_parameters.energy_gap_time_microseconds = default_energy_gap_time_microseconds + i*10
        print "i=%i | energy_gap_time_microseconds = %i, default = %i" % (
            i, 
            struck_analysis_parameters.energy_gap_time_microseconds,
            default_energy_gap_time_microseconds,
        )

        generateTier3Files.process_file(filename)

        out_file_name = wfmProcessing.create_outfile_name(filename)
        new_out_file_name = "%s_%i_e_gap.root" % (
            os.path.splitext(out_file_name)[0],
            struck_analysis_parameters.energy_gap_time_microseconds,
        )
        cmd = "mv %s %s" % (out_file_name, new_out_file_name)
        print cmd
        output = commands.getstatusoutput(cmd)
        if output[0] != 0: print output[1]
        print output[1]
        result_files.append(new_out_file_name)

    return result_files


if __name__ == "__main__":

    filename = "/g/g17/alexiss/scratch/2016_09_13_pulser_tests/tier1_SIS3316Raw_20160914184725_digitizer_noise_tests__1-ngm.root"
    filename = "/g/g17/alexiss/scratch/2016_08_15_8th_LXe/tier1/tier1_SIS3316Raw_20160816180708_8thLXe_126mvDT_cell_full_cath_1700V_HVOn_Noise_100cg__1-ngm.root"
    filename = "tier1_SIS3316Raw_20160815193659_8thLXe_30mvDT_filling_1-ngm.root"
    filename = "/g/g17/alexiss/scratch/9thLXe/2016_09_19_overnight/tier1/tier1_SIS3316Raw_20160922140455_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root"

    results = baseline_process_file(filename) # generate new results

    #gap_process_file(filename)


