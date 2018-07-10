import os,sys,glob
import numpy as np
import struct
import matplotlib.pyplot as plt
#import Data_Chip1

BPS=13

#data_directory = "/p/lscratchd/wu41/teststand_data/14thLXe/2018_04_18/"
data_directory = "/p/lscratchd/wu41/teststand_data/14thLXe/2018_04_18/Separated_Packets/"
#data_directory =  '/p/lscratchd/jewell6/14thLXe_BNL/set0'
#data_directory  = '/g/g19/jewell6/software/charge-readout-scripts/bnl/'


if not os.path.isdir(data_directory):
    print "Bad Dir", data_directory
    sys.exit()
else:
    print "Good Dir", data_directory

files = glob.iglob(os.path.join(data_directory, "Chip1*dat"))

for fname in files:
    files = []
    for chip in xrange(4):
        if chip!=1: continue
        files.append(fname.replace("Chip1", "Chip%i"%chip))
    
    got_all = True
    
    for file1 in files:
        if os.path.isfile(file1):
            print "GOOD", file1
        else:
            print "Bad", file1
            got_all = False
    
    if not got_all: continue


    #Now loop over the 4 chips for this packet
    for fname in files:
        fileinfo   = os.stat(fname)
        filelength = fileinfo.st_size

        with open(fname, 'rb') as f:
            raw_data = f.read(filelength)
            f.close()
        FACE_check = struct.unpack_from(">%dH"%(BPS + 8),raw_data)
        
        print "FACE_check", FACE_check
        print 'filelength', filelength
        print len(raw_data)

        face_index = -1
        
        for i in range (BPS):
            if (FACE_check[i] == 0xFACE):
                face_index = i
                break

        if (face_index == -1):
            print ("FACE not detected")
            print_tuple = []
            for i in range(len(FACE_check)):
                print_tuple.append(hex(FACE_check[i]))

            print (print_tuple)
            raw_input("FACE ISSUE")
            #sys.exit()
        
        shorts = filelength/2
        full_data = struct.unpack_from(">%dH"%shorts,raw_data)
        full_data = full_data[face_index:]
        test_length = len(full_data[face_index:])
        full_samples = test_length // BPS

        wf_list = []

        print "Number of Full samples", full_samples
        
        ch0 = []
        ch1 = []
        ch2 = []
        ch3 = []
        ch4 = []
        ch5 = []
        ch6 = []
        ch7 = []
        ch8 = []
        ch9 = []
        ch10 = []
        ch11 = []
        ch12 = []
        ch13 = []
        ch14 = []
        ch15 = []

        #Correct for the baseline right away
        for i in range (full_samples):
            ch7.append((full_data[(BPS*i)+1] & 0x0FFF))
            ch6.append((((full_data[(BPS*i)+2] & 0x00FF) << 4) + ((full_data[(BPS*i)+1] & 0xF000) >> 12)))
            ch5.append((((full_data[(BPS*i)+3] & 0x000F) << 8) + ((full_data[(BPS*i)+2] & 0xFF00) >> 8)))
            ch4.append((((full_data[(BPS*i)+3] & 0xFFF0) >> 4)))
            ch3.append((full_data[(BPS*i)+4] & 0x0FFF) )
            ch2.append((((full_data[(BPS*i)+5] & 0x00FF) << 4) + ((full_data[(BPS*i)+4] & 0xF000) >> 12)))
            ch1.append((((full_data[(BPS*i)+6] & 0x000F) << 8) + ((full_data[(BPS*i)+5] & 0xFF00) >> 8)))
            ch0.append((((full_data[(BPS*i)+6] & 0xFFF0) >> 4)))
            ch15.append((full_data[(BPS*i)+7] & 0x0FFF))
            ch14.append((((full_data[(BPS*i)+8] & 0x00FF) << 4) + ((full_data[(BPS*i)+7] & 0xF000) >> 12)))
            ch13.append((((full_data[(BPS*i)+9] & 0x000F) << 8) + ((full_data[(BPS*i)+8] & 0xFF00) >> 8)))
            ch12.append((((full_data[(BPS*i)+9] & 0xFFF0) >> 4)))
            ch11.append((full_data[(BPS*i)+10] & 0x0FFF))
            ch10.append((((full_data[(BPS*i)+11] & 0x00FF) << 4) + ((full_data[(BPS*i)+10] & 0xF000) >> 12)))
            ch9.append((((full_data[(BPS*i)+12] & 0x000F) << 8) + ((full_data[(BPS*i)+11] & 0xFF00) >> 8)))
            ch8.append((((full_data[(BPS*i)+12] & 0xFFF0) >> 4)))

        plt.ion()
        plt.plot(ch10)
        plt.plot(ch0)
        plt.show()
        raw_input("PAUSE")
        plt.clf()
