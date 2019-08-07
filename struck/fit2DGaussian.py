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

def apply_light_map(ly_matrix,x,y,z,lim_x,lim_y,lim_z):
    bin_x = np.digitize(x,lim_x)
    bin_y = np.digitize(y,lim_y)
    bin_z = np.digitize(z,lim_z)

    return ly_matrix[bin_x,bin_y,bin_z]

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
    tree.SetBranchStatus("multiplicity",1)
    tree.SetBranchStatus("pos_x",1)
    tree.SetBranchStatus("pos_y",1)

    #selectcmd = struck_analysis_cuts_sipms.get_std_cut(min_time)
    selectcmd  =  struck_analysis_cuts_sipms.get_cut_norise(min_time)
    if '24th' in filename:
        selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(17,18))
    else:
        selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(14,15))

    #selectcmd = selectcmd + " && " + "(pos_x>0)&& ( pos_y<0)"
    drawcmd   = get_dcmd()

    
    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    
    remake= True
    pfile = 'pdata.p'
    if remake or not os.path.isfile(pfile):
        tree.Draw(drawcmd,selectcmd,"goff")
        n = tree.GetSelectedRows()
        chargeEnergy =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
        lightEnergy =   np.array([tree.GetVal(1)[i] for i in xrange(n)])
        driftTime     = np.array([tree.GetVal(2)[i] for i in xrange(n)])
        
        tree.Draw("pos_x:pos_y",selectcmd,"goff")
        pos_x        = np.array([tree.GetVal(0)[i] for i in xrange(n)])
        pos_y        = np.array([tree.GetVal(1)[i] for i in xrange(n)])

        data = np.zeros((5,n))
        data[0,:] = chargeEnergy
        data[1,:] = lightEnergy
        data[2,:] =  driftTime
        data[3,:] =  pos_x
        data[4,:] =  pos_y
        pickle.dump(data, open(pfile,'wb'))
    
    else:
        print "loading file"
        data=pickle.load(open(pfile,'rb'))
        chargeEnergy = data[0,:]
        lightEnergy  = data[1,:]
        driftTime    = data[2,:]
        pos_x        = data[3,:]
        pos_y        = data[4,:]
        data.close()

    chargeEnergy = struck_analysis_cuts_sipms.PurityCorrection(driftTime, chargeEnergy, min_time)

    lightCal = struck_analysis_cuts_sipms.light_cal(min_time)
    lightEnergy *= lightCal

    pos_z = driftTime
    doCorrect=True
    if os.path.isfile('data/light_map_file.p') and doCorrect:
        pfile = open('data/light_map_file.p','rb')
        ly_matrix       = pickle.load(pfile)
        lim_x           = pickle.load(pfile)
        lim_y           = pickle.load(pfile)
        lim_z           = pickle.load(pfile)
        drift_velocity = pickle.load(pfile)
        pos_z *=drift_velocity
        lightEnergy = apply_light_map(ly_matrix,pos_x,pos_y,pos_z,lim_x,lim_y,lim_z)*lightEnergy

    

    plt.figure(figsize=(11,7))
    #ymax = 10000
    ymax  = 1500
    nbins = 25
    min_cut = 10
    if '24th' in filename:
        cmin  = 450
        cmax  = 690
        smin  = 300
        smax  = 1200
        nbins = 30
        min_cut = 30
    else:
        cmin  = 490
        cmax  = 670
        smin  = 320
        smax  = 720
    hist,xedges,yedges,image = plt.hist2d(chargeEnergy, lightEnergy, bins=[nbins,nbins], 
                                          range = [[cmin,cmax],[smin,smax]],
                                          #range=[[0,ymax],[0,ymax]],
                                          norm=colors.LogNorm(vmin=1,vmax=300),
                                          cmap='CMRmap'
                                          )
    xcents = (xedges[:-1] + xedges[1:])/2.
    ycents = (yedges[:-1] + yedges[1:])/2.
    #plt.colorbar()

    p0 = (100., 570., 570., 550*0.055, 100., -0.4)
    if doCorrect:
        p0 = (100., 580., 500., 550*0.055, 100., -0.4)
    X,Y = np.meshgrid(xcents, ycents, indexing='ij')
    
    x1d, y1d = X.ravel(), Y.ravel()
    hist1d   = hist.ravel()
    
    #for hix in xrange(25):
    #    for hiy in xrange(25):
    #        print hist[hix,hiy], xcents[hix], ycents[hiy]
    #        print X[hix,hiy], Y[hix,hiy]
    #        print
    #raw_input('test')

    print np.shape(xcents), np.shape(ycents), np.shape(hist)

    err      = np.sqrt(hist1d)
    #min_cut = 10
    fpts = hist1d > min_cut
    
    ccut = np.logical_and(x1d>cmin, x1d<cmax)
    scut = np.logical_and(y1d>smin, y1d<smax)

    fpts = np.logical_and(fpts, ccut)
    fpts = np.logical_and(fpts, scut)
    
    guess1d = mult_var_gaus((x1d,y1d), *p0)
    #plt.contour(X,Y, guess1d.reshape(np.shape(X)), 3, colors='k', linestyles='--', linewidths=5)
    plt.ion()

    print np.max(hist)
    print np.max(hist1d)
    print x1d[np.argmax(hist1d)]
    print y1d[np.argmax(hist1d)]

    #plt.plot(x1d[np.argmax(hist1d)], y1d[np.argmax(hist1d)], marker='x', ms=30, mew=4, color='w')
    plt.show()
    #raw_input("PAUSE")

    coeff, var_matrix = opt.curve_fit(mult_var_gaus, (x1d[fpts], y1d[fpts]), hist1d[fpts], 
                                        p0=p0,
                                        sigma=err[fpts])

    print coeff
    print "C-Res", coeff[3]/coeff[1]
    print "L-Res", coeff[4]/coeff[2]


    fit1d   = mult_var_gaus((x1d,y1d), *coeff)
    #fit1d   = mult_var_gaus((x1d,y1d), *p0)
    guess1d = mult_var_gaus((x1d,y1d), *p0)

    diagx = np.arange(np.min(chargeEnergy), np.max(chargeEnergy))
    chargeEnergyCut, lightEnergyCut, diag_parms, diag_cut = struck_analysis_cuts_sipms.diag_cut(chargeEnergy,lightEnergy, min_time)

    #plt.plot(diagx, diag_parms[0]*diagx + diag_parms[1], linestyle='--', c='r', linewidth=7.0)
    #plt.plot(diagx, diag_parms[2]*diagx + diag_parms[3], linestyle='--',  c='r',  linewidth=7.0)
    cb = plt.colorbar()
    
    plt.contour(X,Y, fit1d.reshape(np.shape(X)),   3,   colors='k', linewidths=5, linestyles='--')
    #plt.contour(X,Y, guess1d.reshape(np.shape(X)), 3, colors='y', linestyles='--', linewidth=5)
    
    plt.plot(coeff[1], coeff[2], marker='x', ms=30, mew=4, color='k')

    cb.set_label("Counts", fontsize=15)
    plt.title("Light vs Charge SiPM Run", fontsize=16)
    plt.xlabel("Charge Energy [keV]", fontsize=15)
    plt.ylabel("Light Energy [ADC]", fontsize=15)
    plt.savefig("./plots/fit_light_vs_charge_%s.pdf" % bname)
    
    
    plt.figure(23, figsize=(15,5))

    plt.subplot(131)
    hist[hist<min_cut] = np.nan
    plt.imshow(hist.T, interpolation='nearest', origin='low', aspect='auto',
                extent=[np.min(X), np.max(X), np.min(Y), np.max(Y)])

    plt.subplot(132)
    plt.imshow(fit1d.reshape(np.shape(X)).T, interpolation='nearest', origin='low', aspect='auto',
                            extent=[np.min(X), np.max(X), np.min(Y), np.max(Y)])
    plt.contour(X,Y, fit1d.reshape(np.shape(X)),   3,   colors='w', linewidth=5)
    plt.plot(coeff[1], coeff[2], marker='x', ms=30, mew=4, color='w')
    

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

    raw_input("PAUSE END")

if __name__ == "__main__":
    #filename = "~/jewell6_new2/22nd_LXe/overnight_4_17_2019/tier3_added/tier3_22nd_overnight_4_17_2019_v1.root"
    #filename  = "~/jewell6_new2/22nd_LXe/overnight_4_18_2019_aftercirc/tier3_added/tier3_added_22nd_overnight2_aftercirc_nofilter.root"
    
    #filename = "/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2.root"
    #filename = "/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2_newgains.root"
    filename  = "/home/teststand/24th_LXe/tier3_added/tier3_added_24th_dn5_dn6_newgains.root"

    print "Using ", filename
    process_file(filename)



