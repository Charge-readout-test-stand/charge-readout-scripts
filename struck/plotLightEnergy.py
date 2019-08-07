import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
import struck_analysis_parameters
import scipy.optimize as opt
import FitPeakPy
import struck_analysis_cuts_sipms

plt.ion()

def get_cut(rise_time_low = 0, rise_time_high=20, sig_low=200, sig_high=4000):
    selection = []
    #selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("nfound_channels==32")
    selection.append("SignalEnergy > %.2f" % sig_low)
    if sig_high < 3000: selection.append("SignalEnergy < %.2f" % sig_high)
    selection.append("nsignals==2")
    selection.append("nXsignals==1")
    selection.append("nYsignals==1")
    selection.append("(rise_time_stop95_sum-trigger_time) > %f " % rise_time_low)
    selection.append("(rise_time_stop95_sum-trigger_time) < %f " % rise_time_high)
    selection = " && ".join(selection)
    return selection

def get_dcmd(useCharge=True,useLight=True,useRise=False):
    draw_array = []
    if useCharge:draw_array.append("SignalEnergy")
    if useLight: draw_array.append("SignalEnergyLight")
    if useRise:draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def process_file(filename):
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())

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

    rise_bins     = []
    charge_peaks  = []
    rotated_peaks = []
    scint_peaks   = []

    for rise_cut in [(0,4),(4,7), (7,10), (10,13), (13,16)]:
        selectcmd       = get_cut(rise_time_low = rise_cut[0], rise_time_high=rise_cut[1])
        drawcmd,nvals   = get_dcmd(useRise=True)
        
        #rise_bins.append((rise_cut[0]+rise_cut[1])/2.0)

        print "Draw CMD",  drawcmd
        print "Select CMD",selectcmd
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
    
        chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
        lightEnergy  =  np.array([tree.GetVal(1)[i] for i in xrange(n)])
        driftTime     =  np.array([tree.GetVal(2)[i] for i in xrange(n)])
        lightCal = struck_analysis_cuts_sipms.light_cal(min_time)
        lightEnergy  *= lightCal 

        rise_bins.append(np.mean(driftTime))

        label = r'%i $\mu$s to %i $\mu$s' % (rise_cut[0], rise_cut[1])

        plt.figure(1)
        hist,bin_edges = np.histogram(chargeEnergy, bins=120, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        #plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist),marker='o', linestyle='None', label=label)
        
        fitx, fitp, fitcov, isFail, full_fit, gaus, linear =FitPeakPy.FitPeakLinear(hist, np.sqrt(hist), bin_centers)
        
        plt.figure(10)
        plt.clf()
        plt.step(bin_centers, hist, where='post', label=label, linewidth=2.0)
        plt.plot(fitx,full_fit)
        plt.plot(fitx,gaus)
        plt.plot(fitx,linear)
        
        #raw_input()

        charge_peaks.append(fitp[1])

        cal = 570.0/fitp[1]
        newCharge = cal*chargeEnergy
        hist,bin_edges = np.histogram(newCharge, bins=120, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        
        print "Fit Peak is at %.2f and res is %.2f"  % (fitp[1], fitp[2]*100.0/fitp[1])
        
        plt.figure(1)
        plt.step(bin_centers, hist, where='post', label=label, linewidth=2.0)
        plt.legend(fontsize=14)                        
        plt.title("Charge Energy vs Risetime Bin", fontsize=18)
        plt.xlabel("Charge Energy [keV]", fontsize=18)
        plt.ylabel("Counts", fontsize=18)
        plt.xlim(200,1250)
        
        #raw_input()

        #--------------------------------------------------------------------------------------------
        #Light Energy
        #--------------------------------------------------------------------------------------------
        #hist,bin_edges = np.histogram(lightEnergy, bins=100, range=(0,11000))
        hist,bin_edges = np.histogram(lightEnergy, bins=100, range=(0,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        #plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist),marker='o', linestyle='None', label=label)
        
        fitx, fitp, fitcov, isFail, full_fit, gaus, linear =FitPeakPy.FitPeakLinear(hist, np.sqrt(hist), bin_centers, 
                                                                                    fit_width=500,peak_guess=570)
        cal = 570.0/fitp[1]
        plt.figure(10)
        plt.clf()
        plt.step(bin_centers, hist, where='post', label=label, linewidth=2.0)
        plt.plot(fitx,full_fit)
        plt.plot(fitx,gaus)
        plt.plot(fitx,linear)
        #raw_input()
        scint_peaks.append(fitp[1])

        selectcmd       = get_cut(rise_time_low = rise_cut[0], rise_time_high=rise_cut[1], sig_low=470, sig_high=650)
        drawcmd,nvals   = get_dcmd(useCharge=False)
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        lightEnergyCut  =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
        lightEnergyCut *= lightCal

        hist_cut,bin_edges_cut = np.histogram(lightEnergyCut, bins=100, range=(0,2000))
        bin_centers_cut = bin_edges_cut[:-1] + np.diff(bin_edges_cut)/2.0
        plt.step(bin_centers_cut, hist_cut, where='post', label=label, linewidth=2.0)

        plt.figure(2)
        cal = 570.0/fitp[1]
        newLight = cal*lightEnergy
        hist,bin_edges = np.histogram(newLight, bins=120, range=(0,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

        plt.step(bin_centers, hist, where='post', label=label, linewidth=2.0)
        plt.legend(fontsize=18)
        plt.title("Light Energy vs Risetime Bin" , fontsize=18)
        plt.xlabel("Light Energy [uncal]", fontsize=18)
        plt.ylabel("Counts", fontsize=18)

        plt.figure(3)
        hist,bin_edges = np.histogram(chargeEnergy*np.cos(0.05) + lightEnergy*np.sin(0.05), bins=120, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        #plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist),marker='o', linestyle='None', label=label)
        
        fitx, fitp, fitcov, isFail, full_fit, gaus, linear =FitPeakPy.FitPeakLinear(hist, np.sqrt(hist), bin_centers)
        cal = 570.0/fitp[1]
        rotEnergy = cal*(chargeEnergy*np.cos(0.05) + lightEnergy*np.sin(0.05))
        hist,bin_edges = np.histogram(rotEnergy, bins=120, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        res = (fitp[2]/fitp[1])*100.0
        #label += r"(%.2f $\%%$)" % res

        rotated_peaks.append(fitp[1])

        plt.step(bin_centers, hist, where='post', label=label, linewidth=2.0)
        #plt.plot(fitx, full_fit)
        plt.legend(fontsize=18)
        plt.title("Rotated Energy vs Risetime Bin" , fontsize=18)
        plt.xlabel("Rotated Energy [keV??]", fontsize=18)
        plt.ylabel("Counts", fontsize=18)
        plt.xlim(200,1550)
    
    plt.figure(1)
    plt.savefig("./plots/chargeEnergy_vs_risebin.pdf")
    plt.figure(2)
    plt.savefig("./plots/lightEnergy_vs_risebin.pdf")
    plt.figure(3)
    plt.savefig("./plots/rotatedEnergy_vs_risebin.pdf")
    raw_input("PAUSE")

    selectcmd       = get_cut()
    drawcmd,nvals   = get_dcmd(useRise=True)

    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()

    chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy  =  np.array([tree.GetVal(1)[i] for i in xrange(n)])
    driftTime     =  np.array([tree.GetVal(2)[i] for i in xrange(n)]) 
    lightEnergyCut *= lightCal

    rotEnergy = chargeEnergy*np.cos(0.05) + lightEnergy*np.sin(0.05)   

    plt.figure(4)
    dtmax = 20
    max_counts = 500
    dbins = 50
    H = plt.hist2d(driftTime, chargeEnergy, bins=[dbins,100], range=[[0,dtmax],[0,1500]],
                   norm=colors.LogNorm(vmin=1,vmax=max_counts))
    
    plt.plot(rise_bins, charge_peaks, marker='o', ms=6.0, c='k')
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=18)
    plt.ylabel("Charge Energy [uncal]",fontsize=18)
    plt.title("Charge Energy vs Drift Time",fontsize=18)
    plt.ylim(300,1400)
    plt.savefig("./plots/chargeEnergy_vs_driftTime_withFit.pdf")
 
    plt.figure(5)
    dtmax = 20
    max_counts = 500
    dbins = 50
    H = plt.hist2d(driftTime, rotEnergy, bins=[dbins,100], range=[[0,dtmax],[0,1500]],
                   norm=colors.LogNorm(vmin=1,vmax=max_counts))
    plt.plot(rise_bins, rotated_peaks, marker='o', ms=6.0, c='k')
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=18)
    plt.ylabel("Rotated Energy [uncal]",fontsize=18)
    plt.title("Rotated Energy vs Drift Time",fontsize=18)
    plt.ylim(300,1600)
    plt.savefig("./plots/rotatedEnergy_vs_driftTime_withFit.pdf")
    
    plt.figure(6)
    dtmax = 20
    max_counts = 500
    dbins = 50
    H = plt.hist2d(driftTime, lightEnergy, bins=[dbins,100], range=[[0,dtmax],[0,1200]],
                   norm=colors.LogNorm(vmin=1,vmax=max_counts))
    plt.plot(rise_bins, scint_peaks, marker='o', ms=6.0, c='k')
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=18)
    plt.ylabel("Light Energy [uncal]",fontsize=18)
    plt.title("Light Energy vs Drift Time",fontsize=18)
    #plt.ylim(700,3000)
    plt.savefig("./plots/scintEnergy_vs_driftTime_withFit.pdf")
    
    plt.figure(7)
    scint_peaks = np.array(scint_peaks)
    scint_peaks *= 1/np.max(scint_peaks)
    mcorr = (scint_peaks[-1] - scint_peaks[0])/(rise_bins[-1] - rise_bins[0])
    bcorr = scint_peaks[0] - mcorr*rise_bins[0]
    correction = 1/(driftTime*mcorr + bcorr)
    #correction = 1.0
    plt.clf()
    print "Slope",mcorr
    print "Y-inter",bcorr
    print "Correction is", correction
    lightEnergyCorrected = lightEnergy*correction
    
    H = plt.hist2d(driftTime, lightEnergyCorrected, bins=[dbins,100], range=[[0,dtmax],[0,11000]],
                   norm=colors.LogNorm(vmin=1,vmax=max_counts))
    plt.xlabel(r"Drift Time [$\mu$s]",fontsize=18)
    plt.ylabel("Light Energy [uncal]",fontsize=18)
    plt.title("Corrected Light Energy vs Drift Time",fontsize=18)
    plt.savefig("./plots/scintEnergy_vs_driftTime_withCorrection.pdf")
    
    plt.figure(8)
    hist,bin_edges = np.histogram(lightEnergyCorrected, bins=100, range=(0,11000))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

    plt.step(bin_centers, hist, where='post', label=label, linewidth=2.0)
    plt.savefig("./plots/lightEnergyCorrected_full.pdf")
    plt.xlim(1,10500)
    plt.title("Corrected Light Energy (Full Detector)" , fontsize=18)
    plt.xlabel("Corrected Light Energy [uncal]", fontsize=18)
    plt.ylabel("Counts", fontsize=18)

    drift_cut = np.logical_and(driftTime > 7.0, driftTime < 13.0)
    plt.figure(9)
    H = plt.hist2d(chargeEnergy[drift_cut], lightEnergyCorrected[drift_cut], 
    #H = plt.hist2d(chargeEnergy, lightEnergyCorrected,
                   bins=[100,100], range=[[300,1300],[0,11000]],
                   norm=colors.LogNorm(vmin=1,vmax=200))
    cb = plt.colorbar()
    cb.set_label("Counts", fontsize=15)
    plt.title("Corrected Light vs Charge SiPM Run", fontsize=18)
    plt.xlabel("Charge Energy [keV]", fontsize=18)
    plt.ylabel("Light Energy [ADC]", fontsize=18)
    plt.savefig("./plots/correctedlight_vs_charge.pdf")

    #drift_cut = np.logical_and(driftTime > 7.0, driftTime < 13.0)
    #drift_cut = np.logical_and(driftTime > 10.0, driftTime < 13.0)
    #plt.clf()
    color_list = ['b','r']
    for ci, theta in enumerate([0.0, 0.08]): #np.arange(0,.2, 0.02):
        plt.figure(11)
        rotEnergyLCorr = lightEnergyCorrected[drift_cut]*np.sin(theta) + chargeEnergy[drift_cut]*np.cos(theta)
        norm = np.cos(theta) + np.sin(theta)
        print "Norm factor???", norm
        rotEnergyLCorr *= 1.0/norm
        hist,bin_edges = np.histogram(rotEnergyLCorr, bins=120, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

        fitx, fitp, fitcov, isFail, full_fit, gaus, linear =FitPeakPy.FitPeakLinear(hist, np.sqrt(hist), bin_centers)
        cal = 570.0/fitp[1]
        rotEnergyLCorr *= cal
        
        hist,bin_edges = np.histogram(rotEnergyLCorr, bins=110, range=(200,1400))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        fitx, fitp, fitcov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakLinear(hist, np.sqrt(hist), bin_centers, fit_width=120)
        #fitx, fitp, fitcov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeak(hist, np.sqrt(hist), bin_centers, fit_width=120)

        fitx2, fitp2, fitcov2, isFail2, full_fit2, gaus2, linear2 = FitPeakPy.FitPeak(hist, np.sqrt(hist), bin_centers, 
                                                                                      fit_width=170, peak_guess=1100)

        res  = 100*fitp[2]/fitp[1]
        res2 = 100*fitp2[2]/fitp2[1]
        print "Resolution @ 570 is  ", res, " for theta ", theta
        print "Resolution @ 1050 is ", res2," for theta ", theta

        plt.step(bin_centers, hist, where='post', linewidth=2.0, c=color_list[ci], label=r'$\theta$ = %.2f (%.2f $\%%$)' % (theta, res))
        plt.xlabel("Rotated Energy [keV]", fontsize=18)
        plt.ylabel("Counts", fontsize=18)
        plt.title("Rotated Energy with Light Correction")

        plt.figure(12)
        plt.clf()
        plt.step(bin_centers, hist, where='post', linewidth=2.0)
        plt.plot(fitx,full_fit, linewidth=2)
        plt.plot(fitx,gaus, label='570keV Peak (%.2f %%)' % res, linewidth=2)
        plt.plot(fitx,linear,linewidth=2)
        plt.plot(fitx2,full_fit2, linewidth=2)
        plt.plot(fitx2,gaus2,label='1050keV Peak (%.2f %%)' % res2,linewidth=2)
        plt.plot(fitx2,linear2,linewidth=2)

        
        plt.title("Rotated Energy for (Theta %.2f)" % theta, fontsize=18)
        plt.xlabel("Rotated Energy [keV]")
        plt.ylabel("Counts")
        plt.legend(fontsize=18)
        plt.savefig("./plots/rotate_fit_with_correction_theta%.2f_both_peaks.pdf" % theta)
        raw_input()

    plt.figure(11)
    plt.legend(fontsize=17)
    plt.savefig("./plots/gg_rotated_res_fit_with_correction.pdf")
    plt.savefig("./plots/gg_rotated_res_fit_with_correction.png")
    raw_input()


if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        #filename  = "overnight_new_bias_tier3_all_v3_12_6_2017.root"
        #filename  = "all_tier3_overnight_day2_315bias.root"
        filename   = "/home/teststand/22nd_LXe/overnight_4_17_2019/tier3_added/tier3_22nd_overnight_4_17_2019_v1.root"
    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)

