#!/usr/bin/env python

"""
This script processes new tier0 *.dat files to create tier1 root files

Should probably learn to use popen instead of commands...

notes about batch jobs:
https://confluence.slac.stanford.edu/display/exo/Batch+Jobs+without+the+Pipeline

SLAC info about computing:
http://glast-ground.slac.stanford.edu/workbook/pages/installingOfflineSW/usingSlacBatchFarm.htm

"""

import os
import sys
import commands



def process_file(filename, verbose=True):

    if verbose:
        print "---> processing file: ", filename

    do_batch = True
    #do_batch = False

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    basename = "tier1_" + basename
    #print basename

    if os.path.isfile("%s.root" % basename):
        if verbose:
            print "--> %s.root already exists!!" % basename
        return 0

    #return 1 # debugging

    #script = "/u/xo/alexis4/software/collaborators_alexis/sis3316_offline/Release/sis3316_offline"
    script = "/nfs/slac/g/exo_data4/users/peihaos/charge-readout-scripts/struck_new/sis3316_offline/Release/sis3316_offline"

    cmd =  '(time %s -b %s ) >& %s.out' % (
        script,
        filename,
        basename,
    )
    #print cmd

    # write an executable csh  script
    script = os.fdopen(os.open("%s.csh" % basename, os.O_WRONLY | os.O_CREAT, int("0777", 8)), 'w')
    script.write(cmd)
    script.close()

    #return # debugging

    if do_batch:
        # run in batch queue:
        cmd = "bsub -q xlong -R rhel60 -W 15:00 -J %s -o %s.log %s.csh" % (
            basename,
            basename,
            basename,
        )
    else:
        # run the script from the command line
        cmd = "./%s.csh " % (basename, )

    #return 1 # debugging

    #print cmd
    output = commands.getstatusoutput(cmd)
    if verbose:
        print output[1]
    elif output[0] != 0:
        print output[1]

    return 1


def main(filenames,verbose=True):

    n_files = 0
    for filename in filenames:
        n_files += process_file(filename,verbose)
    return n_files



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis .dat files]"
        sys.exit(1)


    main(sys.argv[1:])

