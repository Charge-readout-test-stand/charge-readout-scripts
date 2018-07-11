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

def memory_usage_psutil():
    # return the memory usage in MB
    process = psutil.Process(os.getpid())
    mem = process.memory_info()[0] / float(2 ** 20)
    return mem, process.memory_percent()

def ProcessDir(input_dir, output_dir):


    out_filename = input_dir.split("/")[-1]
    out_filename = "tier3_%s.root" % out_filename
    out_filename = os.path.join(output_dir, out_filename)
    
    print "Outfile is", out_filename

    out_file = ROOT.TFile(out_filename, "recreate")
    gout = out_file.GetDirectory("")
    nchannels = settings.chip_num*settings.chs_per_chip
    
    out_tree = ROOT.TTree("tree", "%s processed wfm tree" % input_dir.split("/")[-2])
    
    hit_channels = array('I', [0]) # signed int
    out_tree.Branch('hit_channels', hit_channels, 'hit_channels/i')

    hit_channelsX = array('I', [0]) # signed int
    out_tree.Branch('hit_channelsX', hit_channelsX, 'hit_channelsX/i')
    
    hit_channelsY = array('I', [0]) # signed int
    out_tree.Branch('hit_channelsY', hit_channelsY, 'hit_channelsY/i')

    hit_map = array('I', [0]*nchannels) # signed int
    out_tree.Branch('hit_map', hit_map, 'hit_map[%i]/i' % nchannels)

    channel = array('I', [0]*nchannels) # unsigned int
    out_tree.Branch('channel', channel, 'channel[%i]/i' % nchannels)

    wfm_max_energy = array('d', [0])
    out_tree.Branch('wfm_max_energy', wfm_max_energy, 'wfm_max_energy/D')

    wfm_area_energy = array('d', [0])
    out_tree.Branch('wfm_area_energy', wfm_area_energy, 'wfm_area_energy/D')

    wfm_area = array('d', [0]*nchannels)
    out_tree.Branch('wfm_area', wfm_area, 'wfm_area[%i]/D' % nchannels)

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

    eventNum = array('I', [0]) # signed int
    out_tree.Branch('eventNum', eventNum, 'eventNum/i')
    
    packetNum = array('I', [0]) # signed int
    out_tree.Branch('packetNum', packetNum, 'packetNum/i')

    file_list = glob.iglob(os.path.join(input_dir, "Chip0*dat"))
    nevents = 0
    
    #Loop over each file in the directory which each contain 4 events/packets from 1 Chip
    #total 4 chips (2 messed up)
    for fi, fname in enumerate(file_list):
        
        #Get packet number from file name
        packet_num = os.path.basename(fname).replace(".dat","")
        packet_num = int(packet_num.replace("Chip0_Packet",""))

        event_data = {}
        for event in xrange(settings.packets_per_file): event_data[event+packet_num] = {}

        #Loop over chips 
        for chip in xrange(settings.chip_num):
            
            chip_fname = fname.replace("Chip0","Chip%i"%chip)
            all_data = Data_Analysis.Data_Analysis().Seperate_Packets(chip_fname)
            
            #Now loop over each event in the and extract the WFs
            for ei,data in enumerate(all_data):
                wf_list  =  Data_Analysis.Data_Analysis().UnpackData(data)
                event_num = packet_num + ei
                
                for wi, wf in enumerate(wf_list):
                    wf_ch = chip*settings.chs_per_chip + wi       
                    if chip==2 or chip==1:
                        #These chips are bad for the moment
                        event_data[event_num][wf_ch] = np.array(wf)*0.0
                    else:
                        event_data[event_num][wf_ch] = np.array(wf)
 

        for ei in event_data:
            
            packetNum[0] = ei       
            eventNum = nevents
            hit_channels[0] = 0
            hit_channelsX[0] = 0
            hit_channelsY[0] = 0
            wfm_max_energy[0] = 0
            wfm_area_energy[0] = 0
            for ch in event_data[ei]:
                wf = np.array(event_data[ei][ch])
                channel[ch] = ch

                wfm_max[ch]       = np.max(wf)
                wfm_min[ch]       = np.min(wf)
                wfm_max_time[ch]  = np.argmax(wf)*0.5
                wfm_min_time[ch]  = np.argmin(wf)*0.5
                wfm_baseline[ch]  = np.mean(wf[:20])

                wf = wf - wfm_baseline[ch]  

                #print np.max(wf),  wfm_max[ch], wfm_min[ch], wfm_max_time[ch], wfm_min_time[ch]
                #integral +/- 20 samples around the max

                t_area_min = np.argmax(wf) - 20
                t_area_max = np.argmax(wf) + 20

                if np.max(wf) > 30:
                    hit_channels[0] +=1
                    hit_map[ch] = 1

                    if ch < 32: hit_channelsX[0] +=1
                    else:       hit_channelsY[0] +=1

                    wfm_area[ch] = np.trapz(wf[t_area_min:t_area_max])
                    
                    wfm_area_energy[0] += wfm_area[ch]
                    wfm_max_energy[0]  += wfm_max[ch]-wfm_baseline[ch]

                    if False:
                        plt.ion()
                        plt.figure(1)
                        plt.clf()
                        area1 = np.trapz(wf[t_area_min:t_area_max])
                        area2 = np.trapz(wf[np.argmax(wf)-40:np.argmax(wf)+40])
                        plt.title("A1=%f, A2=%f" % (area1,area2))
                        plt.axvline(t_area_min, c='r', linewidth=3)
                        plt.axvline(t_area_max, c='r', linewidth=3)
                    
                        plt.axvline(np.argmax(wf)-40, c='g', linewidth=3)
                        plt.axvline(np.argmax(wf)+40, c='g', linewidth=3)
                    
                        plt.plot(wf)
                        raw_input("PAUSE")

                else:
                    wfm_area[ch] = 0.0
                    hit_map[ch]  = 0 

            out_tree.Fill()
            nevents += 1
            if nevents%1000 == 0:
                print nevents, memory_usage_psutil()

        #if nevents > 1000: break
    
    gout.cd("")
    out_tree.Write()
    #out_tree.Close()

if __name__ == "__main__":
    
    parser = OptionParser()
    (options, input_dir) = parser.parse_args()   
    ProcessDir(input_dir[0], output_dir=input_dir[1])


