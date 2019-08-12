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

DoLightCorrection=False

def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    draw_array.append("SignalEnergyLight")
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd

def process_files(file_list):

    for filename in file_list:
        tfile = ROOT.TFile(filename)
        tree = tfile.Get("tree")
        tree.SetEstimate(tree.GetEntries())

        bname = os.path.basename(filename)
        bname = bname.replace(".root", "")

        min_time  = struck_analysis_cuts_sipms.get_min_time(tfile.Get("run_tree"))

        #Speed things up by setting on and off branches
        tree.SetBranchStatus("*",0)
        tree.SetBranchStatus("SignalEnergy",1)
        tree.SetBranchStatus("nsignals",1)
        tree.SetBranchStatus("nXsignals",1)
        tree.SetBranchStatus("nYsignals",1)
        tree.SetBranchStatus("channel",1)
        tree.SetBranchStatus("energy",1)
        tree.SetBranchStatus("nfound_channels",1)
        tree.SetBranchStatus("SignalEnergyLight",1)
        tree.SetBranchStatus("lightEnergy",1)
        tree.SetBranchStatus("rise_time_stop95_sum",1)
        tree.SetBranchStatus("trigger_time",1)
        
        selectcmd  = struck_analysis_cuts_sipms.get_std_cut(min_time)
        drawcmd    = get_dcmd()
        print "Draw CMD",  drawcmd
        print "Select CMD",selectcmd
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()

        lightCal   = struck_analysis_cuts_sipms.light_cal(min_time)
        rotCal     = struck_analysis_cuts_sipms.rot_cal(min_time)
        chargeCal  = struck_analysis_cuts_sipms.charge_cal(min_time)
        theta = struck_analysis_cuts_sipms.get_theta(min_time)        

        chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
        lightEnergy =   np.array([tree.GetVal(1)[i] for i in xrange(n)])
        driftTime    =  np.array([tree.GetVal(2)[i] for i in xrange(n)])
        lightEnergy *= lightCal      
        chargeEnergyCut, lightEnergyCut, diag_parms, diag_cut =  struck_analysis_cuts_sipms.diag_cut(chargeEnergy,
                                                                                          lightEnergy, min_time)
        rotEnergyCut = (chargeEnergyCut*np.cos(theta) + lightEnergyCut*np.sin(theta))
        rotEnergyCut *= rotCal/(np.cos(theta) + np.sin(theta))        
        chargeEnergyCut *= chargeCal

        if "overnight_new_bias" in bname:
            label = "Old 305"
        elif "all_tier3_overnight_day2" in bname:
            label = "New 315"
        elif "all_tier3_day" in bname:
            label = "New 305"

        #Compare Rotated Energy
        plt.figure(1,figsize=(9,5))
        hist,bin_edges = np.histogram(rotEnergyCut, bins=140, range=(200,2000))
        hist = (hist*1.0)/np.sum(hist)
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        
        fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                    bin_centers, fit_width=170)
        res  = (fitp[2]/fitp[1])*100
        labelR = label + r" ($\sigma$/E = %.2f $\%%$) " % res
        plt.step(bin_centers, hist, where='post', linewidth=2.0, label=labelR)
        plt.ylabel("Counts",fontsize=16)
        plt.xlabel("Rotated Energy [keV]",fontsize=16)
        plt.title("Rotated Energy Comparison", fontsize=16)
        plt.xlim(300,1400)
        plt.legend()
        

        #Compare Charge Energy
        plt.figure(2,figsize=(9,5))
        hist,bin_edges = np.histogram(chargeEnergyCut, bins=140, range=(200,2000))
        hist = (hist*1.0)/np.sum(hist)
        fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                    bin_centers, fit_width=170)
        res  = (fitp[2]/fitp[1])*100
        labelC = label + r" ($\sigma$/E = %.2f $\%%$) " % res
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        plt.step(bin_centers, hist, where='post', linewidth=2.0, label=labelC)
        plt.ylabel("Counts",fontsize=16)
        plt.xlabel("Charge Energy [keV]",fontsize=16)
        plt.title("Charge Energy Comparison", fontsize=16)
        plt.xlim(300,1400)
        plt.legend()
        
        #Compare Light Energy
        plt.figure(3,figsize=(9,5))
        hist,bin_edges = np.histogram(lightEnergyCut, bins=100, range=(200,2000))
        hist = (hist*1.0)/np.sum(hist)
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        plt.step(bin_centers, hist, where='post', linewidth=2.0, label=label)
        plt.ylabel("Counts",fontsize=16)
        plt.xlabel("Light Energy [keV]",fontsize=16)
        plt.title("Light Energy Comparison", fontsize=16)
        plt.legend()
    
    plt.figure(1)
    plt.savefig("./plots/rotated_comparison.pdf")
    plt.figure(2)
    plt.savefig("./plots/charge_comparison.pdf")
    plt.figure(3)
    plt.savefig("./plots/light_comparison.pdf")
    raw_input()       

if __name__ == "__main__":


    file_list = ["~/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v3_12_6_2017.root",
                 "~/2018_01_26_SiPM_Run2/full_cell_overnight_day_2/tier3_added/all_tier3_overnight_day2_315bias_v1.root",
                 "~/2018_01_26_SiPM_Run2/full_cell_day_runs/tier3_added/all_tier3_day1_305bias_v2.root"]
    process_files(file_list)



