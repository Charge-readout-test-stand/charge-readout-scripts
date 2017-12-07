import sys
import numpy as np
import matplotlib.pyplot as plt
import struck_analysis_parameters
import ROOT

def get_cut(ch):
    selection = []
    selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("SignalEnergy > 300")
    selection.append("SignalEnergy < 1000")
    selection.append("nsignals==2")
    selection.append("(nXsignals==1 && nYsignals==1)")
    selection.append("channel==%i" % ch)
    selection.append("(rise_time_stop95_sum-trigger_time) > 10")
    selection.append("(rise_time_stop95_sum-trigger_time) < 15")
    selection = " && ".join(selection)
    return selection

def get_dcmd(ch):
    draw_array = []
    #draw_array.append("energy[%i]" % ch)
    draw_array.append("(sipm_max[%i] + sipm_min[%i])" % (ch,ch))
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def process_file(filename):
    
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())

    #Speed things up by setting on and off branches
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("SignalEnergy",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("nXsignals",1)
    tree.SetBranchStatus("nYsignals",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("energy",1)
    tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)
    tree.SetBranchStatus("sipm_max",1)
    tree.SetBranchStatus("sipm_min",1)

    sipm_channels_to_use = struck_analysis_parameters.sipm_channels_to_use
    channel_map          = struck_analysis_parameters.channel_map
    
    energy_list = []
    name_list   = []
    #energy_matrix = np.zeros(sum(sipm_channels_to_use),sum(sipm_channels_to_use))

    for ch,isGood in enumerate(sipm_channels_to_use):
        if not isGood:continue

        selectcmd           = get_cut(ch)
        drawcmd,dsize       = get_dcmd(ch)
        print "Draw: %s" % drawcmd
        print "Select: %s" % selectcmd
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        channelEnergy =  np.array([tree.GetVal(0)[j] for j in xrange(n)])
        print channel_map[ch], len(channelEnergy)
        energy_list.append(channelEnergy)
        #raw_input()
        #if len(energy_list) > 3: break
        name_list.append(channel_map[ch])

    print np.sum(sipm_channels_to_use)
    print len(energy_list[0])

    energy_matrix = np.zeros((len(energy_list), len(energy_list[0])))
    for ei in xrange(len(energy_list)):
        energy_matrix[ei] = energy_list[ei]
    
    print np.shape(energy_matrix)
    corr_matrix =  np.corrcoef(energy_matrix)
    
    print corr_matrix
    
    plt.figure(figsize=(12,7))
    plt.ion()
    corr_max = 0.65
    plt.imshow(corr_matrix,interpolation='nearest', vmin=-1*corr_max, vmax=corr_max)
    #plt.grid()
    cb = plt.colorbar()
    cb.set_label("Correlation Coef", fontsize=18)
    xticks = np.arange(len(name_list))
    plt.xticks(xticks, name_list, rotation='vertical', fontsize=17)
    plt.yticks(xticks, name_list, rotation='horizontal', fontsize=17)
    plt.title("SiPM Correlation Matrix",fontsize=18)
    plt.show()
    plt.savefig("./plots/sipm_correlation_matrix.pdf")
    raw_input()


if __name__ == "__main__":
    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        filename  = "overnight_new_bias_tier3_all_v3_12_6_2017.root"
    else:
        filename = sys.argv[1]
    
    print "Using ", filename
    process_file(filename)
