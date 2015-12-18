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
import submitPythonJobsSLAC
import generateTier3Files_internal
import generateTier3Files_external


# options:
#directory = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_03_testing"
directory = os.getcwd()

do_tier1 = False
do_tier3_internal = True 
do_tier3_external = False




def submitTier1():

    print "tier1 generation jobs..."
    os.chdir("%s/tier1" % directory)
    #print os.getcwd()
    filenames = glob.glob("%s/tier0/*.dat" % directory)
    print "\t %i tier0 files" % len(filenames)
    n_files = submitNewTier1Jobs.main(filenames, verbose=False)
    print "\t %i jobs submitted" % n_files



def submitTier3_external():
    print "tier3 (from tier2)  generation jobs..."
    input_dir = "%s/tier1" % directory
    output_dir = "%s/tier3_external" % directory
    
    os.chdir(output_dir)
    #print os.getcwd()
    filenames = glob.glob("%s/*.root" % input_dir)
    print "\t %i input files" % len(filenames)
    n_files = 0
    script_name = os.path.splitext(inspect.getfile(generateTier3Files_external))[0] + ".py"
    #print script_name

    for filename in filenames:
        #print filename
        outfile_name = generateTier3Files_external.create_outfile_name(filename)
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

   

def submitTier3_internal():
    print "tier3 (from tier1)  generation jobs..."
    input_dir = "%s/tier1" % directory
    output_dir = "%s/tier3_internal" % directory
    
    os.chdir(output_dir)
    #print os.getcwd()
    filenames = glob.glob("%s/*.root" % input_dir)
    print "\t %i input files" % len(filenames)
    n_files = 0
    script_name = os.path.splitext(inspect.getfile(generateTier3Files_internal))[0] + ".py"
    #print script_name

    for filename in filenames:
        #print filename
        outfile_name = generateTier3Files_internal.create_outfile_name(filename)
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

    if do_tier3_internal:
        submitTier3_internal()

    if do_tier3_external:
        submitTier3_external()

    
def main():
    process_files()

    
if __name__ == "__main__":

    main()
    #process_files()


