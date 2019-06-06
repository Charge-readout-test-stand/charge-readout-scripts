#import plot2DEnergy

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
import cPickle as pickle


def mult_var_gaus((X,Y), *p):
    A,ux,uy,sx,sy,rho = p
    #X,Y = np.meshgrid(x,y)
    assert rho != 1
    a= -1 / (2*(1-rho**2))
    
    exp =  ((X - ux)/sx)**2
    exp += ((Y - uy)/sy)**2
    exp += -1*(2*rho*(X - ux)*(Y - uy))/(sx*sy)

    Z = A*np.exp(a*exp)
    #return Z.ravel()
    return Z

def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    draw_array.append("SignalEnergyLight")
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
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
    
    remake= False
    pfile = 'pdata.p'
    if remake or not os.path.isfile(pfile):
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
        lightEnergy =   np.array([tree.GetVal(1)[i] for i in xrange(n)])
        driftTime    = np.array([tree.GetVal(2)[i] for i in xrange(n)])
        
        data = np.zeros((3,n))
        data[0,:] = chargeEnergy
        data[1,:] = lightEnergy
        data[2,:] =  driftTime
        pickle.dump(data, open(pfile,'wb'))
    
    else:
        print "loading file"
        data=pickle.load(open(pfile,'rb'))
        chargeEnergy = data[0,:]
        lightEnergy  = data[1,:]
        driftTime    = data[2,:]

    chargeEnergy = struck_analysis_cuts_sipms.PurityCorrection(driftTime, chargeEnergy, min_time)

    lightCal = struck_analysis_cuts_sipms.light_cal(min_time)
    lightEnergy *= lightCal

    plt.figure(figsize=(11,7))
    #ymax = 10000
    ymax  = 1500
    nbins = 20
    hist,xedges,yedges,image = plt.hist2d(chargeEnergy, lightEnergy, bins=[nbins,nbins], 
                                          range = [[450,630],[350,850]]
                                          #range=[[0,ymax],[0,ymax]],
                                          #norm=colors.LogNorm(vmin=1,vmax=100)
                                          )
    xcents = (xedges[:-1] + xedges[1:])/2.
    ycents = (yedges[:-1] + yedges[1:])/2.
 
    
    p0 = (100., 550., 590., 35., 100., -0.4)
    X,Y = np.meshgrid(xcents, ycents)
    x1d, y1d = X.ravel(), Y.ravel()
    hist1d   = hist.ravel()
    err      = np.sqrt(hist1d)
    min_cut = 25
    fpts = hist1d > min_cut
    ccut = np.logical_and(x1d>450, x1d<630)
    scut = np.logical_and(y1d>350, y1d<800)
    fpts = np.logical_and(fpts, ccut)
    fpts = np.logical_and(fpts, scut)

    coeff, var_matrix = opt.curve_fit(mult_var_gaus, (x1d[fpts], y1d[fpts]), hist1d[fpts], 
                                        p0=p0,
                                        sigma=err[fpts])

    print coeff
    print "C-Res", coeff[3]/coeff[1]
    print "L-Res", coeff[4]/coeff[2]


    fit1d   = mult_var_gaus((x1d,y1d), *coeff)
    guess1d = mult_var_gaus((x1d,y1d), *p0)

    diagx = np.arange(np.min(chargeEnergy), np.max(chargeEnergy))
    chargeEnergyCut, lightEnergyCut, diag_parms, diag_cut = struck_analysis_cuts_sipms.diag_cut(chargeEnergy,lightEnergy, min_time)

    #plt.plot(diagx, diag_parms[0]*diagx + diag_parms[1], linestyle='--', c='r', linewidth=7.0)
    #plt.plot(diagx, diag_parms[2]*diagx + diag_parms[3], linestyle='--',  c='r',  linewidth=7.0)
    cb = plt.colorbar()
    
    plt.contour(X,Y, fit1d.reshape(np.shape(X)), 3,   colors='r')
    plt.contour(X,Y, guess1d.reshape(np.shape(X)), 3, colors='g', linestyles='--')
    
    plt.plot(coeff[1], coeff[2], marker='x', ms=20, color='r')

    cb.set_label("Counts", fontsize=15)
    plt.title("Light vs Charge SiPM Run", fontsize=16)
    plt.xlabel("Charge Energy [keV]", fontsize=15)
    plt.ylabel("Light Energy [ADC]", fontsize=15)
    plt.savefig("./plots/light_vs_charge_%s.pdf" % bname)
    
    
    plt.figure(23, figsize=(15,5))

    plt.subplot(131)
    hist[hist<min_cut] = np.nan
    plt.imshow(hist.T, interpolation='nearest', origin='low', aspect='auto',
                extent=[np.min(X), np.max(X), np.min(Y), np.max(Y)])

    plt.subplot(132)
    plt.imshow(fit1d.reshape(np.shape(X)).T, interpolation='nearest', origin='low', aspect='auto',
                            extent=[np.min(X), np.max(X), np.min(Y), np.max(Y)])

    plt.subplot(133)
    diff = (hist - fit1d.reshape(np.shape(X)))
    diff[hist>1] *= 1./np.sqrt(hist[hist>1])
    
    diff_guess = (hist - guess1d.reshape(np.shape(X)))
    diff_guess[hist>1] *= 1./np.sqrt(hist[hist>1])

    print np.sum(diff.ravel()[fpts]**2), np.sum(diff_guess.ravel()[fpts]**2)

    
    plt.imshow(diff.T, interpolation='nearest', origin='low', aspect='auto',
                            extent=[np.min(X), np.max(X), np.min(Y), np.max(Y)])
    plt.colorbar()

    plt.show()

if __name__ == "__main__":
    filename = "~/jewell6_new2/22nd_LXe/overnight_4_17_2019/tier3_added/tier3_22nd_overnight_4_17_2019_v1.root"
    #filename  = "~/jewell6_new2/22nd_LXe/overnight_4_18_2019_aftercirc/tier3_added/tier3_added_22nd_overnight2_aftercirc_nofilter.root"
    
    print "Using ", filename
    process_file(filename)



