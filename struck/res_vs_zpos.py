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

plt.ion()

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
    selectcmd  =  struck_analysis_cuts_sipms.get_cut_norise(min_time)
    
    #if '24th' in filename: selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(14,18))
    #else: selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(14,15))

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

    chargeEnergy = struck_analysis_cuts_sipms.PurityCorrection(driftTime, chargeEnergy, min_time)
    lightCal = struck_analysis_cuts_sipms.light_cal(min_time)
    lightEnergy    *= lightCal#*0.65

    drift_vel = struck_analysis_cuts_sipms.get_drift_vel(driftTime)
    pos_z     = driftTime*drift_vel

    dz=3
    for z in np.arange(0, 33, dz):
        zwin = [z,z+dz]
        
        zcut = np.logical_and(pos_z > zwin[0], pos_z< zwin[1])
#===============================================
        if True:
            theta_scan_nodiag1 = ScanRotationAngle.ScanRotation(chargeEnergy[zcut], lightEnergy[zcut], 
                                                                570.0, "nodiag_%s_570"%bname)
            plt.figure(999)
            plt.clf()
            plot_ac(theta_scan_nodiag1)
            #run_scan_570(theta_scan_nodiag1)
    
            #theta_scan_nodiag2 = ScanRotationAngle.ScanRotation(chargeEnergy, lightEnergy, 1060.0, "nodiag_%s_1060"%bname)
            #run_scan_1060(theta_scan_nodiag2)

#===============================================
        #For the diagnoal cut case
        chargeEnergyCut, lightEnergyCut, diag_parms, diag_cut =  struck_analysis_cuts_sipms.diag_cut(chargeEnergy[zcut],
                                                                                                     lightEnergy[zcut], 
                                                                                                     min_time)
    
        theta_scan_diag1 =  ScanRotationAngle.ScanRotation(chargeEnergyCut, lightEnergyCut, 570.0, "diag_%s_570"%bname)
        plt.figure(190)
        plt.clf()
        plot_ac(theta_scan_diag1)
        run_scan_570(theta_scan_diag1)
        plt.figure(191)
        plt.clf()
        theta_scan_diag1.plot_theta(filled=False, color='k')
        plt.title("%.2fmm<Z<%.2fmm" % (zwin[0], zwin[1]))

        theta_scan_diag2 =  ScanRotationAngle.ScanRotation(chargeEnergyCut, lightEnergyCut, 1060.0, "diag_%s_1060"%bname)
        run_scan_1060(theta_scan_diag2)
        plt.figure(192)
        plt.clf()
        theta_scan_diag2.plot_theta(filled=False, color='k')

#===============================================
        
        plt.show()
        raw_input()

def plot_ac(scanner):
    scanner.plot2D(100,[0,1500], 100, [0,1500], vmax=100)
    plt.xlabel("Charge Energy [keV]", fontsize=15)
    plt.ylabel("Light Energy [keV]", fontsize=15)
    plt.colorbar()
    

def run_scan_570(scanner):
    scanner.setXWin([0,1500])
    scanner.setBins(200)
    scanner.setWidth(130)
    scanner.setGuess(570, 20)
    scanner.set_theta_list(np.arange(0,0.6, 0.05))
    scanner.ScanAngles()

def run_scan_1060(scanner):
    scanner.setXWin([0,1500])
    scanner.setBins(200)
    scanner.setWidth(170)
    scanner.setGuess(1075, 25)
    scanner.set_theta_list(np.arange(0,0.6, 0.05))
    scanner.ScanAngles()
    

if __name__ == "__main__":
    filename    =   "/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2_newgains.root"
    process_file(filename)


