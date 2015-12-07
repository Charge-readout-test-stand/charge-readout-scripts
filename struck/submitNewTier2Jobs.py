#!/usr/bin/env python

"""
This script processes new tier 1 root files to create tier2 files

Right now this just runs things from the command line; soon it should submit the
job to the cluster.

Should probably learn to use popen instead of commands...

notes about batch jobs:
https://confluence.slac.stanford.edu/display/exo/Batch+Jobs+without+the+Pipeline

SLAC info about computing:
http://glast-ground.slac.stanford.edu/workbook/pages/installingOfflineSW/usingSlacBatchFarm.htm

"""

import os
import sys
import inspect
import commands

import buildTier2EventsUsingTriggerInput


def process_file(filename, verbose=True):

    if verbose:
        print "---> processing file: ", filename

    do_batch = True
    #do_batch = False

    basename = buildTier2EventsUsingTriggerInput.get_basename(filename)
    #print basename

    if os.path.isfile("%s.root" % basename):
        if verbose:
            print "--> %s.root already exists!!" % basename
        return 0

    script_name = os.path.splitext(inspect.getfile(buildTier2EventsUsingTriggerInput))[0] + ".py"
    cmd =  '(time %s %s ) >& %s.out' % (
        script_name,
        filename,
        basename,
    )
    if verbose:
        print cmd

    # write an executable csh  script
    script = os.fdopen(os.open("%s.csh" % basename, os.O_WRONLY | os.O_CREAT, int("0777", 8)), 'w')
    #script.write("#!/bin/csh \n")
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

    if verbose:
        print cmd

    #return 1 # debugging
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
        print "arguments: [sis root files]"
        sys.exit(1)

    main(sys.argv[1:])


