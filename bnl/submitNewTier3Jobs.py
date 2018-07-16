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

import generateTier3BNL

def SubmitJob(top_dir, dir_name):

    # options:
    queue = "pbatch" 
    #queue = "pshort" 
    hours = 4
    minutes = 0

    script_name = "%s.py" % os.path.splitext(inspect.getfile(generateTier3BNL))[0]
    shell_script_name = "script_%s.sh" % dir_name
    out_dir = os.path.join(top_dir, "../processed_data")
    print top_dir, out_dir 
    shell_script_name = os.path.join(out_dir, shell_script_name)

    cmd = ""
    cmd = '#!/bin/bash \n'
    cmd += 'source ~/.bash_profile \n' # works for Alexis
    cmd += 'printenv \n'

    cmd += 'echo starting tier3... \n'
    cmd += 'cd %s \n'       % out_dir
    cmd += 'umask 002 \n' # add write permissions for group
    cmd += 'time python %s %s %s > %s 2>&1 \n\n' % (
        script_name,
        "%s" % (os.path.join(top_dir, dir_name)),
        out_dir,
        "log_tier3_%s.out" % (dir_name),
    )

    # write an executable script
    script = open(shell_script_name, 'w')
    script.write(cmd)
    script.close()

    outfile = os.path.join(out_dir, "out_%s.out" % dir_name)

    cmd = """msub \\
          -A nuphys \\
          -m abe \\
            -V \\
          -N %(base)s \\
          -o %(outfile)s \\
          -j oe \\
          -q %(queue)s \\
          -l walltime=%(hours)02i:%(minutes)02i:00 \\
          -l ttc=1 \\
          '%(shell_script_name)s'
            """ % {
                  "queue": queue,
                  "hours": hours,
                  "minutes": minutes,
                  "base": dir_name,
                  "outfile":outfile,
                  "shell_script_name": shell_script_name,
                }

    print cmd

    # I don't really understand this, but can't use command.getstatusoutput here:
    #This submists
    write_handle = os.popen(cmd, 'w')
    write_handle.close()
    return 1


if __name__ == "__main__":

    #if len(sys.argv) < 2:
    #    print "arguments: [NGM .bin files]"
    #    sys.exit(1)
    #dir_name = sys.argv[1]
    
    dir_name = "/p/lscratchd/jewell6/14thLXe_BNL/parsed_data/"
    dir_list = os.listdir(dir_name)

    for dirname in dir_list:
        print dirname
        SubmitJob(dir_name, dirname)
        #sys.exit()

