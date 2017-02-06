"""
A new script, trying to process existing files in a loop that keeps 200 jobs
running at once. 

This script builds a list of the tier1 root files and processes each one once.
This is suitale for reprocessing, when all of the tier1 files are already at
LLNL. If tier1 is still transferring, use submit_new_tier3_LLNL.py.  

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
    script_name = "%s.py" % os.path.splitext(inspect.getfile(generateTier3Files))[0]
    filenames.sort()

    while True:
        print "---> loop %i: %i tier1 files to consider" % (i_loop, len(filenames))
        if len(filenames) == 0: 
            print "Done!"
            sys.exit()

        # check whether this user already has any jobs in the queue
        cmd = "showq | grep %s | wc -l" % os.getlogin()
        output = commands.getstatusoutput(cmd)
        n_jobs = int(output[1])
        if n_jobs > 0:
            print "\t ==> %i jobs already in the queue." % n_jobs

        n_submitted = 0
        n_total_filenames = len(filenames)

        for i in xrange(len(filenames)):

            # limit jobs in queue to follow good neighbor policy
            if n_submitted + n_jobs >= 200:
                print "\t%i files already submitted.. stopping for now" % n_submitted
                break

            filename = filenames[0]
            print "--> processing file %i of %i: %s" % (i, n_total_filenames, filename)

            basename = os.path.basename(filename) # drop the directory structure
            basename = "_".join(basename.split("_")[1:])  # drop the tier1_
            tier3_name = "tier3_%s" % basename

            # if tier3 file exists, skip it, otherwise create it:
            if os.path.isfile(tier3_name):
                print "\t==> skipping %s" % tier3_name
                popped_filename = filenames.pop(0)
                #print "\t\tpopped_filename:", os.path.basename(popped_filename)
                #print "\t\tfilename:", os.path.basename(filename)
                continue

            else:
                n_submitted += 1
                filename = os.path.abspath(filename)
                log_name = "log_%s.out" % os.path.splitext(tier3_name)[0]
                print "\tprocessing job %i" % n_submitted
                submitPythonJobsLLNL.main(
                    python_script=script_name,
                    filenames=[filename],
                )
                popped_filename = filenames.pop(0)
                #print "\tpopped_filename:", os.path.basename(popped_filename)
                #print "\tfilename:", os.path.basename(filename)
                if os.path.basename(popped_filename) != os.path.basename(filename):
                    print "popped_filename != filename"
                    sys.exit(1)

            #sys.exit(1) # debugging

        print "\t====> %i jobs submitted" % n_submitted
        if n_submitted == 0: break
        i_loop += 1

        sleep_time = 60 # seconds
        print "\tsleeping for %i seconds... \n\n" % sleep_time
        time.sleep(sleep_time)
            

if __name__ == "__main__":

    process_files(sys.argv[1:])

