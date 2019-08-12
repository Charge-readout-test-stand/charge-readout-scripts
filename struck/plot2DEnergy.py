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
import itertools

plt.ion()

DoLightCorrection=False
drift_length = 33.0

def lightmap(x,y,drift_time,light_energy,charge_energy,cut,n_bin):
    cut_energy = (cut[0]<charge_energy) & (charge_energy<cut[1]) & (50<light_energy) & (light_energy<340)
    drift_time_cut = drift_time[cut_energy]
    light_energy_cut = light_energy[cut_energy]
    pos_x_cut = x[cut_energy]
    pos_y_cut = y[cut_energy]
    counts,bn = np.histogram(drift_time_cut,bins=50,range=(1,30))
    drift_velocity = drift_length/bn[0:][np.argmax(counts)]
    pos_z = drift_velocity*drift_time_cut
    lim_x = np.linspace(pos_x_cut.min(),pos_x_cut.max(),n_bin)
    lim_y = np.linspace(pos_y_cut.min(),pos_y_cut.max(),n_bin)
    lim_z = np.linspace(0.0,35.0,n_bin+1)
    bin_x_cut = np.digitize(pos_x_cut,lim_x)
    bin_y_cut = np.digitize(pos_y_cut,lim_y)
    bin_z_cut = np.digitize(pos_z,lim_z)
    vxl = np.array((bin_x_cut,bin_y_cut,bin_z_cut)).T
    mean_light_energy = np.mean(light_energy_cut)
    ly_matrix = np.ones((n_bin+1,n_bin+1,n_bin+2))
    #n_light_ev = np.zeros((n_bin+1,n_bin+1,n_bin+2))

    for i,vl in enumerate(itertools.product(np.arange(n_bin)+1,np.arange(n_bin)+1,np.arange(n_bin+1)+1)):
        selection_idx = np.where(np.sum((vxl == vl).reshape(-1,3),axis=1) == 3)[0]

        if  selection_idx.shape[0] == 0: continue

        light_energy_voxel = light_energy_cut[selection_idx]
        ly_matrix[vl[0],vl[1],vl[2]] = mean_light_energy/np.mean(light_energy_voxel)
        #ly_matrix[vl[0],vl[1],vl[2]] = np.mean(light_energy_voxel)
        #n_light_ev[vl[0],vl[1],vl[2]] = selection_idx.shape[0]

    return ly_matrix,lim_x,lim_y,lim_z,drift_velocity
    #return np.mean(ly_matrix[1:,1:,1:-1])/ly_matrix,lim_x,lim_y,lim_z,drift_velocity


def apply_light_map(ly_matrix,x,y,z,lim_x,lim_y,lim_z):
    bin_x = np.digitize(x,lim_x)
    bin_y = np.digitize(y,lim_y)
    bin_z = np.digitize(z,lim_z)

    return ly_matrix[bin_x,bin_y,bin_z]


def get_dcmd(light_map=True):
    draw_array = []
    draw_array.append("SignalEnergy")
    #draw_array.append("SignalEnergyLightTCut")
    draw_array.append("SignalEnergyLight")
    #draw_array.append("SignalEnergyLightBoth")
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_cmd =  ":".join(draw_array)

    if light_map:
        pos_array = []
        pos_array.append("pos_x")
        pos_array.append("pos_y")
        draw_pos = ":".join(pos_array)
        return draw_cmd,draw_pos

    return draw_cmd

def process_file(filename):
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())
    
    bname = os.path.basename(filename)
    bname = bname.replace(".root", "")

    min_time  = struck_analysis_cuts_sipms.get_min_time(tfile.Get("run_tree"))

    print "Min Tiime for this run", min_time

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
    #tree.SetBranchStatus("SignalEnergyLightTCut",1)
    #tree.SetBranchStatus("SignalEnergyLightBoth",1)
    tree.SetBranchStatus("lightEnergy",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("pos_x",1)
    tree.SetBranchStatus("pos_y",1)
    tree.SetBranchStatus("multiplicity",1)
    #selectcmd  = struck_analysis_cuts_sipms.get_std_cut(min_time)
    
    selectcmd  =  struck_analysis_cuts_sipms.get_cut_norise(min_time)
    if '1320' in filename or '24th' in filename:
        selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(14,18))
    else:
        #selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(12,15))
        selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(14,15))
        #selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(12,15))

    #if DoLightCorrection:
    #    selectcmd = struck_analysis_cuts_sipms.get_cut_norise(min_time)
        #selectcmd += " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(4,15))
    #    selectcmd += " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(10,15))
    
    #selectcmd += " && (pos_x<10 && pos_x>0) && (pos_y>0 && pos_y<5)"
    #selectcmd  += " && (pos_x>0)&& ( pos_y>0)"

    drawcmd,drawpos   = get_dcmd()
    print "Draw CMD",  drawcmd
    print "Select CMD for light map",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()    
    chargeEnergy = np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy  = np.array([tree.GetVal(1)[i] for i in xrange(n)])
    driftTime    = np.array([tree.GetVal(2)[i] for i in xrange(n)])
    tree.Draw(drawpos,selectcmd,"goff")
    pos_x        = np.array([tree.GetVal(0)[i] for i in xrange(n)])
    pos_y        = np.array([tree.GetVal(1)[i] for i in xrange(n)])

    if chargeEnergy.shape != pos_x.shape: raise IndexError('Position and energy have different sizes')


    chargeEnergy = struck_analysis_cuts_sipms.PurityCorrection(driftTime, chargeEnergy, min_time)
    lightCal = struck_analysis_cuts_sipms.light_cal(min_time)
    lightEnergy    *= lightCal#*0.65
    lightEnergy_uncorr = np.copy(lightEnergy)

    pos_z = driftTime
    if os.path.isfile('data/light_map_file.p'):
        pfile = open('data/light_map_file.p','rb')
        import cPickle as pickle
        ly_matrix       = pickle.load(pfile)
        lim_x           = pickle.load(pfile)
        lim_y           = pickle.load(pfile)
        lim_z           = pickle.load(pfile)
        drift_velocity = pickle.load(pfile)
        pos_z *=drift_velocity
        
        #lightEnergy = apply_light_map(ly_matrix,pos_x,pos_y,pos_z,lim_x,lim_y,lim_z)*lightEnergy
        #lightEnergyCorr = apply_light_map(ly_matrix,pos_x,pos_y,pos_z,lim_x,lim_y,lim_z)*lightEnergyCorr

        #raw_input("Pause")
    
    #if DoLightCorrection:
    #    lightEnergy = struck_analysis_cuts_sipms.LightCorrect(driftTime, lightEnergy, min_time)

#========================================
    plt.figure(figsize=(11,7))
    print np.shape(ly_matrix)
    plt.imshow(ly_matrix[:,:,-2]*570, interpolation='nearest')
    plt.colorbar()

#==========================================
    plt.figure(figsize=(11,7))
    print np.min(pos_x), np.max(pos_x), np.min(pos_y), np.max(pos_y)
    H = plt.hist2d(pos_x, pos_y, bins=[7,7], range=[[-10,20],[-15,15]],
                    norm=colors.LogNorm(vmin=100,vmax=10000)
                    )

    plt.colorbar()
#====================================

    plt.figure(figsize=(11,7))
    smin = 200
    smax = 1000
    cmin = 470
    cmax = 670
    nbins = 80
    plt.subplot(121)
    H = plt.hist2d(chargeEnergy, lightEnergy_uncorr, bins=[nbins,nbins], range=[[cmin,cmax],[smin,smax]],
                               norm=colors.LogNorm(vmin=1,vmax=100))


    plt.subplot(122)
    H = plt.hist2d(chargeEnergy, lightEnergy*(570.0/500.0), bins=[nbins,nbins], range=[[cmin,cmax],[smin,smax]],
                               norm=colors.LogNorm(vmin=1,vmax=100))


#=====================
    plt.figure(figsize=(11,7))
    smin = 0
    smax = 2500
    cmin = 20
    cmax = 1500
    nbins = 120

    H = plt.hist2d(chargeEnergy, lightEnergy, bins=[nbins,nbins], range=[[cmin,cmax],[smin,smax]], 
                   norm=colors.LogNorm(vmin=1,vmax=1000))
    
    #print H
    #exit()

    diagx = np.arange(np.min(chargeEnergy), np.max(chargeEnergy))
    chargeEnergyCut, lightEnergyCut, diag_parms, diag_cut =  struck_analysis_cuts_sipms.diag_cut(chargeEnergy,
                                                                                                 lightEnergy, min_time)

    #plt.plot(diagx, diag_parms[0]*diagx + diag_parms[1], linestyle='--', c='r', linewidth=7.0)
    #plt.plot(diagx, diag_parms[2]*diagx + diag_parms[3], linestyle='--',  c='r',  linewidth=7.0)
    cb = plt.colorbar()
    cb.set_label("Counts", fontsize=15)
    #plt.title("Light vs Charge SiPM Run", fontsize=16)
    plt.xlabel("Charge Energy [keV]", fontsize=15)
    #plt.ylabel("Light Energy [ADC]", fontsize=15)
    plt.ylabel("Light Energy [keV]", fontsize=15)
    plt.savefig("./plots/light_vs_charge_%s.pdf" % bname)
    plt.savefig("./plots/light_vs_charge_%s.png" % bname)

    plt.show()
    raw_input("PAUSE")    



    plt.clf()

    H = plt.hist2d(chargeEnergyCut, lightEnergyCut, bins=[nbins,nbins], range=[[cmin,cmax],[smin,smax]],
                   norm=colors.LogNorm(vmin=1,vmax=1000))
    cb = plt.colorbar()
    cb.set_label("Counts", fontsize=15)
    plt.title("Light vs Charge SiPM Run", fontsize=16)
    plt.xlabel("Charge Energy [keV]", fontsize=15)
    #plt.ylabel("Light Energy [ADC]", fontsize=15)
    plt.ylabel("Light Energy [keV]", fontsize=15)
    plt.savefig("./plots/light_vs_charge_diagcut_%s.pdf" % bname)
    raw_input("PAUSE")
    plt.clf()


    theta_list = np.arange(0.0,0.5, 0.02)
    min_theta_nocut = ScanAngles(chargeEnergy, lightEnergy, theta_list, "noDiag_%s" % bname)
    theta_list = [0.0, min_theta_nocut, np.max(theta_list)]
    CompareAngles(chargeEnergy, lightEnergy, theta_list, 'compare_noDiag_%s' % bname)
    raw_input()
    PlotBest(chargeEnergy, lightEnergy,min_theta_nocut, 'best_noDiag_%s' % bname)

    theta_list = np.arange(0.0,0.5, 0.02)
    min_theta_diag = ScanAngles(chargeEnergyCut, lightEnergyCut, theta_list, "wDiag_%s" % bname)
    #theta_list = [0.0, min_theta_diag, np.max(theta_list)]
    theta_list = [0.0, min_theta_diag]
    CompareAngles(chargeEnergyCut, lightEnergyCut, theta_list, "compare_wDiag_%s" % bname)
    raw_input()
    
    PlotBest(chargeEnergyCut, lightEnergyCut, min_theta_diag, "best_wDiag_%s" % bname)
    
def CompareAngles(chargeEnergy, lightEnergy, theta_list, name):
    figtheta = plt.figure(7,figsize=(9,5))
    figtheta.clf()
    
    ymax_list = []
    
    color_list = ['b','r']

    for ti,theta in enumerate(theta_list):
        
        rot_energy = (chargeEnergy*np.cos(theta) + lightEnergy*np.sin(theta))
        norm = np.cos(theta) + np.sin(theta)
        rot_energy *= 1.0/norm
        #Make Histogram
        hist,bin_edges = np.histogram(rot_energy, bins=140, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

        fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                    bin_centers, 
                                                                                    #fit_width=170
                                                                                    fit_width=120
                                                                                    )
        
        fitx2, fitp2, fit_cov2, isFail2, full_fit2, gaus2, linear2 = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                    bin_centers, fit_width=170, peak_guess=1050)

        res  = np.abs(fitp[2]/fitp[1])*100
        res2 = np.abs(fitp2[2]/fitp2[1])*100
        cal = (570.0/fitp[1])
        print "------------------->Theta:",theta, "Cal:", cal

        cal_m = (1060.0-570.0)/(fitp2[1]-fitp[1])
        cal_b = 570.0 - fitp[1]*cal_m
        

        hist,bin_edges = np.histogram(rot_energy*cal, bins=120, range=(200,2000))
        #hist,bin_edges = np.histogram(rot_energy*cal, bins=180, range=(200,2000))
        bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0
        
        if len(theta_list)==2:
            if ti==0:
                etype='Charge \n'   
            if ti==1:
                etype  ='Rotated \n'
            
            etype += r"570keV: $\sigma$/E = %.2f $\pm$ %.2f  "% (res, (fit_cov[2,2]**0.5)*100.0/fitp[1])
            etype += "%"
            etype += "\n"
            etype += r"1060keV: $\sigma$/E = %.2f $\pm$ %.2f " % (res2, (fit_cov2[2,2]**0.5)*100.0/fitp2[1])
            etype += "%"

            print cal, cal_m*570 + cal_b, cal_m*1060 + cal_b
            cal_energy = cal_m*rot_energy + cal_b
            #hist,bin_edges = np.histogram(cal_energy*cal, bins=150, range=(200,2000))
            hist,bin_edges = np.histogram(cal_energy, bins=120, range=(200,2000))
            bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

            plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist), linestyle='None', 
                         color=color_list[ti],  marker='.',  ms=1)
            
            #plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist), drawstyle='steps-post', 
            
            #plt.step(bin_centers, hist, where='post',
                #label=r"$\sigma$/E = %.2f $\%%$, %.2f $\%%$  ($\theta$= %.2f)" % (res, res2,theta), 
                    #label=r"$\sigma$/E = %.2f $\%%$ (%s)" % (res, etype),
                    #label='%s'%etype,
                    #color=color_list[ti],
                    #linewidth=3.0)

            plt.hist(cal_energy, bins=120, range=(200,2000), label='%s'%etype,
                        color=color_list[ti],facecolor=color_list[ti], alpha=0.2,
                        linewidth=3.0, histtype='stepfilled')
            
            plt.hist(cal_energy, bins=120, range=(200,2000),
                        color=color_list[ti],facecolor='None',
                        linewidth=3.0, histtype='step')

            #plt.fill_between(bin_centers, hist, alpha=0.3, color=color_list[ti], step='post')
            

        else:
            plt.step(bin_centers, hist, where='post',
                    label=r"$\sigma$/E = %.2f $\%%$, %.2f $\%%$  ($\theta$= %.2f)" % (res, res2,theta), 
                    #label=r"$\sigma$/E = %.2f $\%%$ (%s)" % (res, etype),
                    #color=color_list[ti],
                    linewidth=2.0)


        ymax_list.append(np.max(hist))
    
    plt.xlabel("Energy [keV]", fontsize=15)
    plt.ylabel("Counts [#]", fontsize=15)
    plt.xlim(200,1500)
    plt.ylim(0,  max(ymax_list)*1.1)
    plt.legend()
    plt.grid(True)
    plt.savefig("./plots/theta_scan/compare_rot_angles_%s.pdf" % name)
    
    #plt.xlim(250,1000)
    plt.xlim(300,1300)
    plt.savefig("./plots/theta_scan/compare_rot_angles_%s.png" % name)
    #raw_input()
    return

def PlotBest(chargeEnergy, lightEnergy, theta, name):
    
    figtheta = plt.figure(77,figsize=(9,5))
    figtheta.clf()

    rot_energy = (chargeEnergy*np.cos(theta) + lightEnergy*np.sin(theta))
    norm = np.cos(theta) + np.sin(theta)
    rot_energy *= 1.0/norm
    
    #Make Histogram
    hist,bin_edges = np.histogram(rot_energy, bins=140, range=(200,2000))
    bin_centers    = bin_edges[:-1] + np.diff(bin_edges)/2.0

    fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                bin_centers, 
                                                                                fit_width=120
                                                                                )

    fitx2, fitp2, fit_cov2, isFail2, full_fit2, gaus2, linear2 = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
                                                                                bin_centers, fit_width=170, peak_guess=1050)

    res  = np.abs(fitp[2]/fitp[1])*100
    res2 = np.abs(fitp2[2]/fitp2[1])*100
    cal = (570.0/fitp[1])
    
    print "------------------->Best Theta:",theta, "Cal:", cal
    #hist,bin_edges = np.histogram(rot_energy*cal, bins=140, range=(200,2000))
    #bin_centers = bin_edges[:-1] + np.diff(bin_edges)/2.0

    #fitx, fitp, fit_cov, isFail, full_fit, gaus, linear = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
    #                                                                             bin_centers, fit_width=170)

    #fitx2, fitp2, fit_cov2, isFail2, full_fit2, gaus2, linear2 = FitPeakPy.FitPeakTest(hist, np.sqrt(hist),
    #                                                                             bin_centers, fit_width=170, peak_guess=1050)

    #res  = (fitp[2]/fitp[1])*100
    #res2 = (fitp2[2]/fitp2[1])*100

    plt.errorbar(bin_centers, hist, yerr=np.sqrt(hist),marker='o', linestyle='None', c='k')
    plt.plot(fitx, full_fit, c='r', label=r"$\sigma$/E (570keV) = %.2f %%" % (res), linewidth=2.0)
    #plt.plot(fitx, gaus,     c='b', label='Gaus Comp')
    #plt.plot(fitx, linear,   c='g', linewidth=2.0)

    #plt.plot(fitx2, full_fit2, c='c', label=r"$\sigma$/E (1050keV) = %.2f %%" % (res2), linewidth=2.0)
    #plt.plot(fitx2, gaus2,     c='b')
    #plt.plot(fitx2, linear2,   c='g', linewidth=2.0)

    plt.legend(fontsize=18)
    #plt.title(r"Rotated Energy ($\theta$ = %.2f rad)" % theta, fontsize=18)
    #plt.title(r"Rotated Energy", fontsize=18)
    plt.xlabel("Rotated Energy [keV]", fontsize=18)
    plt.ylabel("Counts", fontsize=18)
    plt.xlim(300,1400)

    plt.xlim(300,1300)
    plt.ylim(0,  np.max(hist)*1.1)
    plt.legend()
    plt.grid(True)
    plt.savefig("./plots/theta_scan/best_rot_angles_%s.pdf" % name)
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
                                                                         bin_centers, fit_width=120)

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
            res = np.abs(fitp[2]/fitp[1])*100
            if not isFail: res_err = (fit_cov[2,2]/fitp[1])*100
            else: 
                res_err = 0.0
                res     = 0.0

            res2 = np.abs(fitp2[2]/fitp2[1])*100
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
        plt.plot(fitx, full_fit, c='r', label=r"$\sigma$/E (570keV) = %.2f %%" % (res), linewidth=2.0)
        plt.plot(fitx, gaus,     c='b')
        plt.plot(fitx, linear,   c='g', linewidth=2.0)
        
        plt.plot(fitx2, full_fit2, c='c', label=r"$\sigma$/E (1050keV) = %.2f %%" % (res2), linewidth=2.0)
        plt.plot(fitx2, gaus2,     c='b')
        plt.plot(fitx2, linear2,   c='g', linewidth=2.0)

        plt.legend(fontsize=18)
        plt.title(r"Rotated Energy ($\theta$ = %.2f rad)" % theta, fontsize=18)
        plt.xlabel("Rotated Energy [uncal]", fontsize=18)
        plt.ylabel("Counts", fontsize=18)
        plt.xlim(300,1400)
        pdf.savefig(figtheta)

        if res_err<1.e-9 :
            res_err =  1.e9
        if res_err2<1.e-9:
            res_err2 = 1.e9

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
    
    print res_err_list
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
    plt.title(r"Resoltuion vs Theta Scan ($\theta_{avg}$=%.2f)"%((min_theta1 + min_theta2)/2.0),fontsize=18)
    plt.ylim(2.5, 7.5)
    plt.xlim(-.02, np.max(theta_list)*1.2)
    plt.legend()
    pdf.savefig(figprof)
    pdf.close()
    
    #return (min_theta1 + min_theta2)/2.0
    return (min_theta1)

if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        #filename  = "~/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v3_12_6_2017.root"
        #filename  = "~/13thLXe/all_tier3_overnight_day2_315bias_v3.root"
        #filename  = "~/2018_01_26_SiPM_Run2/full_cell_day_runs/tier3_added/all_tier3_day1_305bias_v3.root"
        #filename  = "~/2018_01_26_SiPM_Run2/full_cell_day_runs_2/tier3_added/all_tier3_day2_305bias.root"
        #filename   = "~/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v4_12_7_2017.root"
        #filename   = "/home/teststand/22nd_LXe/overnight_4_17_2019/tier3_added/tier3_22nd_overnight_4_17_2019_v1.root"
        #filename    = "/home/teststand/22nd_LXe/overnight_4_18_2019_aftercirc/tier3_added/tier3_added_22nd_overnight2_aftercirc.root"
        #filename    = "/home/teststand/22nd_LXe/overnight_4_18_2019_aftercirc/tier3_added/tier3_added_22nd_overnight2_aftercirc_nofilter.root"
        #filename    = "/home/teststand/22nd_LXe/day_testing_4_19_2019_newfield/tier3_added/tier3_added_22nd_1320V_v1.root"
        #filename     = "/home/teststand/23rd_LXe/tier3_all/tier3_23rd.root"
        
        #filename    =   "/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2.root"
        filename    =   "/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2_newgains.root"
        #filename   = "/home/teststand/24th_LXe/tier3_added/tier3_added_24th_dn5_dn6.root"
        #filename   = "/home/teststand/24th_LXe/tier3_added/tier3_added_24th_dn5_dn6_newgains.root"

    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)


