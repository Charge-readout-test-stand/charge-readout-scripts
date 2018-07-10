import os,sys,glob
import numpy as np
import struct
import matplotlib.pyplot as plt
import Data_Analysis
from user_settings import user_editable_settings
settings = user_editable_settings()


def Run(data_dir):
    
    if not os.path.isdir(data_dir):
        print "Bad Dir", data_dir
        sys.exit()
    
    file_list = glob.iglob(os.path.join(data_dir, "Chip0*dat"))
    
    for fname in file_list:
        
        event_data = {}
        for event in xrange(settings.packets_per_file): 
            event_data[event] = {}

        for chip in xrange(4):
            #print "******************Chip%i**********************" % chip

            chip_fname = fname.replace("Chip0","Chip%i"%chip)
            all_data = Data_Analysis.Data_Analysis().Seperate_Packets(chip_fname)
            

            for ei,data in enumerate(all_data):
                wf_list  =  Data_Analysis.Data_Analysis().UnpackData(data)
                
                for wi, wf in enumerate(wf_list):
                    channel = chip*16 + wi
                    if chip==2 or chip==1:
                        event_data[ei][channel] = np.array(wf)*0.0
                        #event_data[ei][channel] = np.array(wf)*1.0    
                    else:
                        event_data[ei][channel] = np.array(wf)
    

        plt.ion()
        for ed in event_data:
            found=0
            plt.figure(1, figsize=(10,10))

            wfimage = np.zeros((len(event_data[ed]), len(event_data[ed][0])))
            pmax=0
            for ch in event_data[ed]:
                
                #if (np.max(event_data[ed][ch])-np.mean(event_data[ed][ch][:20]))>1500:
                #    print np.max(event_data[ed][ch]), np.max(event_data[ed][ch])%64
                event_data[ed][ch] = event_data[ed][ch] - np.mean(event_data[ed][ch][:20])
                
                time_samps = np.arange(len(event_data[ed][ch]))*0.5

                #Peak finder
                #if np.max(event_data[ed][ch])/np.std(event_data[ed][ch][:20]) > 10: 
                if (np.max(event_data[ed][ch]) > 35 and np.max(event_data[ed][ch]) < 1500):
                    found=1
                    print "Found on Ch", ch
                    print np.max(event_data[ed][ch]), np.std(event_data[ed][ch][:20])
                    plt.subplot(212)
                    plt.plot(time_samps, event_data[ed][ch])
                    pmax = np.max((pmax, np.max(event_data[ed][ch])))

                wfimage[ch] = event_data[ed][ch]


            #plt.plot(np.arange(len(event_data[ed][ch])), np.array(event_data[ed][ch]) + ch*1000)
            plt.subplot(211)
            #plt.plot(time_samps, event_data[ed][ch]+30*(ch+1))
            plt.imshow(wfimage, interpolation='nearest', vmin=-10, vmax=pmax)   
            #plt.colorbar()    
            plt.ylabel("Ch #", fontsize=15)
            #plt.ylim(0,2000)
            plt.subplot(211)
            #plt.xlabel("Time [us]")
            plt.subplot(212)
            plt.xlabel("Time [us]", fontsize=15)
            plt.show()
            if found:  raw_input("PAUSE")
            plt.clf()


if __name__ == "__main__":
    
    #data_dir =  '/p/lscratchd/jewell6/14thLXe_BNL/set0'
    data_dir  = '/p/lscratchd/jewell6/14thLXe_BNL/parsed_data/set1/'

    Run(data_dir)
