import os,sys,glob
import numpy as np
import struct
import matplotlib.pyplot as plt
import Data_Analysis
from user_settings import user_editable_settings
settings = user_editable_settings()

def FindIntWindow(wf):
    peakAmp  = np.max(wf)
    peakTime = np.argmax(wf) 
    
    check_window = 5
    rms_limit    = 5

    tlow  = -1
    thigh = -1

    for shift in np.arange(0, peakTime):
        
        if (peakTime-check_window-shift) < 0: break
        if (peakTime+shift+check_window) > len(wf): break
        
        check_range_low = np.arange(peakTime-check_window-shift, peakTime-shift, 1)   
        check_range_high= np.arange(peakTime+shift, peakTime+shift+check_window, 1)

        #print np.mean(wf[check_range_low]), np.mean(wf[check_range_high])

        if np.mean(wf[check_range_low]) < rms_limit and tlow < 0: 
            tlow = check_range_low[0]
        
        if np.mean(wf[check_range_high]) < rms_limit and thigh < 0:
            thigh = check_range_high[-1]

    plt.figure(10)
    plt.clf()
    plt.plot(wf, color='b', linewidth=2)
    plt.axvline(tlow,  linewidth=2, color='r')
    plt.axvline(thigh, linewidth=2, color='r')

    plt.show()
    #raw_input()

def isChipGood(wf_list):
    
    plt.figure(12)
    plt.ion()
    plt.clf()
    
    events_over = np.zeros(len(wf_list))

    max_points=None
    for wi, wf in enumerate(wf_list):
        wf=np.array(wf)
        
        if wi==0: 
            max_points = (wf>1500)
            events_over[wi] = np.sum(max_points)
            #if np.sum(max_points)==0: break
        else:
            print "Check others", np.sum(wf[max_points]>1500)

            events_over[wi] = np.sum(wf[max_points]>1500)
        plt.plot(wf)

    plt.show()

    if np.sum(events_over) > 10: 
        return False
    else:
        #raw_input("CHIP1 CHECK PAUSE")
        return True

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
                
                scale = 1.0

                useChip1 = True
                if chip==1:
                    if not isChipGood(wf_list):
                        useChip1 = False
                        scale=0.0

                for wi, wf in enumerate(wf_list):
                    channel = chip*16 + wi
                    if chip==2 or chip==1:
                        #event_data[ei][channel] = np.array(wf)*0.0
                        event_data[ei][channel] = np.array(wf)*scale    
                    else:
                        event_data[ei][channel] = np.array(wf)
                
                print "Next Event"
    

        plt.ion()
        for ed in event_data:
            found=0
            plt.figure(1, figsize=(10,10))

            wfimage = np.zeros((len(event_data[ed]), len(event_data[ed][0])))
            pmax=0
            for ch in event_data[ed]:
                
                #if ch > 15 or ch < 47: continue
                bline = np.mean(event_data[ed][ch][:20])
                #if (np.max(event_data[ed][ch])-np.mean(event_data[ed][ch][:20]))>1500:
                #    print np.max(event_data[ed][ch]), np.max(event_data[ed][ch])%64
                event_data[ed][ch] = event_data[ed][ch] - np.mean(event_data[ed][ch][:20])
                
                time_samps = np.arange(len(event_data[ed][ch]))*0.5

                #Peak finder
                #if np.max(event_data[ed][ch])/np.std(event_data[ed][ch][:20]) > 10: 
                #if (np.max(event_data[ed][ch]) > 30) and not (ch > 15 and ch < 48):
                if (np.max(event_data[ed][ch]) > 30) and not (ch > 15+16 and ch < 48):
                #if (np.max(event_data[ed][ch]) > 30) and not (ch > 15 and ch < 15+16+1):
                    found=1
                    print "Found on Ch", ch
                    print np.max(event_data[ed][ch]), np.std(event_data[ed][ch][:20])
                    print bline
                    plt.subplot(212)
                    plt.plot(time_samps, event_data[ed][ch])
                    pmax = np.max((pmax, np.max(event_data[ed][ch])))
                    
                    FindIntWindow(event_data[ed][ch])
                    plt.figure(1)

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
            #if event_data[ed]['use1']: raw_input("CHIP1 GOOD PAUSE")
            plt.clf()


if __name__ == "__main__":
    
    #data_dir =  '/p/lscratchd/jewell6/14thLXe_BNL/set0'
    data_dir  = '/p/lscratchd/jewell6/14thLXe_BNL/parsed_data/set1/'

    Run(data_dir)
