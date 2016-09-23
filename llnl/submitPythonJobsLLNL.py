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
    hours = 0
    minutes = 30


    #print "\n".join(filenames)
    #filenames.sort()
    #print "\n".join(filenames)
    #sys.exit()

    if verbose:
        print 'python_script:', python_script


    # per 

    print "===> submitting up to 200 of %i files" % len(filenames)


    for filename in filenames[:200]:

        if verbose:
            print "--> processing:", filename

        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        #print basename

# sample LLNL command (from nEXO MC)
#msub -A afqn -m abe -V -N mc$j -o $OUT_DIR/log/blog_$DIFF.job${j} -j oe -q pbatch -l walltime=12:00:00 $OUT_DIR/jobs_hold/doall${j}.script

# https://computing.llnl.gov/tutorials/linux_clusters/


        batch_script_name = "script_%s.sh" % basename
        batch_script = open(batch_script_name,'w')
        batch_script.write("#!/bin/bash \n")
        batch_script.write('source ~/.bash_profile \n') # works for Alexis
        batch_script.write('printenv \n')
        batch_script.write('time python %(python_script)s %(options)s %(filename)s \n' % {
          "python_script": python_script,
          "options": options,
          "filename": filename,
        })
        batch_script.close()

        print "batch_script_name:", batch_script_name

        script = """
    msub \\
      -A afqn \\
      -m abe \\
      -V \\
      -N %(base)s \\
      -o out_%(base)s.out \\
      -j oe \\
      -q %(queue)s \\
      -l walltime=%(hours)02i:%(minutes)02i:00 \\
      -l ttc=1 \\
      '%(batch_script_name)s'
    """ % {
          "queue": queue,
          "hours": hours,
          "minutes": minutes,
          "base": basename,
          "python_script": python_script,
          "filename": filename,
          "batch_script_name":batch_script_name,
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


