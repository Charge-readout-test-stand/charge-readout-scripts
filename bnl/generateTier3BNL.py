import os,glob,sys
import commands
import numpy as np
from array import array
import Data_Analysis

#Settings from Eric
from user_settings import user_editable_settings
settings = user_editable_settings()

import ROOT
ROOT.gROOT.SetBatch(True) # run in batch mode
import subprocess
from optparse import OptionParser
import matplotlib.pyplot as plt
import psutil

NEST_cal = 139 #keV/fc

def memory_usage_psutil():
    # return the memory usage in MB
    process = psutil.Process(os.getpid())
    mem = process.memory_info()[0] / float(2 ** 20)
    return mem, process.memory_percent()

def isChipGood(wf_list):
        
    events_over = np.zeros(len(wf_list))
    max_points=None

    for wi, wf in enumerate(wf_list):
        wf=np.array(wf)
        if wi==0:
            max_points = (wf>1500)
            events_over[wi] = np.sum(max_points)
        else:
            events_over[wi] = np.sum(wf[max_points]>1500)

    if np.sum(events_over) > 10: return False
    else:                        return True

def FindIntWindow(wf, peakTime):
    check_window = 5
    rms_limit    = 5
    
    tlow  = -1
    for shift in np.arange(0, peakTime):
        if (peakTime-check_window-shift) < 0: 
            tlow=0
            break
        check_range_low = np.arange(peakTime-check_window-shift, peakTime-shift, 1)
        
        if np.mean(wf[check_range_low]) < rms_limit and tlow < 0:
            tlow = check_range_low[0]
            break

    thigh = -1
    for shift in np.arange(0, len(wf)-peakTime):
        if (peakTime+shift+check_window) > len(wf): 
            thigh = len(wf)
            break
        check_range_high= np.arange(peakTime+shift, peakTime+shift+check_window, 1)
        
        if np.mean(wf[check_range_high]) < rms_limit and thigh < 0:
            thigh = check_range_high[-1]
            break

    if tlow<0:  tlow=0
    if thigh<0: thigh=len(wf)
    return [tlow, thigh]

def ProcessDir(input_dir, output_dir):


    out_filename = input_dir.split("/")[-1]
    set_num_hold = int(out_filename.replace('set', ''))
    out_filename = "tier3_%s.root" % out_filename
    out_filename = os.path.join(output_dir, out_filename)
    
    print "Outfile is", out_filename

    out_file = ROOT.TFile(out_filename, "recreate")
    gout = out_file.GetDirectory("")
    nchannels = settings.chip_num*settings.chs_per_chip
    
    out_tree = ROOT.TTree("tree", "%s processed wfm tree" % input_dir.split("/")[-2])
    
    ind_channels = array('I', [0]) # signed int
    out_tree.Branch('ind_channels', ind_channels, 'ind_channels/i')

    hit_channels = array('I', [0]) # signed int
    out_tree.Branch('hit_channels', hit_channels, 'hit_channels/i')

    hit_channelsX = array('I', [0]) # signed int
    out_tree.Branch('hit_channelsX', hit_channelsX, 'hit_channelsX/i')
    
    hit_channelsY = array('I', [0]) # signed int
    out_tree.Branch('hit_channelsY', hit_channelsY, 'hit_channelsY/i')

    hit_map = array('I', [0]*nchannels) # signed int
    out_tree.Branch('hit_map', hit_map, 'hit_map[%i]/i' % nchannels)
    
    ind_map = array('I', [0]*nchannels) # signed int
    out_tree.Branch('ind_map', ind_map, 'ind_map[%i]/i' % nchannels)

    channel = array('I', [0]*nchannels) # unsigned int
    out_tree.Branch('channel', channel, 'channel[%i]/i' % nchannels)

    goodChip1 =  array('I', [0]) # signed int
    out_tree.Branch('goodChip1', goodChip1, 'goodChip1/i')

    wfm_max_energy = array('d', [0])
    out_tree.Branch('wfm_max_energy', wfm_max_energy, 'wfm_max_energy/D')

    wfm_area_energy = array('d', [0])
    out_tree.Branch('wfm_area_energy', wfm_area_energy, 'wfm_area_energy/D')

    wfm_area = array('d', [0]*nchannels)
    out_tree.Branch('wfm_area', wfm_area, 'wfm_area[%i]/D' % nchannels)

    int_wind_low = array('I', [0]*nchannels) # unsigned int
    out_tree.Branch('int_wind_low', int_wind_low, 'int_wind_low[%i]/i' % nchannels)

    int_wind_high = array('I', [0]*nchannels) # unsigned int
    out_tree.Branch('int_wind_high', int_wind_high, 'int_wind_high[%i]/i' % nchannels)

    wfm_max =  array('d', [0]*nchannels)
    out_tree.Branch('wfm_max', wfm_max, 'wfm_max[%i]/D' % nchannels)
 
    wfm_min = array('d', [0]*nchannels)
    out_tree.Branch('wfm_min', wfm_min, 'wfm_min[%i]/D' % nchannels)

    wfm_max_time = array('d', [0]*nchannels)
    out_tree.Branch('wfm_max_time', wfm_max_time, 'wfm_max_time[%i]/D' % nchannels)

    wfm_min_time = array('d', [0]*nchannels)
    out_tree.Branch('wfm_min_time', wfm_min_time, 'wfm_min_time[%i]/D' % nchannels)

    wfm_baseline = array('d', [0]*nchannels)
    out_tree.Branch('wfm_baseline', wfm_baseline, 'wfm_baseline[%i]/D' % nchannels)
    
    wfm_baseline_full = array('d', [0]*nchannels)
    out_tree.Branch('wfm_baseline_full', wfm_baseline_full, 'wfm_baseline_full[%i]/D' % nchannels)

    wfm_rms = array('d', [0]*nchannels)
    out_tree.Branch('wfm_rms', wfm_rms, 'wfm_rms[%i]/D' % nchannels)

    wfm_rms_full = array('d', [0]*nchannels)
    out_tree.Branch('wfm_rms_full', wfm_rms_full, 'wfm_rms_full[%i]/D' % nchannels)

    eventNum = array('I', [0]) # signed int
    out_tree.Branch('eventNum', eventNum, 'eventNum/i')
    
    packetNum = array('I', [0]) # signed int
    out_tree.Branch('packetNum', packetNum, 'packetNum/i')

    segNum    = array('I', [0]) # signed int
    out_tree.Branch('segNum', segNum, 'segNum/i')

    setNum    = array('I', [0]) # signed int
    out_tree.Branch('settNum', setNum, 'setNum/i')
    setNum[0] = set_num_hold 

    file_list = glob.iglob(os.path.join(input_dir, "Chip0*dat"))
    nevents = 0
    
    #Loop over each file in the directory which each contain 4 events/packets from 1 Chip
    #total 4 chips (2 messed up)
    for fi, fname in enumerate(file_list):
        
        #Get packet number from file name
        packet_num = os.path.basename(fname).replace(".dat","")
        packet_num = int(packet_num.replace("Chip0_Packet",""))

        event_data = {}
        useChip1     = []
        for event in xrange(settings.packets_per_file): event_data[event+packet_num] = {}

        #Loop over chips 
        for chip in xrange(settings.chip_num):
            
            chip_fname = fname.replace("Chip0","Chip%i"%chip)
            all_data = Data_Analysis.Data_Analysis().Seperate_Packets(chip_fname)
            
            #Now loop over each event in the and extract the WFs
            for ei,data in enumerate(all_data):
                wf_list  =  Data_Analysis.Data_Analysis().UnpackData(data)
                event_num = packet_num + ei
                
                scale = 0.0
                if chip==1:
                    #Chip-1 is bad sometimes so check if all channels peaked at same time
                    if isChipGood(wf_list):
                        scale=1.0
                        useChip1.append(True)
                    else:
                        useChip1.append(False)

                for wi, wf in enumerate(wf_list):
                    wf_ch = chip*settings.chs_per_chip + wi       
                    if chip==2 or chip==1:
                        #These chips are bad for the moment
                        event_data[event_num][wf_ch] = np.array(wf)*scale
                    else:
                        event_data[event_num][wf_ch] = np.array(wf)
 

        for index, ei in enumerate(event_data):
            
            packetNum[0]       = ei       
            eventNum[0]        = nevents
            goodChip1[0]       = useChip1[index]
            segNum[0]          = index
        
            ind_channels[0]    = 0
            hit_channels[0]    = 0
            hit_channelsX[0]   = 0
            hit_channelsY[0]   = 0
            wfm_max_energy[0]  = 0
            wfm_area_energy[0] = 0

            for ch in event_data[ei]:
                wf = np.array(event_data[ei][ch])
                channel[ch] = ch

                wfm_max[ch]       = np.max(wf)
                wfm_min[ch]       = np.min(wf)
                wfm_max_time[ch]  = np.argmax(wf)*0.5
                wfm_min_time[ch]  = np.argmin(wf)*0.5
                wfm_baseline[ch]  = np.mean(wf[:20])
                old_baseline      = np.mean(wf[:20])
                #wfm_baseline[ch] = settings.baseline[ch]
                wfm_rms[ch]       = np.std(wf[:20])
                wfm_rms_full[ch]  = 0.0
                wfm_baseline_full[ch] = 0.0

                #Baseline subtract
                wf = wf - wfm_baseline[ch]  
                
                #Why does this happen?
                if False and wfm_rms[ch] == 0 and np.max(wf)>30:
                #if True and ch > 15 and ch < 32 and np.max(wf)>30:
                #if True and ch > 1 and ch < 16 and np.max(wf)>30:
                    plt.figure(9)
                    plt.ion()
                    plt.clf()
                    plt.title("Ch=%i, Max=%.3f"%(ch, np.max(wf)))
                    plt.plot(wf)
                    plt.plot(np.array(event_data[ei][ch-1]) - settings.baseline[ch-1])
                    plt.plot(np.array(event_data[ei][ch+1]) - settings.baseline[ch+1])
                    plt.show()
                    print "Channel is ", ch, wfm_rms[ch], np.max(wf)
                    raw_input("Why")

                #If above threshold than correct baseline if necceasry
                if np.max(wf) > 30:
                    int_window = FindIntWindow(wf, np.argmax(wf))
                    int_wind_high[ch] = int_window[1]
                    int_wind_low[ch]  = int_window[0]

                    #First check the baseline by finding integration window
                    use_for_base = np.ones_like(wf)
                    use_for_base[int_window[0]:int_window[1]] = 0
                    new_baseline     =  np.mean(wf[use_for_base>0])
                    wf = wf - new_baseline

                    #add in the adjusted baseline/rms
                    wfm_baseline_full[ch] = wfm_baseline[ch]+new_baseline
                    wfm_rms_full[ch]      = np.std(wf[use_for_base>0])

                skip=False
                if abs(wfm_baseline_full[ch] - settings.baseline[ch])>30 and ch==54:
                    #Occasionally ch 54 drops out
                    #easy to spot since the basline drops by ~40ADC
                    #continue
                    skip=True

                if abs(wfm_baseline_full[ch] - settings.baseline[ch])>1000:
                    #Crazy shift probably weird noise
                    #continue
                    skip=True
            
                #If still above threshold continue
                if np.max(wf) > 30 and not skip:
                    int_window = FindIntWindow(wf, np.argmax(wf))
                    int_wind_high[ch] = int_window[1]
                    int_wind_low[ch]  = int_window[0]

                    use_for_base = np.ones_like(wf)
                    use_for_base[int_window[0]:int_window[1]] = 0
                    new_baseline     = np.sum(use_for_base*wf)/np.sum(use_for_base)

                    hit_channels[0] +=1
                    hit_map[ch] = 1

                    if ch < 32: hit_channelsX[0] +=1
                    else:       hit_channelsY[0] +=1

                    #wfm_area[ch] = np.trapz(wf[int_window[0]:int_window[1]])
                    wfm_area[ch]    = np.sum(wf[int_window[0]:int_window[1]])
                    wfm_area[ch]   *= (NEST_cal/settings.int_gain[ch])

                    wfm_area_energy[0] += wfm_area[ch]
                    wfm_max_energy[0]  += (wfm_max[ch]-wfm_baseline_full[ch])*(NEST_cal/settings.amp_gain[ch])

                    #if True and abs(wfm_area_energy[0] - wfm_max_energy[0]) > 100:
                    if False:
                    #if True and (int_window[1]-int_window[0]) > 30:
                    #if True and abs(wfm_baseline[ch] - settings.baseline[ch])>30:
                        plt.ion()
                        plt.figure(1)
                        plt.clf()
                        print ch, wfm_baseline_full[ch], new_baseline, settings.baseline[ch]
                        print (settings.baseline[ch]-wfm_baseline_full[ch])
                        print "here, file", wfm_rms[ch], settings.rms[ch]    
                        print "Max vs Area", wfm_area_energy[0], wfm_max_energy[0]
            
                        plt.title("Ch=%i, W=%i, BL=%.2f" % (ch, int_window[1]-int_window[0], new_baseline))
                        plt.axvline(int_window[0], c='r', linewidth=3)
                        plt.axvline(int_window[1], c='r', linewidth=3)
                        plt.axhline(new_baseline, c='m', linewidth=3)
        
                        plt.plot(wf)
                        raw_input("PAUSE")

                else:
                    wfm_area[ch] = 0.0
                    hit_map[ch]  = 0
                    int_wind_high[ch] = 0
                    int_wind_low[ch]  = 0

                if np.min(wf) < -30 and not skip:
                    ind_map[ch] = 1
                    ind_channels[0] += 1
                    if False:
                        plt.ion()
                        plt.figure(1)
                        plt.clf()
                    
                    
                        if ch+1 < 16*4: plt.plot(event_data[ei][ch+1]-settings.baseline[ch+1], label='%i'%(ch+1))
                        if ch+2 < 16*4: plt.plot(event_data[ei][ch+2]-settings.baseline[ch+2], label='%i'%(ch+2))
                        plt.plot(wf,label='%i'%ch)
                        if ch-1 >= 0: plt.plot(event_data[ei][ch-1]-settings.baseline[ch-1],   label='%i'%(ch-1))
                        if ch-2 >= 0: plt.plot(event_data[ei][ch-2]-settings.baseline[ch-2],   label='%i'%(ch-2))

                        plt.legend()
                        raw_input("MIN PAUSE")

                else:
                    ind_map[ch] = 0

            if False  and np.sum(hit_map) > 0.5 and np.sum((np.array(wfm_min)-np.array(wfm_baseline_full))<-30):
                print np.array(channel)[np.array(hit_map)>0.5]
                print np.array(channel)[(np.array(wfm_min)-np.array(wfm_baseline_full))<-30]
                raw_input()

            out_tree.Fill()
            nevents += 1
            if nevents%1000 == 0:
                print nevents, memory_usage_psutil()

        if nevents > 2000: break
    
    gout.cd("")
    out_tree.Write()
    #out_tree.Close()

if __name__ == "__main__":
    
    parser = OptionParser()
    (options, input_dir) = parser.parse_args()   
    ProcessDir(input_dir[0], output_dir=input_dir[1])


