"""
A new script to submit only up to 200 jobs at a time for processing at LLNL. 
29 Aug 2016 AGS
"""



import os
import sys
import inspect
import commands

from struck import toRoot
import submitPythonJobsLLNL


def process_files(filenames):

    script_name = "%s.py" % os.path.splitext(inspect.getfile(toRoot))[0]

    # check whether this user already has any jobs in the queue
    cmd = "showq | grep %s | wc -l" % os.getlogin()
    output = commands.getstatusoutput(cmd)
    n_jobs = int(output[1])
    # if there are jobs in the queue, don't submit any more
    if n_jobs > 0:
        print "==> %i jobs in the queue. No more jobs will be submitted" % n_jobs
        return


    print "--> checking %i files" % len(filenames)
    n_submitted = 0
    for i, filename in enumerate(filenames):
        
        print "--> processing file %i of %i: %s" % (i, len(filenames), filename)

        basename = os.path.splitext(os.path.basename(filename))[0] # drop the directory structure
        tier1_name = "tier1_%s.root" % basename

        # if tier1 file exists, skip it, otherwise create it:
        if os.path.isfile(tier1_name):
            print "==> skipping"

        else:
            # limit jobs in queue to follow good neighbor policy
            if n_submitted >= 200:
                print "%i files submitted.. stopping for now" % n_submitted
                break

            n_submitted += 1
            filename = os.path.abspath(filename)
            log_name = "log_%s.out" % os.path.splitext(tier1_name)[0]
            print "processing!"
            submitPythonJobsLLNL.main(
                python_script=script_name,
                filenames=[filename],
            )

    print "====> %i jobs submitted" % n_submitted
            

if __name__ == "__main__":

    process_files(sys.argv[1:])

