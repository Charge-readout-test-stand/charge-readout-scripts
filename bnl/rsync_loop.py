import glob,os,sys
import pwd,grp
import numpy as np
import shutil

file_list = glob.glob("./file_list/file*txt")
data_dir = '/g/g19/jewell6/jewell6/14thLXe_BNL/parsed_data/'

#curr_dir = '/media/teststand/Elements/nEXO/2018_04_18/parsed_data/'
curr_dir = "/home/teststand/bnl_data_parsing/parsed_data/"

if not os.path.isdir(data_dir): os.makedirs(data_dir)
cmd_header = "rsync -avzh --progress -e 'ssh' teststand@171.64.56.173:"

output = open('log.txt', 'w')
output.write("Start \n")

#for i in xrange(len(file_list)):   
#for i in np.arange(42,80):
for i in np.arange(214, 237,1):
    new_dir = os.path.join(data_dir, "set%i" % i)
    if not os.path.isdir(new_dir): os.makedirs(new_dir)
    new_dir += "/"

    old_dir = os.path.join(curr_dir, "set%i" % i)
    old_dir += "/"
    
    cmd = cmd_header + "%s %s" % (old_dir, new_dir)
    print cmd   
    output.write(cmd+'\n')
    os.system(cmd) 
    print "Done ", i
    output.write("Done %i \n" %i)

output.close()

