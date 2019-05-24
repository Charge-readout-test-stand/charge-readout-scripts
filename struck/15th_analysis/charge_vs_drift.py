import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
import scipy.optimize as opt

import FitPeakPy

plt.ion()
plt.figure(1)

def ffnExp(x,A,t):
    exp  = A*np.exp(-x/t)
    return exp

def profileX(x,y, binsX, binsY):
    prof_bins = [] 
    prof_mean = []
    for bi in xrange(len(binsX)-1):
        pcutX = np.logical_and(x>binsX[bi], x<binsX[bi+1])
        pcutY = np.logical_and(y>binsY[0], y<binsY[-1])
        pcut = np.logical_and(pcutX, pcutY)
        prof_mean.append(np.mean(y[pcut]))
        prof_bins.append(np.mean(x[pcut]))
    return np.array(prof_bins), np.array(prof_mean)

def get_cut():
    selection = []
    #selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("SignalEnergy > 0")
    selection.append("nsignals<=2")
    selection.append("nXsignals==1")
    selection.append("nYsignals==1")
    selection = " && ".join(selection)
    return selection


def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    #draw_array.append("SignalEnergyLight")
    draw_array.append("SignalEnergyLight")
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_array.append("(energy[5])")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)


def process_file(filename, corr=1e9, cal=1.0):
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
    tree.SetBranchStatus("SignalEnergyLight",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("nXsignals",1)
    tree.SetBranchStatus("nYsignals",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("energy",1)
    tree.SetBranchStatus("nfound_channels",1)
    #tree.SetBranchStatus("lightEnergy",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)

    selectcmd = get_cut()
    drawcmd,nvals   = get_dcmd()

    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()

    dtmax = 18
    chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy  =  np.array([tree.GetVal(1)[i] for i in xrange(n)])
    driftTime    =  np.array([tree.GetVal(2)[i] for i in xrange(n)])
    energy31     =  np.array([tree.GetVal(3)[i] for i in xrange(n)])

    chargeEnergy *= cal

    drift_time_hist, bin_edges = np.histogram(driftTime, bins=100, range=(0,dtmax))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

    plt.clf()
    plt.title("Drift Time Distribution")
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=15)
    plt.ylabel("Counts/%.2f" % np.diff(bin_edges)[0], fontsize=15)
    plt.errorbar(bin_centers, drift_time_hist, yerr=np.sqrt(drift_time_hist),marker='o', linestyle='None', c='k')
    plt.show()
    plt.savefig("./plots/driftTimeDist.pdf")
    raw_input("PAUSE1")


    plt.clf()
    H = plt.hist2d(driftTime, energy31, bins=[100,100], range=[[0,dtmax],[0,200]],
            norm=colors.LogNorm(vmin=1,vmax=1000))
    raw_input()

    plt.clf()
    H = plt.hist2d(driftTime, chargeEnergy, bins=[100,100], range=[[0,dtmax],[0,1500]],
                                                       norm=colors.LogNorm(vmin=1,vmax=1500))
    
    pX,pY = profileX(driftTime, chargeEnergy, binsX=np.arange(0,14,2), binsY=np.arange(10, 1000, 10))
    #pX,pY = profileX(driftTime, chargeEnergy, binsX=np.arange(0,20,2), binsY=np.arange(50, 1000, 10))

    #plt.plot(pX, pY, marker='o', ms=10, linestyle='None', color='k')

    plt.title("Charge vs Drift",fontsize=16)
    plt.colorbar()
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=15)
    plt.ylabel("UnCorrected Charge Energy",fontsize=15)
    plt.savefig("./plots/driftTimeDist_vs_ChargeEnergy_%s.pdf" % bname)
    raw_input("PAUSE2")

    plt.clf()
    bp, bcov = opt.curve_fit(ffnExp, pX, pY, p0=[600,5.0])
    plt.title(bp)
    plt.plot(pX, pY, marker='o', ms=10, linestyle='None', color='k')
    plt.plot(pX, ffnExp(pX, bp[0], bp[1]))
    
    raw_input("PAUSE")


    plt.clf()
    chargeEnergy_corr = chargeEnergy/np.exp(-driftTime/corr)
    H = plt.hist2d(driftTime, chargeEnergy_corr, bins=[50,50], range=[[0,dtmax],[0,1500]],
                                                                           norm=colors.LogNorm(vmin=1,vmax=1000))

    #pX,pY = profileX(driftTime, chargeEnergy_corr, binsX=np.arange(0,20,2), binsY=np.arange(50, 1000, 10))
    #plt.plot(pX, pY, marker='o', ms=10, linestyle='None', color='k')
    plt.title(r"Charge vs Drift ($\tau_{e}$=%.2fus)"%corr,fontsize=16)
    plt.colorbar()
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=15)
    plt.ylabel(r"Corrected Charge Energy ($\tau_{e}$=%.2fus)"%corr,fontsize=15)
    plt.savefig("./plots/driftTimeDist_vs_ChargeEnergy_quickCorr_%s.pdf" % bname)
    
    raw_input("PAUSE3")

    plt.clf()
    drift_cut = np.logical_and(driftTime>10, driftTime<16)
    hist_corr, bin_edges= np.histogram(chargeEnergy_corr[drift_cut], bins=100, range=(100,1500))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    hist_uncorr, bin_edges= np.histogram(chargeEnergy[drift_cut], bins=100, range=(100,1500))

    plt.errorbar(bin_centers, hist_corr,   yerr=np.sqrt(hist_corr), 
                        marker='o', linestyle='None', c='k', label="Purity Corrected")
    plt.errorbar(bin_centers, hist_uncorr, yerr=np.sqrt(hist_uncorr),
                        marker='o', linestyle='None', c='r', label="Un-Corrected")

    plt.title(r"Charge Energy (10us <Drift-Time < 16us) ($\tau_{e}$=%.2fus)"%corr)
    plt.legend(loc='upper right')
    plt.xlabel(r"Charge Energy [uncal]",fontsize=15)
    plt.ylabel("Counts",fontsize=15)
    plt.savefig("./plots/spectrum_with_correction_10_to_16_%s.pdf" % bname)
    raw_input("PAUSE3")

    hist_corr10 = {'bins':bin_centers, 'counts':hist_corr}
    
    plt.clf()
    drift_cut = np.logical_and(driftTime>2, driftTime<5)
    hist_corr, bin_edges= np.histogram(chargeEnergy_corr[drift_cut], bins=100, range=(100,1500))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    hist_uncorr, bin_edges= np.histogram(chargeEnergy[drift_cut], bins=100, range=(100,1500))

    plt.errorbar(bin_centers, hist_corr,   yerr=np.sqrt(hist_corr),
                        marker='o', linestyle='None', c='k', label="Purity Corrected")
    plt.errorbar(bin_centers, hist_uncorr, yerr=np.sqrt(hist_uncorr),
                        marker='o', linestyle='None', c='r', label="Un-Corrected")

    plt.title(r"Charge Energy (2us <Drift-Time < 5us) ($\tau_{e}$=%.2fus)"%corr)
    plt.legend(loc='upper right')
    plt.xlabel(r"Charge Energy [uncal]",fontsize=15)
    plt.ylabel("Counts",fontsize=15)
    plt.savefig("./plots/spectrum_with_correction_2_to_5_%s.pdf" % bname)

    raw_input("PAUSE3")
    
    return hist_corr10

def Compare(hist_list):
    plt.figure(2)
    
    for hist in hist_list:
        norm  = 1.0/np.sum(hist[1]['counts'])
        
        fitx, bp, bcov, fail, full_fit, gaus,exp = FitPeakPy.FitPeak(hist[1]['counts']*norm, 
                                                                   np.sqrt(hist[1]['counts'])*norm, 
                                                                   hist[1]['bins'], 570, 150)

        print "Result", bp
        print np.shape(full_fit), full_fit
        print np.shape(fitx), fitx

        plt.errorbar(hist[1]['bins'], hist[1]['counts']*norm, yerr=np.sqrt(hist[1]['counts'])*norm, drawstyle='steps-mid',
                        linewidth=2,  color=hist[2],
                        label=r"%s ($\sigma$/E = %.2f %%)"% (hist[0], (bp[2]*100/bp[1])))
        
        plt.plot(fitx, full_fit, color=hist[2], linewidth=3, linestyle='--')

    plt.title(r"Charge Energy (10us < Drift-Time < 16us)")
    plt.legend(loc='upper right')
    plt.xlabel(r"Charge Energy [uncal]",fontsize=15)
    plt.ylabel("Counts",fontsize=15)

    plt.savefig("./plots/compare_spectrum_new_vs_old.pdf")
    raw_input("PAUSE COMPARE")

if __name__ == "__main__":
 
    #filename = "/home/teststand/21st_LXe/overnight_run_3_29_2019/tier3_added/tier3_added_21st_overnight_3_29_2019_v1.root"
    #process_file(filename, corr=1.0e9)
    #raw_input("21st")

    #filename = "/home/teststand/21st_LXe/day_testing_3_30_2019_pumprunning/tier3_added/tier3_added_21st_day_runs_pumpoff_3_30_2019_v1.root"
    #process_file(filename, corr=1.0e9)
    #raw_input("21st (after pump)")

    #filename="/home/teststand/20th_LXe/tier3_added_day1_overnight1_20th_v1.root"
    #process_file(filename, corr=17.0)
    #raw_input("20th")

    #filename="/home/teststand/19th_LXe/overnight_2_19_2019/tier3_added/tier3_added_overnight_19th_thresh15_v1.root"
    #filename="/home/teststand/19th_LXe/tier3_added_overnight1+2_19th_v1.root"
    #process_file(filename, corr=23.0)
    #raw_input("PAUSE 19th")

    filename = "/home/teststand/22nd_LXe/overnight_4_17_2019/tier3_added/tier3_22nd_overnight_4_17_2019_v1.root"
    hist_corr10_old = process_file(filename, corr=50.0, cal=570/587.)
    raw_input("PAUSE 22nd")

    filename = "/home/teststand/11th_LXe/2017_02_01_overnight_vme/tier3_added/tier3_combined_rise10.root"
    hist_corr10_old = process_file(filename, corr=1e9, cal=570/587.)
    raw_input("PAUSE 11th")

    #filename="/home/teststand/15th_LXe/overnight_fullCell/tier3_added/tier3_allData_v2_sipmGain.root"
    #process_file(filename, corr=3.5)
 
    #filename="/home/teststand/16th_LXe/overnigh_fullCell/tier3_added/tier3_added_overnight_v2_alldata.root"
    filename="/home/teststand/16th_LXe/tier3_added_overnight_16th_thresh15.root"
    process_file(filename, corr=6.3)
    raw_input("PAUSE 16th")


    #filename = "/home/teststand/16th_LXe/overnight_fullCell_12_4_2018/tier3_added/tier3_added_all_v1_12_18_2018.root"
    #process_file(filename, corr=4.5)

    #filename = "/home/teststand/17th_LXe/overnight_12_18_2018/tier3_added/tier3_added_all_overnight_12_18_2018_v1.root"
    #filename  = "/home/teststand/17th_LXe/overnight_12_18_2018/tier3_added/tier3_added_overnight_12_18_2018_17th_thresh15.root"
    filename = "/home/teststand/17th_LXe/overnight_12_18_2018/tier3_added/tier3_added_overnight_12_18_2018_17th_thresh15.root"
    hist_corr10_new = process_file(filename, corr=14.0, cal=570./497.)
    #hist_corr10_new = process_file(filename, corr=11.0, cal=570./497.)

    filename  = "/home/teststand/18th_LXe/overnight_1_22_2019/tier3_added/tier3_added_overnight_18th_1_23_2019_thresh15.root"
    hist_corr10_new2 = process_file(filename, corr=23.0, cal=570./497.)

    Compare([["New", hist_corr10_new,'r'], ["New2", hist_corr10_new2, 'b']])
    #Compare([["Old", hist_corr10_old,'r'], ["New", hist_corr10_new, 'b']])

    #filename = "/home/teststand/17th_LXe/day_testing_12_19_2018/tier3_added/tier3_all_added_day_testing_12_19_2019_v1.root"
    #process_file(filename, corr=14.0)

    #filename = "/home/teststand/17th_LXe/overnight_12_18_2018/tier3_added/tier3_added_first_2hrs_overnight_v1.root"
    #process_file(filename, corr=14.0)

    #filename = "/home/teststand/17th_LXe/day_testing_12_18_2018/tier3_added/tier3_added_all_day_testing_12_18_2018_diffTrigs.root"
    #process_file(filename, corr=14.0)

    #filename="/home/teststand/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v4_12_7_2017.root"
    #process_file(filename)

    #filename="/home/teststand/13thLXe/all_tier3_overnight_day2_315bias_v3.root"
    #process_file(filename)

    #filename="/home/teststand/15th_LXe/mc/tier3_added_4us_500files.root"
    #process_file(filename)

    #filename="/home/teststand/15th_LXe/mc/tier3_added_inf_500files.root"
    #process_file(filename)


