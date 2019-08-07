import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
import struck_analysis_parameters
import struck_analysis_cuts_sipms
import scipy.optimize as opt

plt.ion()

def get_dcmd():
    draw_array = []
    draw_array.append("(channel*(sipm_max/baseline_rms_filter > 10.0))")
    draw_array.append("(channel*(sipm_min/baseline_rms_filter < -20.0))")
    #draw_array.append("channel")
    draw_array.append("sipm_max")
    draw_array.append("sipm_min")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def process_file(filename):
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())
    bname = os.path.basename(filename)
    bname = bname.replace(".root", "")

    min_time  = struck_analysis_cuts_sipms.get_min_time(tfile.Get("run_tree"))
    selectcmd = struck_analysis_cuts_sipms.get_cut_norise(min_time)

    #Speed things up by setting on and off branches
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("SignalEnergy",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("nXsignals",1)
    tree.SetBranchStatus("nYsignals",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("sipm_max",1)
    tree.SetBranchStatus("sipm_min",1)
    tree.SetBranchStatus("baseline_rms_filter",1)

    drawcmd,nvals   = get_dcmd()
    
    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()

    positiveSigs =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    negSigs      =  np.array([tree.GetVal(1)[i] for i in xrange(n)])
    sipmMax      =  np.array([tree.GetVal(2)[i] for i in xrange(n)])
    sipmMin      =  np.array([tree.GetVal(3)[i] for i in xrange(n)])

    plt.figure(figsize=(11,7))
    
    posSig = ((sipmMax+sipmMin) > 0)
    negSig = ((sipmMax+sipmMin) < 0)

    posHist,bin_edges = np.histogram(positiveSigs[posSig], bins=32, range=(0,32))
    pos_bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    
    negHist,bin_edges = np.histogram(negSigs[negSig], bins=32, range=(0,32))
    neg_bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

    xtick    = []
    posEntry = []
    negEntry = []
    xtick_labels=[]

    for i in xrange(len(posHist)):
        print pos_bin_centers[i], posHist[i], negHist[i]
        if posHist[i] > 0 and pos_bin_centers[i] > 4.5:
            #xtick.append(pos_bin_centers[i])
            xtick.append(len(xtick))
            negEntry.append(negHist[i])
            posEntry.append(posHist[i])
            xtick_labels.append(struck_analysis_parameters.channel_map[i])

    print xtick
    print xtick_labels

    plt.bar(xtick, posEntry, 0.5, color='r', alpha=1.0,label='Positive', align='center')
    plt.bar(xtick, negEntry, 0.5, bottom=posEntry, color='b', alpha=1.0, label='Negative', align='center')
    plt.xticks(xtick, xtick_labels, rotation='vertical', fontsize=18)
    plt.ylim(0,120000)
    plt.xlim(-1,12)
    plt.legend(fontsize=20)
    plt.title("SiPM Frequency of Positive and Negative Signals",fontsize=18)
    plt.ylabel("Counts",fontsize=18)
    plt.show()
    plt.savefig("./plots/sipm_multiplicity.pdf")
    raw_input()
    

if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        #filename  = "overnight_new_bias_tier3_all_v3_12_6_2017.root"
        #filename   = "all_tier3_overnight_day2_315bias_v1.root"
        filename   = "~/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v3_12_6_2017.root"
    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)



