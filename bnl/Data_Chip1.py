# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 11:50:17 2017

@author: vlsilab2
"""

import os
import struct
import matplotlib.pyplot as plt
import glob
import re
import sys
from user_settings import user_editable_settings
settings = user_editable_settings()


class Data_Analysis:
    
    def Seperate_Packets(self, path, startfile, nfiles):

        #path=sys.argv[1]
	#startfile = int(argv[2])
	#nfiles = int(argv[3])

        self.screendisplay = sys.stdout
        sys.stdout = open(path + self.debug_file_name, "a+")

        
        #search_path = [path + "*Chip0_Packet*.dat", path + "*Chip1_Packet*.dat", 
        #               path + "*Chip2_Packet*.dat", path + "*Chip3_Packet*.dat"]

        #search_path = [path + "*Chip3_Packet*.dat"] 
 
        search_path = []
	for i in range(int(startfile),int(startfile+4*nfiles),4):
            search_path.append("{}Chip1_Packet{}.dat".format(path,i))

        new_path = path + "/Separated_Packets/"

        #print "new path is : ", new_path

        try: 
            os.makedirs(new_path)
        except OSError:
            if os.path.exists(new_path):
                pass
        '''    
        for the_file in os.listdir(new_path):
            file_path = os.path.join(new_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
        '''

        print ("Separating packets in " + path + " for " + str(settings.chip_num) + " chips assuming that there's " +\
               str(settings.packets_per_file) + " packets to a file.  The new separated packets will be in " + new_path)
        
        numbers = re.compile(r'(\d+)')
        def numericalSort(value):
            parts = numbers.split(value)
            parts[1::2] = map(int, parts[1::2])
            return parts
        
        for i in range(1,2):
            packet_counter = 0
            #relevant_files = sorted(glob.glob(search_path), key=numericalSort)
            #for infile in relevant_files:
            for fileid, infile in enumerate(search_path):
		if(os.path.isfile(infile)==0):
		    continue
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
                    packet_number_int = struct.unpack_from(">1I",packet_number_bytes)

                    
                    filename = new_path + "Chip{}_Packet{}.dat".format(i,packet_number_int[0])
                    with open(filename,"wb") as f:
                        f.write(data_fraction) 
                        f.close()
                        
                packet_counter += 1
                if (packet_counter%self.notice1_every == 0):
                    sys.stdout.close()
                    sys.stdout = self.screendisplay
		    #print ("Chip {}: {}/{} packet bundles separated".format(i, packet_counter, len(relevant_files)))
                    print ("Chip {}: {}/{} packet bundles separated".format(i, packet_counter, len(search_path)))
                    self.screendisplay = sys.stdout
                    sys.stdout = open(path + self.debug_file_name, "a+")
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Chip {} packet bundles fully separated".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")
        #Data_Analysis.Missing_Packet_Check(self, new_path, 1)
        sys.stdout.close()
        sys.stdout = self.screendisplay
    
        return new_path
    
    def Missing_Packet_Check(self, path, packets_per_file):
        
        #search_path = [path + "*Chip0_Packet*.dat", path + "*Chip1_Packet*.dat", 
        #               path + "*Chip2_Packet*.dat", path + "*Chip3_Packet*.dat"]
        
        search_path = [path + "*Chip3_Packet*.dat"] 

        #chip_specific_files = [[],[],[],[]]
        chip_specific_files = []
        
        numbers = re.compile(r'(\d+)')
        def numericalSort(value):
            parts = numbers.split(value)
            parts[1::2] = map(int, parts[1::2])
            return parts
        
        #for i in range(settings.chip_num):
        for i in range(0,1):
            for infile in sorted(glob.glob(search_path[0]), key=numericalSort):
                chip_specific_files.append(infile)
            packets = (len(chip_specific_files))
            packet_num_array = []
            count = 0
            for j in range(packets):
                filename = chip_specific_files[j]
                with open(filename, 'rb') as f:
                    raw_data = f.read(12)
                    f.close()
                packet_num_array.append(struct.unpack_from(">3I",raw_data)[2])
                count += 1
                if (count%self.notice2_every ==0):
                    sys.stdout.close()
                    sys.stdout = self.screendisplay
                    print ("Chip {}: {}/{} packets collected".format(i, count, packets))
                    self.screendisplay = sys.stdout
                    sys.stdout = open(path + self.debug_file_name, "a+")

            skips = 0
            
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Analyzing Chip {}".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")
            
            for k in range(len(packet_num_array) - 1):
                first_number = packet_num_array[k]
                second_number = packet_num_array[k+1]
                if (second_number != first_number + packets_per_file):
                    print ("Chip {} skips from packet {} to packet {}, index {} to {}"
                           .format(i, first_number, second_number, k, k+1))
                    skips += 1
            if (skips == 0):
                print ("No packet skips for Chip {}!".format(i))
            else:
                print ("Chip {} had {} packet skips".format(i, skips))
                
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Chip {} analyzed".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")

    def UnpackData(self, path = "default", data = None, return_data = False):

        if (path == "default"):
            fileinfo  = os.stat(data)
            filelength = fileinfo.st_size
        else:
            filelength = len(data)
        
        if (path == "default"):
            with open(data, 'rb') as f:
                raw_data = f.read(filelength)
                f.close()
            FACE_check = struct.unpack_from(">%dH"%(self.BPS + 8),raw_data)
        elif (path == "bytes"):
            FACE_check = struct.unpack_from(">%dH"%(self.BPS + 8),data)
            
        elif (path == "data"):
            FACE_check = data[:(self.BPS + 8)]
            
        else:
            print ("UnpackData--> Error: Specify which kind of unpacking you want to do")

        
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
        
        #print ("FACE detected at " + str(face_index))
        
        
        if (path == "default"):
            shorts = filelength/2
            full_data = struct.unpack_from(">%dH"%shorts,raw_data)
        elif (path == "bytes"):
            shorts = filelength/2
            full_data = struct.unpack_from(">%dH"%shorts,data)
        else:
            full_data = data

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
        
        if (return_data == True):
            return chip
        
        #print (chip)
        
        if (len(ch7) == len(ch8)):
            all_equal = True
        else:
            all_equal = False
            
        if (all_equal == True):
            length = len(ch7)
            
        time = []
        
        for i in range(length):
            time.append(0.5 * i)
            
        fig = plt.figure(figsize=(16, 12), dpi=80)
        overlay_ax = fig.add_subplot(1,1,1)
        overlay_ax.spines['top'].set_color('none')
        overlay_ax.spines['bottom'].set_color('none')
        overlay_ax.spines['left'].set_color('none')
        overlay_ax.spines['right'].set_color('none')
        overlay_ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        overlay_ax.set_xlabel('Time (us)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.yaxis.set_label_coords(-0.035,0.5)
        
        ax1 = fig.add_subplot(16,1,16)
        plt.plot(time, ch0)
        plt.setp(ax1.get_xticklabels(), fontsize=12)
        ax1.set_title("Channel 0")
        ax2 = ax1.twinx()
        ax2.set_ylabel("Channel 0", rotation = 0)
        ax2.spines['top'].set_color('none')
        ax2.spines['bottom'].set_color('none')
        ax2.spines['left'].set_color('none')
        ax2.spines['right'].set_color('none')
        ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')

        

        for i in range(15):
        
            ax = fig.add_subplot(16,1,15-i, sharex=ax1)
            plt.plot(time, chip[i+1])
            plt.setp(ax.get_xticklabels(), visible=False)
            ax2 = ax.twinx()
            ax2.set_ylabel("Channel " + str(i+1), rotation = 0)
#            ax2.spines['top'].set_color('none')
#            ax2.spines['bottom'].set_color('none')
#            ax2.spines['left'].set_color('none')
#            ax2.spines['right'].set_color('none')
            ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            pos1 = ax2.get_position() # get the original position 
            pos2 = [pos1.x0 + 0.025, pos1.y0 + 0.005,  pos1.width , pos1.height ] 
            ax2.set_position(pos2) # set a new position

        plt.subplots_adjust(wspace=0, hspace=0, top = 1, bottom = 0.05, right = 0.95, left = 0.05)
        return fig
    def quickPlot(self, data):
        
        time = []
        for i in range(len(data)):
            time.append(0.5 * i)
            
            
        fig = plt.figure(figsize=(16, 12), dpi=80)
        overlay_ax = fig.add_subplot(1,1,1)

        overlay_ax.set_xlabel('Time (us)')
        overlay_ax.set_ylabel('ADC Counts')
        plt.plot(time, data)
                
        #plt.show()
        
        return fig, overlay_ax
        
        
#__INIT__#
    def __init__(self):
        self.BPS = 13 #Bytes per sample.  The one for "0xFACE" and then 12 bytes for 16 channels at 12 bits each.
        self.channels = 16
        self.start_of_packet = (b"\xde\xad\xbe\xef")
        self.start_of_sample = (b"\xfa\xce")
        self.debug_file_name = "/Data_Analysis_Debug.txt"
        self.screendisplay = None
        self.notice1_every = 10000
        self.notice2_every = 50000
        
if __name__ == "__main__":
    for i in range(16):
        j = hex(i)[2]
    #    Data_Analysis().UnpackData(path = "default", 
    #             data = "D:\\nEXO\\2017_10_25\\Calibration_flange_warm\\04.7mV_0.5us_200mV\\cali_fpgadac\\fpgadac_{}.dat".format(j))
    #Data_Analysis().UnpackData("D:\\nEXO\\2017_06_19\\" + "ped.dat")
    #Data_Analysis().Missing_Packet_Check("D:\\Eric\\Packets\\")
    
    #path=
    startfile = int(sys.argv[2])
    nfiles = int(sys.argv[3])

    Data_Analysis().Seperate_Packets(path,startfile,nfiles)
