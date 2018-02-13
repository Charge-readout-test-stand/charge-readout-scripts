import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os,sys
import struck_analysis_parameters
import struck_analysis_cuts_sipms
import scipy.optimize as opt
import FitPeakPy
plt.ion()
plt.figure(1)

def get_dcmd_full():
    draw_array = []
    draw_array.append("SignalEnergy")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def get_dcmd(ch):
    draw_array = []
    if ch == "All":
        draw_array.append("SignalEnergy")
    else:
        draw_array.append("energy1_pz[%i]" % ch)
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def process_file(file_list):
    tree = ROOT.TChain("tree")
    for filename in file_list:
        tree.Add(filename)
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
    tree.SetBranchStatus("calibration",1)
    tree.SetBranchStatus("energy1_pz",1)
    #tree.SetBranchStatus("trigger_time",1)
    #tree.SetBranchStatus("rise_time_stop95_sum",1)

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    channel_map            = struck_analysis_parameters.channel_map 
    calibration            = struck_analysis_parameters.calibration_values
    
    cal_file = file("new_calibrations.txt","w")

    for i,ch in enumerate(charge_channels_to_use):
        plt.clf()

        if ch==0:
            cal_file.write("calibration_values[%i] = %f # +/- None %s\n" % (i, calibration[i], channel_map[i]))
            continue
        
        selectcmd = struck_analysis_cuts_sipms.get_chcal_cut(ch)
        drawcmd,nvals   = get_dcmd(i)
        print "Draw CMD",  drawcmd
        print "Select CMD",selectcmd
        
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        channelEnergy =  np.array([tree.GetVal(0)[j] for j in xrange(n)])   
        
        chHist,bin_edges = np.histogram(channelEnergy, bins=100, range=(200,1200))
        
        if channel_map[i] == "Y14":
            chHist,bin_edges = np.histogram(channelEnergy, bins=130, range=(200,1200))

        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
     
        fitx, fitp, fit_cov, isFail, full_fit, gaus, exp = FitPeakPy.FitPeak(chHist, np.sqrt(chHist), bin_centers)

        plt.title("Channel %s" % channel_map[i], fontsize=14)
        plt.xlabel("Energy[keV]", fontsize=15)
        plt.ylabel("Counts/%.2f keV" % np.diff(bin_edges)[0], fontsize=15)
        plt.errorbar(bin_centers, chHist, yerr=np.sqrt(chHist),marker='o', linestyle='None', c='k')
        
        print "New Calibration for %s: %.4f" % (channel_map[i], (570./fitp[1])*calibration[i])
        
        plt.plot(fitx, full_fit, c='r')
        plt.plot(fitx, gaus, c='b')
        plt.plot(fitx, exp, c='g')
        
        #print fit_cov, np.sum(np.isinf(fit_cov))
        if np.sum(np.isinf(fit_cov)) < 0.5:
            fit_err = 570./(fitp[1]*fitp[1])*fit_cov[1,1]
            cal_file.write("calibration_values[%i] = %f # +/- %f %s \n" % (i, (calibration[i]*(570./fitp[1])), fit_err, channel_map[i]))
        else:
            #Failed the fit
            cal_file.write("calibration_values[%i] = %f # +/- %f %s \n" % (i, calibration[i], 0.0, channel_map[i]))

        plt.savefig("./plots/cal/calibration_fit_ch%s.pdf" % channel_map[i])
        
        #if channel_map[i]=="Y14": raw_input()
        raw_input()
    cal_file.close()

    #Now do for the Signal Energy
    drawcmd,nvals   = get_dcmd_full()
    selectcmd = struck_analysis_cuts_sipms.get_fullcal_cut()
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    channelEnergy =  np.array([tree.GetVal(0)[j] for j in xrange(n)])
    chHist,bin_edges = np.histogram(channelEnergy, bins=120, range=(200,1200))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    fitx, fitp, fit_cov, isFail, full_fit, gaus, exp = FitPeakPy.FitPeak(chHist, np.sqrt(chHist), bin_centers)
    plt.title("Signal Energy", fontsize=14)
    plt.xlabel("Energy[keV]", fontsize=15)
    plt.ylabel("Counts/%.2f keV" % np.diff(bin_edges)[0], fontsize=15)
    plt.errorbar(bin_centers, chHist, yerr=np.sqrt(chHist),marker='o', linestyle='None', c='k')
    plt.plot(fitx, full_fit, c='r')
    res = (fitp[2]/fitp[1])*100
    plt.plot(fitx, gaus, c='b', label="%.2f %% \n %.2f keV" % (res, fitp[1]))
    plt.plot(fitx, exp, c='g')
    plt.legend()
    plt.savefig("./plots/cal/full_fit_SignalEnergy.pdf")
    raw_input()

if __name__ == "__main__":

    file_list = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        #filename  = "overnight_new_bias_tier3_all_v3_12_6_2017.root"
        file_list   = ["all_tier3_overnight_day2_315bias.root",
                       "~/2018_01_26_SiPM_Run2/full_cell_day_runs/tier3_added/all_tier3_day1_305bias.root",
                       "~/2018_01_26_SiPM_Run2/full_cell_day_runs_2/tier3_added/all_tier3_day2_305bias.root"]
    else:
        file_list = sys.argv[1:]

    print "Using ", file_list
    process_file(file_list)

