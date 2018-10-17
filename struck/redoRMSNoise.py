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
    selection.append("nfound_channels==32") #cut the dead channel events
    #selection.append("nfound_channels==30") #cut the dead channel events 
    #selection.append("channel==%i" % ch)
    selection.append("file_start_time > 0.1")
    selection = " && ".join(selection)
    return selection

def get_dcmd(ch):
    draw_array = []
    if struck_analysis_parameters.charge_channels_to_use[ch]:
        draw_array.append("baseline_rms[%i]" % ch)
    else:
        draw_array.append("baseline_rms_filter[%i]" % ch)
    draw_array.append("(file_start_time + time_stamp_msec*1.e-3)")
    #draw_array.append("baseline_rms[%i]" % ch)
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

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


def process_file(file_list):
    tree = ROOT.TChain("tree")
    for filename in file_list:
        tree.Add(filename)
        tree.SetEstimate(tree.GetEntries())
    tree.SetEstimate(tree.GetEntries())

    #Speed things up by setting on and off branches
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("calibration",1)
    tree.SetBranchStatus("baseline_rms_filter",1)
    tree.SetBranchStatus("baseline_rms",1)
    tree.SetBranchStatus("file_start_time",1)
    tree.SetBranchStatus("time_stamp_msec",1)

    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    channel_map            = struck_analysis_parameters.channel_map 
    calibration            = struck_analysis_parameters.calibration_values
    
    cal_file = file("new_noise.txt","w")

    for i,ch in enumerate(charge_channels_to_use):
    #for i in [14,15]:
        plt.clf()

        selectcmd = get_cut(i)
        drawcmd,nvals   = get_dcmd(i)
        print "Draw CMD",  drawcmd
        print "Select CMD",selectcmd
        
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        #tree.SetEstimate(n+1)
        channelRMS  =   np.array([tree.GetVal(0)[j] for j in xrange(n)])   
        channelTime =   np.array([tree.GetVal(1)[j] for j in xrange(n)])

        print tree.GetEntries(), n, len(channelRMS), len(channelTime)
    
        plt.figure(2)
        plt.clf()
        if charge_channels_to_use[i]:
            chHist,bin_edges = np.histogram(channelRMS, bins=1000, range=(2,50))
        else:
            chHist,bin_edges = np.histogram(channelRMS, bins=1000, range=(0,100))
        #chHist *= (2000./2**14) #convert from ADC to mV

        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
     
        plt.title("Channel %s" % channel_map[i], fontsize=14)
        plt.xlabel("RMS Noise [mV]", fontsize=15)
        plt.ylabel("Counts/%.2f mV" % np.diff(bin_edges)[0], fontsize=15)
        #plt.errorbar(bin_centers*(2000.0)/(2**14), chHist, yerr=np.sqrt(chHist),marker='o', linestyle='None', c='k', 
        #             label='RMS Noise = %.4f ADC' % np.mean(channelRMS))
        plt.errorbar(bin_centers, chHist, yerr=np.sqrt(chHist),marker='o', linestyle='None', c='k', 
                     label='RMS Noise = %.4f ADC' % np.mean(channelRMS))
        
        #plt.yscale('log')
        #plt.xscale('log')

        noise_mean = np.mean(channelRMS)
        noise_mean_sigma = np.std(channelRMS)
        noise_mean_mV = noise_mean*(2000./2**14)
        noise_mean_keV = noise_mean*calibration[i]
        #print "Noise in ADC:%.4f, mV:%.4f, keV:%.4f" % (noise_mean, noise_mean_mV, noise_mean_keV) 
        print "Noise in ADC with Sigma %.4f and %.4f" % (noise_mean, noise_mean_sigma)
        cal_file.write("rms_keV[%i] = %f*calibration_values[%i] \n" % (i,noise_mean,i))
        cal_file.write("rms_keV_sigma[%i] = %f*calibration_values[%i] \n" % (i,noise_mean_sigma,i))

        plt.legend()
        plt.savefig("./plots/noise/rms_noise_ch%s.pdf" % channel_map[i])
        #plt.yscale('log', nonposy='clip')
        
        plt.figure(1)
        plt.clf()
        channelRMS *= (2000./2**14)
        plt.title("RMS Noise on Ch %s" % channel_map[i])
        plt.xlabel("Time of Event Posix [s]")
        plt.ylabel("RMS Noise [mV]")
        ylow  = noise_mean_mV - 2.5*np.std(channelRMS)
        yhigh = noise_mean_mV + 2.5*np.std(channelRMS) 
        xlow  = min(channelTime)
        xhigh = max(channelTime)
        #plt.plot(channelTime, channelRMS, marker='o', c='r', linestyle='None')
        H = plt.hist2d(channelTime, channelRMS, bins=[100,100], range=[[xlow,xhigh],[ylow,yhigh]])
        plt.colorbar()
        print "RMS low and high is", noise_mean, np.std(channelRMS), ylow,yhigh
        print "Time low and high", xlow,xhigh
        plt.ylim(ylow,yhigh)
        plt.savefig("./plots/noise/rms_noise_vs_time_ch%s.pdf" % channel_map[i])
        
        raw_input()
    cal_file.close()



if __name__ == "__main__":

    file_list = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        #filename =  "overnight_new_bias_tier3_all_v3_12_6_2017.root"
        file_list   = ["all_tier3_overnight_day2_315bias_v1.root",
                       "~/2018_01_26_SiPM_Run2/full_cell_day_runs/tier3_added/all_tier3_day1_305bias.root",
                       "~/2018_01_26_SiPM_Run2/full_cell_day_runs_2/tier3_added/all_tier3_day2_305bias.root"]
    else:
        file_list = sys.argv[1:]

    print "Using ", file_list
    process_file(file_list)

