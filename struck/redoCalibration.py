import ROOT
import numpy as np
import matplotlib.pyplot as plt
import os,sys
import struck_analysis_parameters
import scipy.optimize as opt
plt.ion()
plt.figure(1)

def get_cut(ch):
    selection = []
    selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("SignalEnergy > 100")
    selection.append("nsignals==1")
    selection.append("(nXsignals==1 || nYsignals==1)")
    selection.append("channel==%i" % ch)
    selection = " && ".join(selection)
    return selection

def get_cut_full():
    selection = []
    selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("SignalEnergy > 100")
    selection.append("nsignals==2")
    selection.append("(nXsignals==1 && nYsignals==1)")
    selection = " && ".join(selection)
    return selection

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

def ffn(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3 
    return gaus + exp

def ffn_sep(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3
    return gaus , exp

def FitPeak(hist_counts, hist_errors, bin_centers):
    de = 180 # Fit width
    peak_pos = 570.0 #bin_centers[np.argmax(hist_counts)]
    
    print "Peak Guess", peak_pos

    #Only fit the bins within a range de of the peak
    fit_min = peak_pos-de
    fit_max = peak_pos+de
    fpts = np.logical_and( bin_centers > peak_pos-de, bin_centers < peak_pos+de )
    
    exp_decay_guess  = np.log(fit_max/fit_min)/(2*de)
    exp_height_guess = (hist_counts[fpts])[0]*np.exp(fit_min*exp_decay_guess) 
    spars = [1e2, peak_pos, 30.0, exp_height_guess, exp_decay_guess, 0.] #Initial guess for fitter
    
    fail = False

    #Perform the fit
    try:
        bp, bcov = opt.curve_fit(ffn, bin_centers[fpts], hist_counts[fpts], p0=spars, sigma=hist_errors[fpts])
    except RuntimeError:
        print "**********************Did not work*******************************"
        fail = True
        bp = spars
        bcov = np.eye(len(bp))
    
    #Get the x values for evaluating the function
    xx = np.linspace( bin_centers[fpts][0], bin_centers[fpts][-1], 1e3 )
    
    print ""
    print "-------Fit Results----------"
    print "Mean:  %.2f" % bp[1]
    print "Sigma: %.2f" % bp[2]
    #print bp
    print "----------------------------"
    print

    return xx, bp, bcov, fail


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
    tree.SetBranchStatus("calibration",1)
    tree.SetBranchStatus("energy1_pz",1)
    #tree.SetBranchStatus("trigger_time",1)
    #tree.SetBranchStatus("rise_time_stop95_sum",1)

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    channel_map            = struck_analysis_parameters.channel_map 
    calibration            = struck_analysis_parameters.calibration_values
    
    cal_file = file("new_calibrations.txt","w")

    for i,ch in enumerate(charge_channels_to_use):
        break
        plt.clf()

        if ch==0:
            cal_file.write("calibration_values[%i] = %f # +/- None %s\n" % (i, calibration[i], channel_map[i]))
            continue
        selectcmd = get_cut(i)
        drawcmd,nvals   = get_dcmd(i)
        print "Draw CMD",  drawcmd
        print "Select CMD",selectcmd
        
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        channelEnergy =  np.array([tree.GetVal(0)[j] for j in xrange(n)])   
        
        chHist,bin_edges = np.histogram(channelEnergy, bins=120, range=(200,1200))
        
        if channel_map[i] == "Y14":
            chHist,bin_edges = np.histogram(channelEnergy, bins=130, range=(200,1200))

        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
     
        fitx, fitp, fit_cov, isFail = FitPeak(chHist, np.sqrt(chHist), bin_centers)

        plt.title("Channel %s" % channel_map[i], fontsize=14)
        plt.xlabel("Energy[keV]", fontsize=15)
        plt.ylabel("Counts/%.2f keV" % np.diff(bin_edges)[0], fontsize=15)
        plt.errorbar(bin_centers, chHist, yerr=np.sqrt(chHist),marker='o', linestyle='None', c='k')
        gaus,exp = ffn_sep(fitx, fitp[0], fitp[1], fitp[2], fitp[3], fitp[4], fitp[5])
        full_fit = ffn(fitx, fitp[0], fitp[1], fitp[2], fitp[3], fitp[4], fitp[5])
        
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

        plt.savefig("./plots/calibration_fit_ch%s.pdf" % channel_map[i])
        
        #if channel_map[i]=="Y14": raw_input()
    cal_file.close()

    #Now do for the Signal Energy
    drawcmd,nvals   = get_dcmd_full()
    selectcmd = get_cut_full()
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    channelEnergy =  np.array([tree.GetVal(0)[j] for j in xrange(n)])
    chHist,bin_edges = np.histogram(channelEnergy, bins=120, range=(200,1200))
    bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
    fitx, fitp, fit_cov, isFail = FitPeak(chHist, np.sqrt(chHist), bin_centers)
    plt.title("Signal Energy", fontsize=14)
    plt.xlabel("Energy[keV]", fontsize=15)
    plt.ylabel("Counts/%.2f keV" % np.diff(bin_edges)[0], fontsize=15)

    full_fit = ffn(fitx, fitp[0], fitp[1], fitp[2], fitp[3], fitp[4], fitp[5])
    plt.errorbar(bin_centers, chHist, yerr=np.sqrt(chHist),marker='o', linestyle='None', c='k')
    plt.plot(fitx, full_fit, c='r')
    res = (fitp[2]/fitp[1])*100
    gaus,exp = ffn_sep(fitx, fitp[0], fitp[1], fitp[2], fitp[3], fitp[4], fitp[5])
    plt.plot(fitx, gaus, c='b', label="%.2f %% \n %.2f keV" % (res, fitp[1]))
    plt.plot(fitx, exp, c='g')
    plt.legend()
    plt.savefig("./plots/full_fit_SignalEnergy.pdf")
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

