import ROOT
import numpy as np
import scipy.optimize as opt
import matplotlib.backends.backend_pdf as PdfPages
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys,glob
import Data_Analysis

#Settings from Eric
from user_settings import user_editable_settings
settings = user_editable_settings()


plt.ion()

def process_file(filename):
    
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())
    
    print "Total Entries in Tree", tree.GetEntries()

    drawcmd   = "setNum:packetNum:segNum"
    selectcmd = "hit_channels>14"

    print "Draw"
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    print "Number after Draw",  n

    setNum       =   np.array([tree.GetVal(0)[i] for i in xrange(n)])
    packetNum    =   np.array([tree.GetVal(1)[i] for i in xrange(n)])
    segNum       =   np.array([tree.GetVal(2)[i] for i in xrange(n)])
    
    parse_dir = "/p/lscratchd/jewell6/14thLXe_BNL/parsed_data/"

    for setN,packN,segN in zip(setNum,packetNum,segNum):
        check_dir = os.path.join(parse_dir, "set%i"%setN)
        packet = packN-segN 
        check_dir = os.path.join(check_dir, "Chip0*%i.dat" % packet)
        file_list = glob.glob(check_dir)
        
        if len(file_list) != 1:
            print "HMM", len(file_list)
            print file_list
            print check_dir
            raw_input()
        
        fname = file_list[0]
        print "FNAME", fname

        plt.figure(1)
        plt.clf()
        plt.subplot(212)
        wfimage = np.zeros((settings.chip_num*16, 141))
        for chip in xrange(settings.chip_num):
            chip_fname = fname.replace("Chip0", "Chip%i"%chip)

            all_data = Data_Analysis.Data_Analysis().Seperate_Packets(chip_fname)
            print segN
            wf_list=None

            for ei,data in enumerate(all_data):
                if ei != segN:continue
                wf_list  =  Data_Analysis.Data_Analysis().UnpackData(data)
        
            for wi, wf in enumerate(wf_list):
                ch = chip*16 + wi
                wfimage[ch] = wf - np.mean(wf[:20])
                
                if np.max(wf - np.mean(wf[:20])) > 30 and chip == 1:
                    plt.plot(wf)
                    print ch, np.max(wf), np.argmax(wf)

        plt.ion()
        plt.subplot(211)
        plt.imshow(wfimage, interpolation='nearest', vmin=-10, vmax=100)
        plt.show()
        raw_input()



if __name__ == "__main__":

    #filename = "/g/g19/jewell6/jewell6/14thLXe_BNL/summed_tier3/tier3_added_v1.root"
    #filename  = "/g/g19/jewell6/jewell6/14thLXe_BNL/summed_tier3/tier3_added_v2.root"
    #filename  = "/g/g19/jewell6/jewell6/14thLXe_BNL/summed_tier3/tier3_added_v3.root"
    filename  = "/g/g19/jewell6/jewell6/14thLXe_BNL/summed_tier3/tier3_added_v4.root"

    print "Using ", filename
    process_file(filename)

