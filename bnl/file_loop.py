import os,sys,glob
import numpy as np

data_directory = "/p/lscratchd/wu41/teststand_data/14thLXe/2018_04_18/Separated_Packets/"

if not os.path.isdir(data_directory):
    print "Bad Dir", data_directory
    sys.exit()
else:
    print "Good Dir", data_directory

files = glob.iglob(os.path.join(data_directory, "Chip*dat"))
#os.chmod("test.dat", 0644)
#sys.exit()

i=0
for fname in files:
    print i, fname
    os.chmod(fname, 0644)
    i+=1


