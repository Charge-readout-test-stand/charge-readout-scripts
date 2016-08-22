
import sys
import commands

n_to_add = 50

filenames = sys.argv[1:]
n_files = len(filenames)
print "adding %i of %i files" % (len(filenames[:n_to_add]), n_files)

cmd = "time hadd -f added_tier3_%i.root %s" % (n_to_add, " ".join(filenames[:n_to_add]))
print cmd
output = commands.getstatusoutput(cmd)
print output[1]

