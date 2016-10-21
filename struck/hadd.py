"""
Add all tier3 together to make 1 file

add files with hadd, then hadd -O to optimize branches. 

"""

import commands

basename = "overnight_9thLXe_v3.root"
no_opt_name = "no_opt_%s" % basename

# hadd, but don't reoptimize TTree branches:
cmd = "time hadd %s ../tier3/tier3*.root" % no_opt_name
output = commands.getstatusoutput(cmd)
print output[1]

# hadd again, this time reoptimize TTree branches
cmd = "time hadd -O %s %s" % (basename, no_opt_name)
output = commands.getstatusoutput(cmd)
print output[1]

# remove the no_opt version
cmd = "rm %s" % no_opt_name
output = commands.getstatusoutput(cmd)
print output[1]

