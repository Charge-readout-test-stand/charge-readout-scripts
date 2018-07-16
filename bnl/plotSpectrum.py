import ROOT
import numpy as np
import scipy.optimize as opt
import matplotlib.backends.backend_pdf as PdfPages
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys


plt.ion()

def process_file(filename):
    
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())
    
    print "Total Entries in Tree", tree.GetEntries()

    drawcmd   = "wfm_max_energy:wfm_area_energy:hit_channels:Max$(wfm_max_time*hit_map)"
    #selectcmd = "hit_channels==2 && (hit_channelsX==1 && hit_channelsY==1)"
    selectcmd = "hit_channels>0.5"

    print "Draw"
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    print "Number after Draw",  n

    maxEnergy   =   np.array([tree.GetVal(0)[i] for i in xrange(n)])
    areaEnergy  =   np.array([tree.GetVal(1)[i] for i in xrange(n)])
    nsigs       =   np.array([tree.GetVal(2)[i] for i in xrange(n)])
    maxTime     =   np.array([tree.GetVal(3)[i] for i in xrange(n)])

    #drawcmd = "hit_channelsX:hit_channelsY"
    #tree.Draw(drawcmd,selectcmd,"goff")
    #n = tree.GetSelectedRows()
    #nXsigs   = np.array([tree.GetVal(0)[i] for i in xrange(n)])
    #nYsigs   = np.array([tree.GetVal(1)[i] for i in xrange(n)])

    fs = 15
    plt.figure(1)
    #plt.subplot(11)
    #plt.hist(maxEnergy,bins=200, range=(0,3000))
    hist,bin_edges =np.histogram(maxEnergy,bins=120, range=(0,5000))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0   
    #plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist), marker='o', ms=6, linestyle='None', color='b')
    plt.step(bin_centers, hist, linewidth=2)
    plt.xlabel("Sum(WF Max)", fontsize=fs)
    plt.ylabel("Counts", fontsize=fs)
    plt.xlim(0,5000)
    plt.savefig("./plots/energy_summed_max_amp.png")
    plt.yscale('log')
    plt.savefig("./plots/energy_summed_max_amp_log.png")

    plt.figure(2)
    #plt.subplot(221)
    #plt.hist(maxEnergy,bins=200, range=(0,3000))
    hist,bin_edges =np.histogram(areaEnergy,bins=150, range=(0,5000))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    #plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist), marker='o', ms=6, linestyle='None', color='b')
    plt.step(bin_centers, hist, linewidth=2)
    plt.xlabel("Sum(WF Area)", fontsize=fs)
    plt.ylabel("Counts", fontsize=fs)
    plt.xlim(0,5000)
    plt.savefig("./plots/energy_summed_area.png")
    plt.yscale('log')
    plt.savefig("./plots/energy_summed_area_log.png")
    



    plt.figure(3)
    plt.hist2d(maxEnergy, areaEnergy, bins=[100,100], range=[[0,5000],[0,5000]],
                    norm=colors.LogNorm(vmin=1,vmax=1000))

    plt.xlabel("Sum(WF Max)", fontsize=fs)
    plt.ylabel("Sum(WF Area)", fontsize=fs)
    plt.savefig("./plots/WFarea_vs_max.png")

    plt.figure(4)
    plt.hist(nsigs, bins = np.arange(-0.5, 25.5, 1))
    plt.xlabel("Number Hit Channels", fontsize=fs)
    plt.ylabel("Counts", fontsize=fs)
    plt.yscale('log')
    plt.xlim(0,25)
    plt.savefig("./plots/event_ch_mult.png")

    plt.figure(5)
    hist,bin_edges =np.histogram(maxTime[np.logical_and(nsigs==1, maxEnergy>100)],bins=np.arange(0, 100, 0.5))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    plt.step(bin_centers, hist, linewidth=2)

    plt.axvline(37, color='g', linestyle='--', linewidth=3, label='cath')
    plt.axvline(20, color='r', linestyle='--', linewidth=3, label='anode')
    plt.xlabel("Max Time [us]", fontsize=fs)
    plt.ylabel("Counts", fontsize=fs)
    plt.yscale('log')
    plt.xlim(15,50)
    plt.legend()
    plt.grid(True)
    plt.savefig("./plots/max_drift_time.png")

    plt.show()
    raw_input()

if __name__ == "__main__":

    #filename = "/g/g19/jewell6/jewell6/14thLXe_BNL/summed_tier3/tier3_added_v1.root"
    #filename  = "/g/g19/jewell6/jewell6/14thLXe_BNL/summed_tier3/tier3_added_v2.root"
    filename  = "/g/g19/jewell6/jewell6/14thLXe_BNL/summed_tier3/tier3_added_v3.root"

    print "Using ", filename
    process_file(filename)

