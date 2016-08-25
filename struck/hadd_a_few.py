"""
Add n_to_add files using ROOT's hadd
This is for creating small groups of files; at least smaller groups than the
full overnight set. 
"""


import sys
import commands

n_to_add = 50

filenames = sys.argv[1:]
n_files = len(filenames)
n_added = len(filenames[:n_to_add])
print "adding %i of %i files" % (n_added, n_files)

cmd = "time hadd -f added_tier3_%i.root %s" % (n_added, " ".join(filenames[:n_to_add]))
print cmd
output = commands.getstatusoutput(cmd)
print output[1]

