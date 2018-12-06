#!/usr/bin/env python

"""
This script processes new NGM tier0 *.dat files to create tier1 and tier3 root files

Should probably learn to use popen instead of commands...

script to submit only up to 200 jobs at a time for processing at LLNL. 
"""

import os
import sys
import inspect
import commands

from struck.ngm import toRoot
from struck import generateTier3Files

def process_file(filename, verbose=True):

    # options:
    queue = "pbatch" 
    #queue = "pshort" 
    hours = 4
    minutes = 0
    do_batch = True
    #do_batch = False

    if verbose:
        print "---> processing file: ", filename

    #-------------------------------------------------------------------------------
    # tier 1
    #-------------------------------------------------------------------------------

    basename = os.path.splitext(os.path.basename(filename))[0] # drop the directory structure
    tier1_dir = os.path.abspath(os.path.split(filename)[0]) + "/../tier1"
    tier1_basename = "tier1_%s-ngm.root" % basename
    #print basename

    if os.path.isfile(os.path.join(tier1_dir,tier1_basename)):
        if verbose:
            print "--> %s already exists!!" % tier1_basename
        return 0
    
    shell_script_name = "script_%s.sh" % basename
    if os.path.isfile(shell_script_name):
        print "--> %s already exists!!" % shell_script_name
        return 0

    tier1_dir = os.path.abspath(os.path.split(filename)[0]) + "/../tier1"
    tier1_script_name = "%s.py" % os.path.splitext(inspect.getfile(toRoot))[0]

    cmd = ""
    cmd = '#!/bin/bash \n'
    cmd += 'echo starting tier1... \n'
    cmd += 'source ~/.bash_profile \n' # works for Alexis
    cmd += 'printenv \n'

    #tier1_dir = os.path.abspath(os.path.split(filename)[0]) + "/../tier1"
    cmd += 'mkdir -p %s \n' % tier1_dir
    cmd += 'umask 002 \n' # add write permissions for group
    cmd += 'cd %s \n' % tier1_dir
    cmd += 'time python %s %s  > log_%s.out 2>&1 \n' % (
        tier1_script_name,
        filename,
        basename,
    )
    cmd += 'chmod 664 %s \n\n' % tier1_basename # add write permissions for group to root file

    #-------------------------------------------------------------------------------
    # tier 3
    #-------------------------------------------------------------------------------

    cmd += 'echo starting tier3... \n'
    script_name = "%s.py" % os.path.splitext(inspect.getfile(generateTier3Files))[0]
    tier3_dir = os.path.abspath(os.path.split(filename)[0]) + "/../tier3"
    cmd += 'mkdir -p %s \n' % tier3_dir
    cmd += 'cd %s \n' % tier3_dir
    cmd += 'umask 002 \n' # add write permissions for group
    cmd += 'time python %s %s > %s 2>&1 \n\n' % (
        script_name,
        "%s/%s" % (tier1_dir, tier1_basename),
        "log_tier3_%s.out" % basename,
    )

    #print cmd
    #return 1 # debugging

    # write an executable script
    #shell_script_name = "script_%s.sh" % basename
    script = open(shell_script_name, 'w')
    script.write(cmd)
    script.close()

    #return # debugging


    #-------------------------------------------------------------------------------
    # job submission
    #-------------------------------------------------------------------------------

    if do_batch: # run in batch queue:
        #print "making batch command"

        cmd = """msub \\
              -A nuphys \\
              -m abe \\
              -V \\
              -N %(base)s \\
              -o out_%(base)s.out \\
              -j oe \\
              -q %(queue)s \\
              -l walltime=%(hours)02i:%(minutes)02i:00 \\
              -l ttc=1 \\
              '%(shell_script_name)s'
            """ % {
                  "queue": queue,
                  "hours": hours,
                  "minutes": minutes,
                  "base": basename,
                  "filename": filename,
                  "shell_script_name": shell_script_name,
                }

        #print "done"

    else:
        print "making other command..."
        # run the script from the command line
        cmd = "chmod +x %s " % shell_script_name
        cmd += "./%s \n" % (shell_script_name, )
        print "done"

    #return 1 # debugging

    print cmd

    # I don't really understand this, but can't use command.getstatusoutput here:
    #This submists??
    write_handle = os.popen(cmd, 'w')
    write_handle.close()
    return 1


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [NGM .bin files]"
        sys.exit(1)

    filenames = sys.argv[1:]
    print "Files", len(filenames)

    # check whether this user already has any jobs in the queue
    cmd = "showq | grep %s | wc -l" % os.getlogin()
    output = commands.getstatusoutput(cmd)
    n_jobs = int(output[1])
    # if there are jobs in the queue, don't submit any more
    if n_jobs > 0:
        print "==> %i jobs in the queue. No more jobs will be submitted" % n_jobs
        #sys.exit()


    verbose = True 
    job_lim = 500

    n_submitted = 0
    for filename in filenames:
        n_submitted += process_file(filename,verbose)
        if n_submitted >= job_lim:
            print "%i files submitted... stopping for now" % n_submitted
            break
    print "===> %i jobs submitted" % n_submitted


