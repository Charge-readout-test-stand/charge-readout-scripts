#!/bin/env python

"""
This script generates tier1, tier2, and tier3 files. 
"""

import os
import sys
import glob
import inspect
import commands
import datetime

import submitNewTier1Jobs
import submitNewTier2Jobs
import submitPythonJobsSLAC
import generateTier3Files


# options:
directory = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_02_testing"
do_tier1 = True
do_tier2 = False
do_tier3_from_tier1 = True
do_tier3_from_tier2 = True




def submitTier1():

    print "tier1 generation jobs..."
    os.chdir("%s/tier1" % directory)
    #print os.getcwd()
    filenames = glob.glob("%s/tier0/*.dat" % directory)
    print "\t %i tier0 files" % len(filenames)
    n_files = submitNewTier1Jobs.main(filenames, verbose=False)
    print "\t %i jobs submitted" % n_files


def submitTier2():
    # watch out! tier2 jobs take forever...
    print "tier2 generation jobs..."
    os.chdir("%s/tier2" % directory)
    #print os.getcwd()
    filenames = glob.glob("%s/tier1/*.root" % directory)
    print "\t %i tier1 files" % len(filenames)
    n_files = submitNewTier2Jobs.main(filenames, verbose=False)
    print "\t %i jobs submitted" % n_files

 
def submitTier3_from_tier2():
    print "tier3 (from tier2)  generation jobs..."
    input_dir = "%s/tier2" % directory
    output_dir = "%s/tier3_from_tier2" % directory
    submitTier3(input_dir=input_dir, output_dir=output_dir)

   

def submitTier3_from_tier1():
    print "tier3 (from tier1)  generation jobs..."
    input_dir = "%s/tier1" % directory
    output_dir = "%s/tier3_from_tier1" % directory
    submitTier3(input_dir=input_dir, output_dir=output_dir)


def submitTier3(input_dir, output_dir):
    os.chdir(output_dir)
    #print os.getcwd()
    filenames = glob.glob("%s/*.root" % input_dir)
    print "\t %i input files" % len(filenames)
    n_files = 0
    script_name = os.path.splitext(inspect.getfile(generateTier3Files))[0] + ".py"
    #print script_name

    for filename in filenames:
        #print filename
        outfile_name = generateTier3Files.create_outfile_name(filename)
        outfile_name = "%s/%s" % (os.getcwd(), outfile_name)
        #print outfile_name
        # don't overwrite existing files:
        if not os.path.isfile(outfile_name):
            submitPythonJobsSLAC.main(
                python_script=script_name,
                filenames=[filename], 
                verbose=False,
            )
            n_files += 1

    print "\t %i jobs submitted" % n_files


def are_jobs_pending():

    # if jobs are pending (not running yet), we don't want to submit them
    # again... 

    # crummy workaround -- looking at jobs for all users, then grepping for the
    # known user avoids trouble when the user is running 0 jobs. 
    user = os.environ["USER"]
    cmd = "bjobs -u all | grep %s | grep PEND | wc -l" % user
    output = commands.getstatusoutput(cmd)
    if int(output[1]) != 0:
        print "--> jobs are pending... wait until they start."
        return 1
    else:
        print "--> no pending jobs (good!)"
        return 0




def process_files():

    now = datetime.datetime.now()
    print "starting at %s" % now

    jobs_pending = are_jobs_pending()
    if jobs_pending:
        return

    if do_tier1:
        submitTier1()

    if do_tier2:
        val = raw_input("--> really submit tier2 jobs? (y/n): ")
        if val == 'y':
            submitTier2()

    if do_tier3_from_tier1:
        submitTier3_from_tier1()

    if do_tier3_from_tier2:
        submitTier3_from_tier2()

    
def main():
    process_files()

    
if __name__ == "__main__":

    main()
    #process_files()


