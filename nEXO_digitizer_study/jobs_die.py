"""
"canceljobs ALL" is not working on borax!
https://computing.llnl.gov/tutorials/moab/#Cancel

"""


import sys
import commands

job = 1179176


# find user name:
cmd = "whoami"
output = commands.getstatusoutput(cmd)
if output[0] == 0:
    user = output[1]
else:
    print output[1]
    sys.exit(1)
print "you are: ", user

cmd = "showq -u %s | grep %s" % (user, user)
#print cmd
output = commands.getstatusoutput(cmd)
n_jobs = len(output[1])
print "n jobs: ", n_jobs
if n_jobs == 0:
    print "no jobs"
    sys.exit()

for i, line in enumerate(output[1].split('\n')):
    print "--->", i, line
    job = int(line.split()[0])
    print "job:", job
    cmd = "canceljob %i" % (job)
    print "cmd:", cmd
    output = commands.getstatusoutput(cmd)
    print output[1]
