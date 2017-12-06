import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
import struck_analysis_parameters
import scipy.optimize as opt

plt.ion()
plt.figure(1)

def get_cut():
    selection = []
    selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("SignalEnergy > 200")
    selection.append("nsignals==2")
    selection.append("nXsignals==1")
    selection.append("nYsignals==1")
    selection.append("(rise_time_stop95_sum-trigger_time) > 10")
    selection.append("(rise_time_stop95_sum-trigger_time) < 15")
    selection = " && ".join(selection)
    return selection

def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    draw_array.append("SignalEnergyLight")
    #draw_array.append("lightEnergy")
    #draw_array.append("energy[29]")
    #draw_array.append("energy[30]")
    #draw_array.append("energy[31]")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def ffn(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3
    return gaus + exp

def ffn_lin(x, A1, mu, sig, L1, L2):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    lin  = L1*x + L2
    return gaus + lin

def ffn_lin_sep(x, A1, mu, sig, L1, L2):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    lin  = L1*x + L2
    return gaus ,lin

def ffn_sep(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3
    return gaus , exp

def FitPeakLinear(hist_counts, hist_errors, bin_centers):
    de = 170 # Fit width
    #peak_pos = 570.0 #bin_centers[np.argmax(hist_counts)]
    peak_pos = bin_centers[np.argmax(hist_counts)]

    print "Peak Guess", peak_pos

    #Only fit the bins within a range de of the peak
    fit_min = peak_pos-de
    fit_max = peak_pos+de
    fpts = np.logical_and( bin_centers > peak_pos-de, bin_centers < peak_pos+de )

    start_height = (hist_counts[fpts])[0]
    end_height   = (hist_counts[fpts])[-1]
    if end_height == 0: end_height = 1e-16
    if start_height == 0: start_height = 1.0
    sigma_guess  = 35.0
        
    slope_guess  = (1.0*(start_height-end_height))/(2*de)
    b_guess      = start_height - slope_guess*fit_min
    height_guess = hist_counts[np.argmin(np.abs(bin_centers - peak_pos))] - (slope_guess*peak_pos - b_guess) 

    spars = [height_guess, peak_pos, sigma_guess, slope_guess, b_guess] #Initial guess for fitter

    print "Height Guess:", height_guess
    print "Sigma  Guess:", sigma_guess
    print "Peak Pos:", peak_pos
    print "Exp Height Guess:", slope_guess
    print "EXP Decay Guess", b_guess

    fail = False

    #Perform the fit
    try:
        bp, bcov = opt.curve_fit(ffn_lin, bin_centers[fpts], hist_counts[fpts], p0=spars, sigma=hist_errors[fpts])
    except RuntimeError:
        print "**********************Did not work*******************************"
        fail = True
        bp = spars
        bcov = np.eye(len(bp))

    #Get the x values for evaluating the function
    xx = np.linspace( bin_centers[fpts][0], bin_centers[fpts][-1], 1e3 )

    print ""
    print "-------Fit Results----------"
    print "Fail: %i" % fail
    print "Mean:  %.2f" % bp[1]
    print "Sigma: %.2f" % bp[2]
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
    tree.SetBranchStatus("SignalEnergyLight",1)
    tree.SetBranchStatus("lightEnergy",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)
    tree.SetBranchStatus("trigger_time",1)
    #tree.SetBranchStatus("calibration",1)
    #tree.SetBranchStatus("energy1_pz",1)
    #tree.SetBranchStatus("trigger_time",1)
    #tree.SetBranchStatus("rise_time_stop95_sum",1)

    selectcmd = get_cut()
    drawcmd,nvals   = get_dcmd()
 
    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()
    
    chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy = []
    
    for nval in xrange(nvals-1):
        lightEnergy.append(np.array([tree.GetVal(nval+1)[i] for i in xrange(n)]))

    #H, xedges, yedges = np.histogram2d(chargeEnergy, lightEnergy, bins=[100,100], range=[[0,2000],[0,2000]])

    skipSum = False
    for nval in xrange(nvals-1):
        if nval > 0:
            ymax = 50
        else:
            ymax = 200
        xlabel = drawcmd.split(":")[0]
        ylabel = drawcmd.split(":")[nval+1]
    
        if ylabel == "lightEnergy" or ylabel=='SignalEnergyLight':
            ymax = 10000
            skipSum = True
        plt.clf()
        H = plt.hist2d(chargeEnergy, lightEnergy[nval], bins=[100,100], range=[[200,1200],[0,ymax]], 
                       norm=colors.LogNorm(vmin=1,vmax=100))
    
        plt.colorbar()
        plt.xlabel(xlabel,fontsize=15)
        plt.ylabel(ylabel,fontsize=15)
        plt.title("Light vs Charge SiPM Run")
        plt.savefig("./plots/light_vs_charge_%s.pdf" % ylabel)
        plt.show()
        raw_input()
        
    plt.clf()

    if not skipSum:
        H = plt.hist2d(chargeEnergy, lightEnergy[0] + lightEnergy[1] + lightEnergy[2], bins=[100,100], range=[[200,1200],[0,1000]])
        plt.xlabel(xlabel,fontsize=15)                
        plt.ylabel("Sum Light 29+30+31",fontsize=15)
        plt.title("Light vs Charge")
        plt.savefig("./plots/light_vs_charge_sum.pdf")
        raw_input()
    else:

        theta_list   = []
        res_list     = []
        res_err_list = [] 
        #for theta in np.arange(0.0, 0.2, 0.01):
        for theta in [0.0,0.025,0.05,0.075,0.1]:
            plt.figure(1)
            plt.clf()
            #H = plt.hist((chargeEnergy*np.cos(theta) + lightEnergy[0]*np.sin(theta)), 100, range=(300,2000), facecolor='b', alpha=0.4)
            
            rot_energy = (chargeEnergy*np.cos(theta) + lightEnergy[0]*np.sin(theta))
            norm = np.cos(theta) + np.sin(theta)
            print "Norm factor???", norm
            rot_energy *= 1.0/norm
            
            hist,bin_edges = np.histogram(rot_energy, bins=120, range=(200,2000))
            if theta > 0.4:
                hist,bin_edges = np.histogram(rot_energy, bins=120, range=(0,10000))

            bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
            
            fitx, fitp, fit_cov, isFail = FitPeakLinear(hist, np.sqrt(hist), bin_centers)
            
            full_fit = ffn_lin(fitx, fitp[0], fitp[1], fitp[2], fitp[3], fitp[4])
            plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist),marker='o', linestyle='None', c='k')
            plt.plot(fitx, full_fit, c='r')
            res = 0.0
            res_err = 0.0
            if theta < 0.5:
                res = (fitp[2]/fitp[1])*100
                res_err = (fit_cov[2,2]/fitp[1])
            gaus,exp = ffn_lin_sep(fitx, fitp[0], fitp[1], fitp[2], fitp[3], fitp[4])
            plt.plot(fitx, gaus, c='b', label="%.2f %% \n %.2f keV" % (res, fitp[1]))
            plt.plot(fitx, exp, c='g')
            plt.legend()
            plt.title("Rotated Energy (Theta = %.2f)" % theta)
            plt.xlabel("Rotated Energy [uncal]")
            plt.ylabel("Counts")

            theta_list.append(theta)
            res_list.append(res)
            res_err_list.append(res_err)

            plt.savefig("./plots/full_res_theta_%.2f.pdf" % theta)
            
            plt.figure(3)
            #plt.errorbar(bin_centers*(570/fitp[1]), hist, yerr=np.sqrt(hist), marker='o', linestyle='None',label='Theta %.2f' % theta)
            if theta < 0.5: 
                plt.step(bin_centers*(570/fitp[1]), hist, where='post', label='%.2f %% (Theta %.2f)' % (res,theta), linewidth=2.0)
            plt.title("Rotated Energy vs Theta")
            plt.xlabel("Rotated Energy [keV]")
            plt.ylabel("Counts")
            
            plt.legend()
            plt.xlim(300,1400)
            plt.show()
            raw_input()
        
        plt.savefig("./plots/all_thetas_calibrated.pdf")
        plt.figure(2)
        plt.clf()
        plt.errorbar(theta_list, res_list, yerr=res_err, marker='o', linestyle='None', c='r')
        plt.xlabel("Theta[rad]")
        plt.ylabel("Resolution")
        plt.savefig("./plots/res_vs_theta.pdf")
        raw_input()

if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        filename  = "overnight_new_bias_tier3_all_v3_12_6_2017.root"
    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)

