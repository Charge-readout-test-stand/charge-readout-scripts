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

    ch_list   = np.arange(0,64,1)
    mult_list = np.zeros_like(ch_list) 

    for ch in ch_list:
        drawcmd   = "(wfm_max[%i]-wfm_baseline[%i])" % (ch,ch)
        selectcmd = "hit_map[%i]>0.5" % ch

        print "Draw Ch:", ch
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        print "Number after Draw",  n

        chEnergy  = np.array([tree.GetVal(0)[i] for i in xrange(n)])

        plt.figure(1)
        plt.clf()
        hist,bin_edges = np.histogram(chEnergy, bins = 150, range=(0,3000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        
        print "Intgeral is ", np.sum(hist)
        mult_list[ch] = np.sum(hist)

        plt.step(bin_centers, hist, linewidth=2)
        plt.xlim(0,3000)
        plt.yscale('log')
        plt.ylabel("Counts", fontsize=14)
        plt.xlabel("WF Max", fontsize=14)
        plt.title("Ch=%i"%ch, fontsize=14)
        plt.show()
        plt.grid(True)
        plt.savefig("./plots/ch%i_spectrum.png"%ch)
        #raw_input()
        #if ch > 3: break

    plt.figure(2)
    plt.bar(ch_list, mult_list, width=0.5, align='center')
    plt.xlabel("Channel #", fontsize=14)
    plt.ylabel("Counts", fontsize=14)
    plt.xlim(-1,64)
    plt.grid(True)
    plt.savefig("./plots/channel_mult.png")

    
    plt.show()
    raw_input()

if __name__ == "__main__":

    #filename = "/g/g19/jewell6/jewell6/14thLXe_BNL/processed_data/tier3_added_v1.root"
    filename  = "/g/g19/jewell6/jewell6/14thLXe_BNL/processed_data/tier3_added_v2.root"
    
    print "Using ", filename
    process_file(filename)

