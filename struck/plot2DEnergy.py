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
    selection.append("SignalEnergy > 200")
    selection.append("nsignals==2")
    selection.append("nXsignals==1")
    selection.append("nYsignals==1")
    selection = " && ".join(selection)
    return selection

def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    draw_array.append("lightEnergy")
    #draw_array.append("energy[29]")
    #draw_array.append("energy[30]")
    #draw_array.append("energy[31]")
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
    #tree.SetBranchStatus("is_bad",1)
    #tree.SetBranchStatus("is_pulser",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("energy",1)
    tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("lightEnergy",1)
    #tree.SetBranchStatus("calibration",1)
    #tree.SetBranchStatus("energy1_pz",1)
    #tree.SetBranchStatus("trigger_time",1)
    #tree.SetBranchStatus("rise_time_stop95_sum",1)

    selectcmd = get_cut()
    drawcmd,nvals   = get_dcmd()
 
    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    
    chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy = []
    
    for nval in xrange(nvals-1):
        lightEnergy.append(np.array([tree.GetVal(nval+1)[i] for i in xrange(n)]))

    #H, xedges, yedges = np.histogram2d(chargeEnergy, lightEnergy, bins=[100,100], range=[[0,2000],[0,2000]])

    skipSum = False
    for nval in xrange(nvals-1):
        if nval > 0:
            ymax = 50
        else:
            ymax = 200
        xlabel = drawcmd.split(":")[0]
        ylabel = drawcmd.split(":")[nval+1]
    
        if ylabel == "lightEnergy":
            ymax = 10000
            skipSum = True
        plt.clf()
        H = plt.hist2d(chargeEnergy, lightEnergy[nval], bins=[100,100], range=[[200,1200],[0,ymax]], 
                       norm=colors.LogNorm(vmin=1,vmax=100))
    
        plt.colorbar()
        plt.xlabel(xlabel,fontsize=15)
        plt.ylabel(ylabel,fontsize=15)
        plt.title("Light vs Charge")
        plt.savefig("./plots/light_vs_charge_%s.pdf" % ylabel)
        plt.show()
        raw_input()
    plt.clf()

    if not skipSum:
        H = plt.hist2d(chargeEnergy, lightEnergy[0] + lightEnergy[1] + lightEnergy[2], bins=[100,100], range=[[200,1200],[0,1000]])
        plt.xlabel(xlabel,fontsize=15)                
        plt.ylabel("Sum Light 29+30+31",fontsize=15)
        plt.title("Light vs Charge")
        plt.savefig("./plots/light_vs_charge_sum.pdf")
        raw_input()
    else:
        for theta in np.arange(0.0, 0.3, 0.05):
            plt.clf()
            H = plt.hist((chargeEnergy*np.cos(theta) + lightEnergy[0]*np.sin(theta)), 100, range=(300,2000), facecolor='b', alpha=0.4)
            plt.title("Theta = %.2f" % theta)
            plt.show()
            raw_input()

if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)

