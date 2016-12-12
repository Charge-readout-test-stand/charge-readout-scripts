"""
A new script, trying to process existing files in a loop that keeps 200 jobs
running at once. 

12 Dec 2016 AGS
"""

import os
import sys
import time
import inspect
import commands

from struck import generateTier3Files
import submitPythonJobsLLNL


def process_files(filenames):

    i_loop = 0
    while True:
        print "---> loop %i: %i files to process" % (i_loop, len(filenames))

        # check whether this user already has any jobs in the queue
        cmd = "showq | grep %s | wc -l" % os.getlogin()
        output = commands.getstatusoutput(cmd)
        n_jobs = int(output[1])
        if n_jobs > 0:
            print "\t ==> %i jobs already in the queue." % n_jobs

        print "--> checking %i files" % len(filenames)
        n_submitted = 0
        script_name = "%s.py" % os.path.splitext(inspect.getfile(generateTier3Files))[0]

        for i, filename in enumerate(filenames):
            
            #print "--> processing file %i of %i: %s" % (i, len(filenames), filename)

            basename = os.path.basename(filename) # drop the directory structure
            basename = "_".join(basename.split("_")[1:])  # drop the tier1_
            tier3_name = "tier3_%s" % basename

            # if tier3 file exists, skip it, otherwise create it:
            if os.path.isfile(tier3_name):
                continue
                print "\t==> skipping %s" % tier3_name

            else:
                # limit jobs in queue to follow good neighbor policy
                if n_submitted + n_jobs >= 200:
                    print "\t%i files submitted.. stopping for now" % n_submitted
                    break

                n_submitted += 1
                filename = os.path.abspath(filename)
                log_name = "log_%s.out" % os.path.splitext(tier3_name)[0]
                print "\tprocessing job %i" % n_submitted
                submitPythonJobsLLNL.main(
                    python_script=script_name,
                    filenames=[filename],
                )
                popped_filename = filenames.pop(0)
                print popped_filename, filename
                if popped_filename != filename:
                    print "popped_filename != filename"
                    sys.exit(1)

        print "\t====> %i jobs submitted" % n_submitted
        i_loop += 1

        time.sleep(60)
            

if __name__ == "__main__":

    process_files(sys.argv[1:])

