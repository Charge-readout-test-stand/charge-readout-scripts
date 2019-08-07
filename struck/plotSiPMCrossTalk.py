import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
import struck_analysis_parameters
import struck_analysis_cuts_sipms
import scipy.optimize as opt
import FitPeakPy
import matplotlib.backends.backend_pdf as PdfPages

plt.ion()


def get_dcmd():
    draw_array = []
    draw_array.append("Max$(sipm_max*(abs(sipm_max_time-trigger_time)<0.2))")
    draw_array.append("Min$(sipm_min*(abs(sipm_min_time-trigger_time)<0.2))")
    #draw_array.append("TMath::LocMax(sipm_max)")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd

def process_file(filename):
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())
    
    bname = os.path.basename(filename)
    bname = bname.replace(".root", "")
    min_time  = struck_analysis_cuts_sipms.get_min_time(tfile.Get("run_tree"))
    print min_time

    selectcmd = struck_analysis_cuts_sipms.get_std_cut(min_time)
    drawcmd   = get_dcmd()

    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    
    sipmMax    =   np.array([tree.GetVal(0)[i] for i in xrange(n)])
    sipmMin    =   np.array([tree.GetVal(1)[i] for i in xrange(n)])
    #sipmMaxArg =   np.array([tree.GetVal(2)[i] for i in xrange(n)])

    plt.figure(figsize=(9,5))
    H = plt.hist2d(sipmMax,sipmMin, bins=[100,100], range=[[0,3000],[-3000,0]],
                   norm=colors.LogNorm(vmin=1,vmax=100))
    cb = plt.colorbar()
    cb.set_label("Counts", fontsize=15)
    plt.title("SiPM Max vs Min", fontsize=16)
    plt.xlabel("SiPM Max [ADC]", fontsize=16)
    plt.ylabel("SiPM Min [ADC]", fontsize=16)
    fitx = np.arange(0,3000,1)
    fity1 = -1.0*fitx
    fity2 = -0.65*fitx
    plt.plot(fitx,fity1,c='r',linewidth=9, linestyle='--', label='100% corr')
    plt.plot(fitx,fity2,c='g',linewidth=9, linestyle='--', label='65%  corr')
    plt.legend(loc='lower left')
    plt.savefig("./plots/sipm_max_vs_sipm_min_%s.pdf" % bname)
    raw_input()
    
    plt.figure(figsize=(9,5))
    hist,bin_edges = np.histogram(abs(sipmMin/sipmMax), bins=200, range=(0.001, 3.0))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    plt.step(bin_centers, hist, where='post', linewidth=2.0)
    plt.title("Ratio of Min and Max SiPM Signal", fontsize=16)
    plt.xlabel("SiPM abs(Min/Max)", fontsize=16)
    plt.ylabel("Counts", fontsize=16)
    plt.savefig("./plots/sipm_max_vs_sipm_min_ratio_%s.pdf" % bname)
    
    raw_input()

if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        #filename  = "~/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v3_12_6_2017.root"
        filename  = "all_tier3_overnight_day2_315bias_v1.root"
        #filename  = "~/2018_01_26_SiPM_Run2/full_cell_day_runs/tier3_added/all_tier3_day1_305bias_v2.root"
        #filename  = "~/2018_01_26_SiPM_Run2/full_cell_day_runs_2/tier3_added/all_tier3_day2_305bias.root"
    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)


