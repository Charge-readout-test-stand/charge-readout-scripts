import os
import struct
import matplotlib.pyplot as plt
import glob
import re
import sys
import numpy as np
from user_settings import user_editable_settings
settings = user_editable_settings()

class Data_Analysis:
    
    def __init__(self):
        self.BPS = 13 #Bytes per sample.  The one for "0xFACE" and then 12 bytes for 16 channels at 12 bits each.
        self.channels = 16
        self.start_of_packet = (b"\xde\xad\xbe\xef")
        self.start_of_sample = (b"\xfa\xce")
        #self.debug_file_name = "/Data_Analysis_Debug.txt"
        #self.screendisplay = None
        #self.notice1_every = 10000
        #self.notice2_every = 50000


    def Seperate_Packets(self, infile):
        
        numbers = re.compile(r'(\d+)')
       
        def numericalSort(value):
            parts = numbers.split(value)
            parts[1::2] = map(int, parts[1::2])
            return parts

        all_data = []
            
        packet_counter = 0
        fileinfo  = os.stat(infile)
        filelength = fileinfo.st_size
        shorts = filelength/2
        each_packet = int(filelength / settings.packets_per_file)

        ideal_packet_indices = []
        for j in range(settings.packets_per_file):
            ideal_packet_indices.append(each_packet * j)

        with open(infile, 'rb') as f:
            raw_data = f.read(filelength)
            f.close()
            
        full_data = struct.unpack_from(">%dH"%shorts,raw_data)


        real_packet_indices = []
        for m in re.finditer(self.start_of_packet, raw_data):
            real_packet_indices.append(m.start())


        if (len(real_packet_indices) != settings.packets_per_file):
            print ("WARNING: Found {} different chips in {} instead of the expected {}.".format(
                real_packet_indices, infile, settings.packets_per_file))

        if ((len(full_data)%(settings.packets_per_file)) != 0):
            print ("WARNING: " + infile + " doesn't have a properly divisible file length")
            print ("Ideal incides are {}".format(ideal_packet_indices))
            print ("Read indices are {}".format(real_packet_indices))


        error = 0
        for j in range(len(real_packet_indices)):

            if ((ideal_packet_indices[j]) != (real_packet_indices[j])):
                print ("WARNING: The beginning of Packet {} in {} is not where it should be!".format(j,infile))
                print ("It should be at {} but for some reason it's at {}.".format(hex(ideal_packet_indices[j]),
                                            hex(real_packet_indices[j])))
                data_fraction_test = []
                for k in range(len(real_packet_indices)):
                    if (k < (len(real_packet_indices) - 1)):
                        data_fraction_test.append(raw_data[real_packet_indices[k]:real_packet_indices[k+1]])
                    else:
                        data_fraction_test.append(raw_data[real_packet_indices[k]:])
                test_packet_indices = []
                error = 1
                

        if (error == 1):
            for k in range(len(data_fraction_test)):
                for m in re.finditer(self.start_of_sample, data_fraction_test[k]):
                    test_packet_indices.append(m.start())
                print ("{} samples found for packet {} in {}".format(len(test_packet_indices), k, infile))
                test_packet_indices = []


        for j in range(len(real_packet_indices)):
            if (j < (len(real_packet_indices) - 1)):
                data_fraction = raw_data[real_packet_indices[j]:real_packet_indices[j+1]]
            else:
                data_fraction = raw_data[real_packet_indices[j]:]

            packet_number_bytes = data_fraction[8:12]
            packet_number_int   = struct.unpack_from(">1I",packet_number_bytes)
            all_data.append(data_fraction)

        return all_data
    
    def UnpackData(self, data):
        filelength = len(data)
        
        FACE_check = struct.unpack_from(">%dH"%(self.BPS + 8),data)
        #FACE_check = data[:(self.BPS + 8)]
        
        face_index = -1
        for i in range (self.BPS):
            if (FACE_check[i] == 0xFACE):
                face_index = i
                break

        if (face_index == -1):
            print ("FACE not detected")
            print_tuple = []
            for i in range(len(FACE_check)):
                print_tuple.append(hex(FACE_check[i]))

            print (print_tuple)
            return
        shorts = filelength/2
        full_data = struct.unpack_from(">%dH"%shorts,data)

        full_data = full_data[face_index:]
        test_length = len(full_data[face_index:])
        full_samples = test_length // self.BPS

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
        for i in range (full_samples):
            ch7.append(full_data[(self.BPS*i)+1] & 0x0FFF)
            ch6.append(((full_data[(self.BPS*i)+2] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+1] & 0xF000) >> 12))
            ch5.append(((full_data[(self.BPS*i)+3] & 0x000F) << 8) + ((full_data[(self.BPS*i)+2] & 0xFF00) >> 8))
            ch4.append(((full_data[(self.BPS*i)+3] & 0xFFF0) >> 4))
            ch3.append(full_data[(self.BPS*i)+4] & 0x0FFF)
            ch2.append(((full_data[(self.BPS*i)+5] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+4] & 0xF000) >> 12))
            ch1.append(((full_data[(self.BPS*i)+6] & 0x000F) << 8) + ((full_data[(self.BPS*i)+5] & 0xFF00) >> 8))
            ch0.append(((full_data[(self.BPS*i)+6] & 0xFFF0) >> 4))
            ch15.append(full_data[(self.BPS*i)+7] & 0x0FFF)
            ch14.append(((full_data[(self.BPS*i)+8] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+7] & 0xF000) >> 12))
            ch13.append(((full_data[(self.BPS*i)+9] & 0x000F) << 8) + ((full_data[(self.BPS*i)+8] & 0xFF00) >> 8))
            ch12.append(((full_data[(self.BPS*i)+9] & 0xFFF0) >> 4))
            ch11.append(full_data[(self.BPS*i)+10] & 0x0FFF)
            ch10.append(((full_data[(self.BPS*i)+11] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+10] & 0xF000) >> 12))
            ch9.append(((full_data[(self.BPS*i)+12] & 0x000F) << 8) + ((full_data[(self.BPS*i)+11] & 0xFF00) >> 8))
            ch8.append(((full_data[(self.BPS*i)+12] & 0xFFF0) >> 4))


        chip = [ch0,ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,ch9,ch10,ch11,ch12,ch13,ch14,ch15]
        
        for ci,cd in enumerate(chip):
            #print "---->channel",ci
            #if "Chip2" in : continue
            self.fixData(cd)
            chip[ci] = self.fixData(cd)

        return chip
    
    def fixData(self, data):
        #Make data look not shitty
        #Doesn't really work??
        data_old = np.array(data)
        for i in range(len(data)):
            datum = data[i]
            mod = datum % 64
            if ((mod == 0) or (mod == 1) or (mod == 2) or (mod == 63) or (mod == 62)):

                if(i == 0):
                    data[i] = data[i+1]
                elif (i > (len(data) -2)):
                    data[i] = data[i-1]
                else:
                    data[i] = (data[i-1] + data[i+1])/2
        
        #plt.ion()
        #plt.plot(data_old, color='g', label='old')
        #plt.plot(data, color='r', label='new')
        #plt.legend(loc='upper right')
        #if (np.max(data)-np.min(data)) > 1000: raw_input("PAUSE FIX")
        #plt.clf()
        return data


if __name__ == "__main__":
    all_data = Data_Analysis().Seperate_Packets("/p/lscratchd/jewell6/14thLXe_BNL/set0/Chip1_Packet1000.dat")

    for data in all_data:
        Data_Analysis().UnpackData(data)


