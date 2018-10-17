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
    draw_array.append("SignalEnergy")
    draw_array.append("SignalEnergyLight")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd

def process_file(filename):
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())
    
    bname = os.path.basename(filename)
    bname = bname.replace(".root", "")

    runtree = tfile.Get("run_tree")
    runtree.SetEstimate(runtree.GetEntries())
    runtree.Draw("file_start_time","","goff")
    n = runtree.GetSelectedRows()
    start_times = np.array([runtree.GetVal(0)[i] for i in xrange(n)])
    min_time = np.min(start_times)
    #print len(start_times), np.min(start_times), np.max(start_times)
    #raw_input()

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

    selectcmd = struck_analysis_cuts_sipms.get_std_cut(min_time)
    drawcmd   = get_dcmd()
 
    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    
    chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy =   np.array([tree.GetVal(1)[i] for i in xrange(n)])

    lightCal = struck_analysis_cuts_sipms.light_cal(min_time)

    plt.figure(figsize=(11,7))
    ymax = 10000
    H = plt.hist2d(chargeEnergy, lightEnergy, bins=[100,100], range=[[200,1200],[0,ymax]], 
                   norm=colors.LogNorm(vmin=1,vmax=100))
    

    diagx = np.arange(np.min(chargeEnergy), np.max(chargeEnergy))
    chargeEnergyCut, lightEnergyCut, diag_parms = struck_analysis_cuts_sipms.diag_cut(chargeEnergy,
                                                                                      lightEnergy, min_time)

    plt.plot(diagx, diag_parms[0]*diagx + diag_parms[1], linestyle='--', c='r', linewidth=7.0)
    plt.plot(diagx, diag_parms[2]*diagx + diag_parms[3], linestyle='--',  c='r',  linewidth=7.0)
    cb = plt.colorbar()
    cb.set_label("Counts", fontsize=15)
    plt.title("Light vs Charge SiPM Run", fontsize=16)
    plt.xlabel("Charge Energy [keV]", fontsize=15)
    plt.ylabel("Light Energy [ADC]", fontsize=15)
    plt.savefig("./plots/light_vs_charge_%s.pdf" % bname)
    plt.show()
    raw_input("PAUSE")    
    plt.clf()

    H = plt.hist2d(chargeEnergyCut, lightEnergyCut, bins=[100,100], range=[[200,1200],[0,ymax]],
                   norm=colors.LogNorm(vmin=1,vmax=100))
    cb = plt.colorbar()
    cb.set_label("Counts", fontsize=15)
    plt.title("Light vs Charge SiPM Run", fontsize=16)
    plt.xlabel("Charge Energy [keV]", fontsize=15)
    plt.ylabel("Light Energy [ADC]", fontsize=15)
    plt.savefig("./plots/light_vs_charge_diagcut_%s.pdf" % bname)
    raw_input("PAUSE")
    plt.clf()


    theta_list = np.arange(0.0,0.5, 0.02)
    min_theta_nocut = ScanAngles(chargeEnergy, lightEnergy*lightCal, theta_list, "noDiag_%s" % bname)
    theta_list = [0.0, min_theta_nocut, np.max(theta_list)]
    CompareAngles(chargeEnergy, lightEnergy*lightCal, theta_list, 'compare_noDiag_%s' % bname)
    raw_input()

    theta_list = np.arange(0.0,0.5, 0.02)
    min_theta_diag = ScanAngles(chargeEnergyCut, lightEnergyCut*lightCal, theta_list, "wDiag_%s" % bname)
    theta_list = [0.0, min_theta_diag, np.max(theta_list)]
    CompareAngles(chargeEnergyCut, lightEnergyCut*lightCal, theta_list, "compare_wDiag_%s" % bname)
    raw_input()
    
def CompareAngles(chargeEnergy, lightEnergy, theta_list, name):
    figtheta = plt.figure(7,figsize=(9,5))
    figtheta.clf()
    
    ymax_list = []

    for ti,theta in enumerate(theta_list):
        
        rot_energy = (chargeEnergy*np.cos(theta) + lightEnergy*np.sin(theta))
        norm = np.cos(theta) + np.sin(theta)
        rot_energy *= 1.0/norm
        #Make Histogram
        hist,bin_edges = np.histogram(rot_energy, bins=140, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

        fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                    bin_centers, fit_width=170)
        
        fitx2, fitp2, fit_cov2, isFail2, full_fit2, gaus2, linear2 = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                    bin_centers, fit_width=170, peak_guess=1050)

        res  = (fitp[2]/fitp[1])*100
        res2 = (fitp2[2]/fitp2[1])*100
        cal = (570.0/fitp[1])
        hist,bin_edges = np.histogram(rot_energy*cal, bins=120, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        plt.step(bin_centers, hist, where='post', label=r"$\sigma$/E = %.2f $\%%$, %.2f $\%%$  ($\theta$= %.2f)" % (res, res2,theta), linewidth=2.0)
        
        ymax_list.append(np.max(hist))
    
    plt.xlim(200,1500)
    plt.ylim(0,  max(ymax_list)*1.1)
    plt.legend()
    plt.savefig("./plots/theta_scan/compare_rot_angles_%s.pdf" % name)
    #raw_input()
    return

def ScanAngles(chargeEnergy, lightEnergy, theta_list, name):
    
    res_list     = []
    res_err_list = [] 
    res_list2     = []
    res_err_list2 = []
    
    pdf = PdfPages.PdfPages("./plots/theta_scan/scan_res_theta_%s.pdf" % name)

    for ti,theta in enumerate(theta_list):
        figtheta = plt.figure(3,figsize=(9,5))
        figtheta.clf()
        
        #Rotate the Energy and re-norm
        rot_energy = (chargeEnergy*np.cos(theta) + lightEnergy*np.sin(theta))
        norm = np.cos(theta) + np.sin(theta)
        rot_energy *= 1.0/norm
        
        #Make Histogram
        hist,bin_edges = np.histogram(rot_energy, bins=140, range=(200,2000))
        
        #Get Bin Centers
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
            
        #fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakLinear(hist, np.sqrt(hist), 
        #                                                                bin_centers, fit_width=170)    
        fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                         bin_centers, fit_width=170)

        #fitx2, fitp2, fit_cov2, isFail2, full_fit2, gaus2, linear2 = FitPeakPy.FitPeak(hist, np.sqrt(hist), 
        #                                                                bin_centers, fit_width=170, peak_guess=1060)
        fitx2, fitp2, fit_cov2, isFail2, full_fit2, gaus2, linear2 = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                bin_centers, fit_width=170, peak_guess=1050)
        #Calculate Resolution 
        res = 0.0
        res_err = 0.0
        #if theta < 0.5:
        print theta
        try:
            res = (fitp[2]/fitp[1])*100
            if not isFail: res_err = (fit_cov[2,2]/fitp[1])*100
            else: 
                res_err = 0.0
                res     = 0.0

            res2 = (fitp2[2]/fitp2[1])*100
            if not isFail2: res_err2 = (fit_cov2[2,2]/fitp2[1])*100
            else: 
                res2      = 0.0
                res_err2  = 0.0
        except:
            res = 0.0
            res_err = 0.0
            res2 = 0.0
            res_err2 = 0.0


        #Plot Single Spectrum
        plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist),marker='o', linestyle='None', c='k')
        plt.plot(fitx, full_fit, c='r', label=r"$\sigma$/E = %.2f %%" % (res), linewidth=2.0)
        plt.plot(fitx, gaus,     c='b')
        plt.plot(fitx, linear,   c='g', linewidth=2.0)
        
        plt.plot(fitx2, full_fit2, c='c', label=r"$\sigma$/E = %.2f %%" % (res2), linewidth=2.0)
        plt.plot(fitx2, gaus2,     c='b')
        plt.plot(fitx2, linear2,   c='g', linewidth=2.0)

        plt.legend(fontsize=18)
        plt.title("Rotated Energy (Theta = %.2f rad)" % theta, fontsize=18)
        plt.xlabel("Rotated Energy [uncal]", fontsize=18)
        plt.ylabel("Counts", fontsize=18)
        plt.xlim(300,1400)
        pdf.savefig(figtheta)

        res_list.append(res)
        res_err_list.append(res_err)
        res_list2.append(res2)
        res_err_list2.append(res_err2)

        plt.figure(4,figsize=(12,7))
        if ti==0: plt.clf()
        #Calibrate Spectrum and rebin the histogram
        #Plot each theta on top of each other
        if True: 
            cal = (570.0/fitp[1])
            hist,bin_edges = np.histogram(rot_energy*cal, bins=120, range=(200,2000))
            bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
            plt.step(bin_centers, hist, where='post', label=r"$\sigma$/E = %.2f $\%%$  ($\theta$= %.2f)" % (res,theta), linewidth=2.0)
        
        plt.title("Rotated Energy vs Theta",fontsize=18)
        plt.xlabel("Rotated Energy [keV]", fontsize=18)
        plt.ylabel("Counts", fontsize=18)
        #plt.legend(fontsize=18)
        plt.xlim(300,1400)
        plt.show()
        plt.savefig("./plots/theta_scan/all_thetas_calibrated_%s.pdf" % name)
        
    figprof = plt.figure(figsize=(9,5))
    plt.errorbar(theta_list, res_list, yerr=res_err_list, marker='o', linestyle='None',   c='r',   label='570 keV')
    plt.errorbar(theta_list, res_list2, yerr=res_err_list2, marker='o', linestyle='None', c='b',   label='1060 keV')
    
    poly_results1 = np.polyfit(theta_list, res_list, 2, w=1./np.array(res_err_list))
    plt.plot(theta_list, np.polyval(poly_results1, theta_list), linestyle='-', linewidth=3.0, c='r')
    poly_results2 = np.polyfit(theta_list, res_list2, 2,w=1./np.array(res_err_list2))
    plt.plot(theta_list, np.polyval(poly_results2, theta_list), linestyle='-', linewidth=3.0, c='b')
    
    min_theta1 = -poly_results1[1]/(2*poly_results1[0])
    min_res1    =  np.polyval(poly_results1, min_theta1)
    print "Minimum for 570 keV is at theta = %.3f with res = %.3f" % (min_theta1, min_res1)
    
    min_theta2 = -poly_results2[1]/(2*poly_results2[0])
    min_res2    =  np.polyval(poly_results2, min_theta2)
    print "Minimum for 1050 keV is at theta = %.3f with res = %.3f" % (min_theta2, min_res2)
    
    plt.axvline(min_theta1, linestyle='--', linewidth=4.0, c='r')
    plt.axvline(min_theta2, linestyle='--', linewidth=4.0, c='b')

    plt.xlabel("Theta[rad]",fontsize=18)
    plt.ylabel(r"Resolution ($\sigma$/E) [$\%$]",fontsize=18)
    plt.title("Resoltuion vs Theta Scan",fontsize=18)
    plt.ylim(2.5, 7.5)
    plt.xlim(-.02, np.max(theta_list)*1.2)
    plt.legend()
    pdf.savefig(figprof)
    pdf.close()
    
    return (min_theta1 + min_theta2)/2.0

if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        #filename  = "~/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v3_12_6_2017.root"
        filename  = "all_tier3_overnight_day2_315bias_v1.root"
        #filename  = "~/2018_01_26_SiPM_Run2/full_cell_day_runs/tier3_added/all_tier3_day1_305bias.root"
        #filename  = "~/2018_01_26_SiPM_Run2/full_cell_day_runs_2/tier3_added/all_tier3_day2_305bias.root"
    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)


