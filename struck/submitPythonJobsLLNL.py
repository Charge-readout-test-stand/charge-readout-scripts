#!/usr/bin/env python

"""
submit batch jobs at LLNL

arguments:
1: python script name 
2: filenames



# sample LLNL command (from nEXO MC)
msub -A afqn -m abe -V -N mc$j -o $OUT_DIR/log/blog_$DIFF.job${j} -j oe -q pbatch -l walltime=12:00:00 $OUT_DIR/jobs_hold/doall${j}.script

"""

import os
import sys


def main(python_script, filenames, options="", verbose=True):

    # options:
    queue = "pbatch" 
    hours = 2
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

# sample LLNL command (from nEXO MC)
#msub -A afqn -m abe -V -N mc$j -o $OUT_DIR/log/blog_$DIFF.job${j} -j oe -q pbatch -l walltime=12:00:00 $OUT_DIR/jobs_hold/doall${j}.script

        script = """
    bmsub \\
      -A afqn \\
      -m abe \\
      -V \\
      -q %(queue)s \\
      -walltime %(hours)02i:%(minutes)02i \\
      -oo out_%(base)s.out \\
      -j oe \\
      -N %(base)s \\
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


