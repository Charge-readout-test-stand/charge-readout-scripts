"""
This script calls submit_jobs.sh in a loop. 
"""


import os
import time
import commands
import datetime

def get_n_jobs_in_queue():
    
    # check whether this user already has any jobs in the queue
    cmd = "showq | grep %s | wc -l" % os.getlogin()
    output = commands.getstatusoutput(cmd)
    n_jobs = int(output[1])
    # if there are jobs in the queue, don't submit any more
    return n_jobs


# options:
start_job = 0
n_jobs_total = 1000 # 7k x 500 events gives similar stats to run 11B

n_jobs_in_queue = get_n_jobs_in_queue()

while start_job < n_jobs_total:

    while True:
        if n_jobs_in_queue >= 200: # good neighbor policy...
            print "--> %i jobs in queue at %s... sleeping" % (
                n_jobs_in_queue,
                datetime.datetime.now()
            )
            time.sleep(60)
            n_jobs_in_queue = get_n_jobs_in_queue()
        else:
            print "=====> %i jobs in queue" % n_jobs_in_queue
            break

    print "--> submitting job %i of %i" % (start_job, n_jobs_total)
    cmd = "./submit_jobs.sh %i" % start_job
    print cmd

    # do the submission:
    output = commands.getstatusoutput(cmd)
    print output[1]

    n_jobs_in_queue += 1
    start_job += 1

