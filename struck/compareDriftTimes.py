import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
plt.ion()
plt.figure(1)

def get_cut():
    selection = []
    selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("SignalEnergy > 300")
    selection.append("nsignals==2")
    selection.append("nXsignals==1")
    selection.append("nYsignals==1")
    selection = " && ".join(selection)
    return selection

def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    #draw_array.append("SignalEnergyLight")
    draw_array.append("lightEnergy")
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def process_file(filename):
    plt.figure(1)
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())
    
    bname = os.path.basename(filename).split(".")[0]
    print bname
    field = (bname.split("_"))[-2].split("V.")[0]

    #Speed things up by setting on and off branches
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("SignalEnergy",1)
    #tree.SetBranchStatus("SignalEnergyLight",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("nXsignals",1)
    tree.SetBranchStatus("nYsignals",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("energy",1)
    tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("lightEnergy",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)

    selectcmd = get_cut()
    drawcmd,nvals   = get_dcmd()
 
    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    
    dtmax = 24
    chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy  =  np.array([tree.GetVal(1)[i] for i in xrange(n)])
    driftTime    =  np.array([tree.GetVal(2)[i] for i in xrange(n)])
    
    print driftTime

    drift_time_hist, bin_edges = np.histogram(driftTime, bins=100, range=(0,dtmax))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

    plt.title("Drift Time Distribution")
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=15)
    plt.ylabel("Counts/%.2f" % np.diff(bin_edges)[0], fontsize=15)
    plt.errorbar(bin_centers, drift_time_hist, yerr=np.sqrt(drift_time_hist),marker='o', linestyle='None', c='k')
    plt.show()
    plt.savefig("./plots/driftTimeDist.pdf")
    raw_input()

    plt.clf()
    plt.title("Light vs Drift",fontsize=16)
    H = plt.hist2d(driftTime, lightEnergy, bins=[100,100], range=[[0,dtmax],[0,10000]],
                                           norm=colors.LogNorm(vmin=1,vmax=100))    
    plt.colorbar()
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=15)
    plt.ylabel("Light Energy",fontsize=15)
    plt.savefig("./plots/driftTimeDist_vs_LightEnergy.pdf")
    raw_input()

    plt.clf()
    plt.title("Charge vs Drift",fontsize=16)
    H = plt.hist2d(driftTime, chargeEnergy, bins=[100,100], range=[[0,dtmax],[0,1400]], 
                   norm=colors.LogNorm(vmin=1,vmax=100))
    plt.colorbar()
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=15)
    plt.ylabel("Charge Energy",fontsize=15)
    plt.savefig("./plots/driftTimeDist_vs_ChargeEnergy_%s.pdf" % bname)
    raw_input()

    return {"data":drift_time_hist, "centers": bin_centers, "field":field}

if __name__ == "__main__":

    filenames = ["tier3_added_305bias_330V_v2.root", "tier3_added_305bias_1550V_v2.root", "tier3_added_305bias_3110V_v2.root"]  
    color = ['r','b','g']
    for ci,filename in enumerate(filenames):
        print "Using ", filename
        data = process_file(filename)
        print data
        plt.figure(2)
        plt.errorbar(data['centers'], data['data'], yerr=np.sqrt(data['data']),marker='o', 
                linestyle='None', c=color[ci], label='%s/cm'%data['field'])
    plt.legend()
    plt.title("Drift Time Distribution",fontsize=16)
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=15)
    plt.ylabel("Counts", fontsize=15)

    plt.savefig("./plots/driftTime_vs_field.pdf")
    plt.show()
    raw_input()
