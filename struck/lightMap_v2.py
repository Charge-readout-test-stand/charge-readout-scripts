import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
import struck_analysis_parameters
import struck_analysis_cuts_sipms
import scipy.optimize as opt
import FitPeakPy,PeakFitter2D, PeakFitter1D,ScanRotationAngle
import matplotlib.backends.backend_pdf as PdfPages
import itertools
import cPickle as pickle

#from scipy.interpolate import RegularGridInterpolator
from scipy.interpolate import LinearNDInterpolator
from scipy.interpolate import griddata

color_list   = ['r', 'b', 'g', 'c', 'k', 'y', 'm', 'r', 'b', 'g', 'c', 'y']
drift_length = 33.0
plt.ion()

def gen_lightmap(x,y,drift_time,light_energy,charge_energy, lm_dims):

    #Find max bin in Drift Hist to get Velocity
    counts,bn = np.histogram(drift_time,bins=50,range=(1,30))
    drift_velocity = drift_length/bn[0:][np.argmax(counts)]

    z = drift_time*drift_velocity
    lm_array = np.zeros(lm_dims)
    
    print drift_velocity, bn[0:][np.argmax(counts)]
    #raw_input()    

    dx = (x.max()-x.min())/lm_dims[0]
    dy = (y.max()-y.min())/lm_dims[1]
    dz = (drift_length)/lm_dims[2]


    lim_x = np.arange(x.min(),x.max(),dx)   + dx/2.0
    lim_y = np.arange(y.min(),y.max(),dy)   + dy/2.0
    lim_z = np.arange(0.0,drift_length, dz) + dz/2.0

    X,Y,Z = np.meshgrid(lim_x, lim_y, lim_z, indexing='ij')

    #for ix in xrange(lm_dims[0]):
    for iz in xrange(lm_dims[2]):
        for iy in xrange(lm_dims[1]):
            #for iz in xrange(lm_dims[2]):
            for ix in xrange(lm_dims[0]):   
                xwin = [X[ix,iy,iz]-dx/2.0, X[ix,iy,iz]+dx/2.0]
                ywin = [Y[ix,iy,iz]-dy/2.0, Y[ix,iy,iz]+dy/2.0]
                zwin = [Z[ix,iy,iz]-dz/2.0, Z[ix,iy,iz]+dz/2.0]

                xcut = np.logical_and(x>xwin[0], x<xwin[1])
                ycut = np.logical_and(y>ywin[0], y<ywin[1])
                zcut = np.logical_and(z>zwin[0], z<zwin[1])
                
                cut  = np.logical_and(xcut,ycut)
                cut  = np.logical_and(cut, zcut)

                #light_energy[cut]
                #charge_energy[cut]

                fig = plt.figure(111)
                plt.clf()
                fig.set_size_inches((15,9), forward=True)

            #====================================
                plt.subplot(131)
                pf1 = PeakFitter1D.PeakFitter1D(charge_energy[cut])
                pf1.setBins(120)
                pf1.setXWin([100,2000])
                pf1.setWidth(200)
                pf1.setGuess(570,35)
                pf1.makeHist()
                pf1.doFit()
                pf1.plotFit()
                plt.title("(X=%i, Y=%i, Z=%i) %.2f %%" % (X[ix,iy,iz], Y[ix,iy,iz], Z[ix,iy,iz], pf1.pf[2]*100/pf1.pf[1]))
            #================================

                cpeak  = pf1.pf[1]
                csigma = pf1.pf[2]

                charge_cut = np.logical_and(cpeak-4*csigma, cpeak+4*csigma)
                cut = np.logical_and(charge_cut,cut)

                print "Charge Peak:", cpeak     
                print "C-Sigma:", csigma

            #============================================
                plt.subplot(132)
                pfS = PeakFitter1D.PeakFitter1D(light_energy[cut])
                pfS.setBins(80)
                pfS.setXWin([10,2000])
                pfS.setWidth(300)
                pfS.makeHist()
                pfS.setGuess(pfS.cents[np.argmax(pfS.hist)],100)
                checkS=pfS.doFit()
                if checkS > 0: 
                    pfS.plotFit()
                else:
                    print "Fit failed"

            #==================================
                plt.subplot(133)
                pf2d = PeakFitter2D.PeakFitter2D(charge_energy[cut], light_energy[cut])
                pf2d.setWin([cpeak-4*abs(csigma), cpeak+4*abs(csigma)], [200, 1000])
                pf2d.setBins([20,20])
                pf2d.makeHist()
                
                light_guess=570
                if checkS > 0:
                    light_guess = pfS.pf[1]
                else:
                    maxC,maxS = pf2d.getMaxBin()
                    if abs(maxC-cpeak)<100:
                        light_guess = maxS
                    

                pf2d.setGuess(A=100, ux=cpeak, uy=light_guess, sigx=csigma, sigy=90, rho=-0.5)
                check=pf2d.doFit(min_cut=5)

                pf2d.getMaxBin()


                if check>0:
                    pf2d.plotFit()
                    plt.plot(pf2d.p0[1], pf2d.p0[2], marker='x', ms=30, color='b', mew=10)
                    plt.title("(Q:%.2f, S:%.2f) %.2f %%" % (pf2d.pf[1], pf2d.pf[2], pf2d.pf[3]*100/pf2d.pf[1]))
                    print "Best fit", pf2d.pf
                else:
                    print "Did not suceed"
                    pf2d.plotGuess()
                    plt.plot(pf2d.p0[1], pf2d.p0[2], marker='x', ms=30, color='b', mew=10)

                lm_array[ix,iy,iz] = pf2d.p0[2]
            #==================================
                #raw_input()
                plt.savefig("plots/lightmap/map_fits_%i_%i_%i.png" % (ix,iy,iz))
    
            #==================================================
                find_theta=ScanRotationAngle.ScanRotation(charge_energy[cut], light_energy[cut], 570.0)
                find_theta.setXWin([0,2000])
                find_theta.setBins(180)
                find_theta.setWidth(130)
                find_theta.setGuess(570, 25)
                find_theta.set_theta_list(np.arange(0,0.5, 0.05))
                find_theta.set_make_plots("test")
                find_theta.ScanAngles()

                plt.figure(15)
                min_theta = find_theta.get_best_theta()
                cal       = find_theta.get_cal(find_theta.get_best_theta())
                find_theta.plot_theta(theta=min_theta, filled=True, cal=cal, color=color_list[iz])
                print "---------->Resolution:", find_theta.pf[2]*100/find_theta.pf[1]
                plt.show()
                #raw_input()
            #====================================================

    plt.figure(100)

    plt.imshow(lm_array[:,:,-1].T, interpolation='nearest', origin='low', aspect='auto',
                    extent=[x.min(),x.max(),y.min(),y.max()])
    plt.colorbar()
    plt.savefig("plots/lightmap/map_zslice_cathode.png")
    
    plt.figure(101)

    plt.plot(lim_z, lm_array[0,0,:])
       
    #raw_input()

    pos_stack = np.vstack((x,y,z)).T
    lm_corr = apply_light_map((lim_x, lim_y, lim_z), lm_array, pos_stack)
    #raw_input()
    #570.0/lm_corr

    return light_energy*(570.0/lm_corr), (lim_x, lim_y, lim_z), lm_array

def get_dcmd(light_map=True):
    draw_array = []
    draw_array.append("SignalEnergy")
    draw_array.append("SignalEnergyLight")
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_cmd =  ":".join(draw_array)

    if light_map:
        pos_array = []
        pos_array.append("pos_x")
        pos_array.append("pos_y")
        draw_pos = ":".join(pos_array)
        return draw_cmd,draw_pos
    return draw_cmd

def apply_light_map(lim_xyz, lm_array, eval_pts):

    #X,Y,Z = np.meshgrid(lim_xyz[0], lim_xyz[1], lim_xyz[2], indexing='ij')
    #xyz = np.c_[X.flatten(), Y.flatten(), Z.flatten()]
    #print xyz.shape
    #lm_rgi = LinearNDInterpolator(xyz,lm_array.flatten())
    #print lm_rgi(eval_pts)
    #print interpnd(lim_xyz,lm_array, eval_pts)

    bin_arr = np.zeros((len(lim_xyz), len(eval_pts)), dtype=np.int)
    for i in xrange(len(lim_xyz)):
        if len(lim_xyz[i]) != 1:
            db           = np.diff(lim_xyz[i])[0]/2.0
            bin_edges    = lim_xyz[i] - db
            bin_edges    = np.append(bin_edges, bin_edges[-1]+db*2)
            bin_arr[i,:] = np.digitize(eval_pts[:,i], lim_xyz[i])-1  


    #for ti, test in enumerate(bin_arr[2]):
    #    print lim_xyz[2]
    #    print ti,test
    #    raw_input()

    #print lm_array[bin_arr[0], bin_arr[1], bin_arr[2]]
    return lm_array[bin_arr[0], bin_arr[1], bin_arr[2]]

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
    tree.SetBranchStatus("lightEnergy",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("pos_x",1)
    tree.SetBranchStatus("pos_y",1)
    tree.SetBranchStatus("multiplicity",1)

    selectcmd  = "nfound_channels==32 && multiplicity==1 &&  SignalEnergy > 0"

    drawcmd,drawpos   = get_dcmd()
    print "Draw CMD",  drawcmd
    print "Select CMD for light map",selectcmd
    
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()

    print "Number of selected Events:", n

    chargeEnergy = np.array([tree.GetVal(0)[i] for i in xrange(n)])
    lightEnergy  = np.array([tree.GetVal(1)[i] for i in xrange(n)])
    driftTime    = np.array([tree.GetVal(2)[i] for i in xrange(n)])
    tree.Draw(drawpos,selectcmd,"goff")
    pos_x        = np.array([tree.GetVal(0)[i] for i in xrange(n)])
    pos_y        = np.array([tree.GetVal(1)[i] for i in xrange(n)])


    chargeEnergy = struck_analysis_cuts_sipms.PurityCorrection(driftTime, chargeEnergy, min_time)
    lightCal     = struck_analysis_cuts_sipms.light_cal(min_time)
    lightEnergy *= lightCal#*0.65

    
    #pos_stack = np.vstack((pos_x, pos_y, driftTime)).T
    #print stack
    #print stack.shape
    #raw_input()

    lightEnergyCorr, lm_xyz, lm_array = gen_lightmap(pos_x,pos_y,driftTime,lightEnergy,chargeEnergy,[1,1,11])
    
    raw_input("Pause iter 1")

    #gen_lightmap(pos_x,pos_y,driftTime,lightEnergyCorr,chargeEnergy,[3,3,5])
    gen_lightmap(pos_x,pos_y,driftTime,lightEnergyCorr,chargeEnergy,[1,1,11])

    raw_input("Pause iter 2")

    find_theta=ScanRotationAngle.ScanRotation(chargeEnergy,lightEnergyCorr, 570.0)
    find_theta.setXWin([0,2000])
    find_theta.setBins(180)
    find_theta.setWidth(130)
    find_theta.setGuess(570, 25)
    find_theta.set_theta_list(np.arange(0,0.5, 0.05))
    find_theta.set_make_plots("test")
    find_theta.ScanAngles()
    #find_theta.plotFit()
    
    plt.figure(15)
    min_theta = find_theta.get_best_theta()
    cal       = find_theta.get_cal(find_theta.get_best_theta())
    find_theta.plot_theta(theta=min_theta, filled=True, cal=cal) 
    plt.show()
    
    raw_input()


if __name__ == "__main__":
    filename    =   "/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2_newgains.root"
    #filename  = "/home/teststand/24th_LXe/tier3_added/tier3_added_24th_dn5_dn6_newgains.root"
    process_file(filename)


