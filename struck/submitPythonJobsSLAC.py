#!/usr/bin/env python

"""
submit batch jobs at SLAC

arguments:
1: python script name 
2: filenames

if running as exodata, do this first:
source /afs/slac.stanford.edu/u/xo/alexis4/.cshrc

slac batch info:
https://www.slac.stanford.edu/exp/glast/wb/prod/pages/installingOfflineSW/usingSlacBatchFarm.htm

02 Apr 2014 AGS
"""

import os
import sys


def main(python_script, filenames, options="", verbose=True):

    # options:
    #queue = "long" # <= 2 hours
    queue = "xlong" # <= 16 hours
    hours = 15
    minutes = 00


    #print "\n".join(filenames)
    #filenames.sort()
    #print "\n".join(filenames)
    #sys.exit()

    if verbose:
        print 'python_script:', python_script


    for filename in filenames:

        if verbose:
            print "--> processing:", filename

        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        #print basename

        script = """
    bsub \\
      -R rhel60 \\
      -q %(queue)s \\
      -W %(hours)02i:%(minutes)02i \\
      -oo out_%(base)s.out \\
      -J %(base)s \\
       'printenv; python %(python_script)s %(options)s %(filename)s'
    """ % {
          "queue": queue,
          "hours": hours,
          "minutes": minutes,
          "base": basename,
          "python_script": python_script,
          "options": options,
          "filename": filename,
        }

        if verbose:
            print script

        write_handle = os.popen(script, 'w')
        write_handle.close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [python script] [filename(s)]"
        sys.exit(1)

    python_script = sys.argv[1]
    filenames = sys.argv[2:]

    main(python_script, filenames)


