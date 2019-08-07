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
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def get_dcmd(ch):
    draw_array = []
    if ch == "All":
        draw_array.append("SignalEnergy")
    else:
        draw_array.append("energy1_pz[%i]" % ch)
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def process_file(file_list):
    tree = ROOT.TChain("tree")
    run_tree = ROOT.TChain("run_tree")
    for filename in file_list:
        tree.Add(filename)
        run_tree.Add(filename)
    tree.SetEstimate(tree.GetEntries())

    #Speed things up by setting on and off branches
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("SignalEnergy",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("nXsignals",1)
    tree.SetBranchStatus("nYsignals",1)
    #tree.SetBranchStatus("is_bad",1)
    #tree.SetBranchStatus("is_pulser",1)
    tree.SetBranchStatus("multiplicity",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("energy",1)
    tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("lightEnergy",1)
    tree.SetBranchStatus("calibration",1)
    tree.SetBranchStatus("energy1_pz",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)

    min_time  = struck_analysis_cuts_sipms.get_min_time(run_tree)
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    channel_map            = struck_analysis_parameters.channel_map 
    calibration            = struck_analysis_parameters.calibration_values
    
    cal_file = file("new_calibrations.txt","w")

    print min_time

    for i,ch in enumerate(charge_channels_to_use):
        plt.clf()
        
        #if  channel_map[i] != "X18": continue

        if ch==0:
            cal_file.write("calibration_values[%i] = %f # +/- None %s\n" % (i, calibration[i], channel_map[i]))
            continue
        
        selectcmd = struck_analysis_cuts_sipms.get_chcal_cut(ch,min_time)
        drawcmd,nvals   = get_dcmd(i)
        print "Draw CMD",  drawcmd
        print "Select CMD",selectcmd
        
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        channelEnergy =  np.array([tree.GetVal(0)[j] for j in xrange(n)])   
        driftTime      =  np.array([tree.GetVal(1)[j] for j in xrange(n)])

        channelEnergy = struck_analysis_cuts_sipms.PurityCorrection(driftTime, channelEnergy, min_time)

        chHist,bin_edges = np.histogram(channelEnergy, bins=100, range=(200,1200))
        
        #if channel_map[i] == "Y14":
        #    chHist,bin_edges = np.histogram(channelEnergy, bins=130, range=(200,1200))

        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
     
        fitx, fitp, fit_cov, isFail, full_fit, gaus, exp = FitPeakPy.FitPeak(chHist, np.sqrt(chHist), bin_centers)#, peak_guess=533)
        #fitx, fitp, fit_cov, isFail, full_fit, gaus, exp = FitPeakPy.FitPeakTest(chHist, np.sqrt(chHist), bin_centers,  peak_guess=510)

        plt.title("Channel %s" % channel_map[i], fontsize=14)
        plt.xlabel("Energy[keV]", fontsize=15)
        plt.ylabel("Counts/%.2f keV" % np.diff(bin_edges)[0], fontsize=15)
        plt.errorbar(bin_centers, chHist, yerr=np.sqrt(chHist),marker='o', linestyle='None', c='k')
        
        print 570., fitp[1], calibration[i]
        print "New Calibration for %s: %.4f" % (channel_map[i], (570./fitp[1])*calibration[i])
        
        plt.plot(fitx, full_fit, c='r')
        plt.plot(fitx, gaus, c='b')
        plt.plot(fitx, exp, c='g')
        
        #Get Current Calibration from Tree not script

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
    selectcmd = struck_analysis_cuts_sipms.get_fullcal_cut(min_time)
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    channelEnergy  =  np.array([tree.GetVal(0)[j] for j in xrange(n)])
    driftTime      =  np.array([tree.GetVal(1)[j] for j in xrange(n)])
    channelEnergy = struck_analysis_cuts_sipms.PurityCorrection(driftTime, channelEnergy, min_time)

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
        file_list   = ["all_tier3_overnight_day2_315bias_v3.root",
                       "~/2018_01_26_SiPM_Run2/full_cell_day_runs/tier3_added/all_tier3_day1_305bias_v3.root",
                       "~/2018_01_26_SiPM_Run2/full_cell_day_runs_2/tier3_added/all_tier3_day2_305bias_v3.root"]
        #file_list   = ["/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2.root"]
        file_list    = ["/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2_newgains.root"]
        file_list    = ["/home/teststand/24th_LXe/tier3_added/tier3_added_24th_dn5_dn6_newgains.root"]
    else:
        file_list = sys.argv[1:]

    print "Using ", file_list
    process_file(file_list)

