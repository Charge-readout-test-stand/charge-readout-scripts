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
import cPickle as pickle


drift_length = 33.0
plt.ion()

def lightmap(x,y,drift_time,light_energy,charge_energy,cut,n_bin):
    #cut_energy = (cut[0]<charge_energy) & (charge_energy<cut[1]) & (50<light_energy) & (light_energy<340)
    cut_energy  = np.logical_and((cut[0]<charge_energy), (charge_energy<cut[1]))
    light_cut   = np.logical_and(light_energy<1000, light_energy>200)
    cut_energy  = np.logical_and(cut_energy, light_cut)

    drift_time_cut    = drift_time[cut_energy]
    light_energy_cut  = light_energy[cut_energy]
    charge_energy_cut = charge_energy[cut_energy] 

    pos_x_cut = x[cut_energy]
    pos_y_cut = y[cut_energy]
    
    counts,bn = np.histogram(drift_time_cut,bins=50,range=(1,30))
    drift_velocity = drift_length/bn[0:][np.argmax(counts)]
    print "Drift velocity is", drift_velocity, bn[0:][np.argmax(counts)]

    pos_z = drift_velocity*drift_time_cut
    
    lim_x = np.linspace(pos_x_cut.min(),pos_x_cut.max(),n_bin)
    lim_y = np.linspace(pos_y_cut.min(),pos_y_cut.max(),n_bin)
    lim_z = np.linspace(0.0,35.0,n_bin+1)
    
    bin_x_cut = np.digitize(pos_x_cut,lim_x)
    bin_y_cut = np.digitize(pos_y_cut,lim_y)
    bin_z_cut = np.digitize(pos_z,lim_z)
    
    vxl = np.array((bin_x_cut,bin_y_cut,bin_z_cut)).T
    mean_light_energy = np.mean(light_energy_cut)
    mean_light_energy = 570.0
    ly_matrix = np.ones((n_bin+1,n_bin+1,n_bin+2))
    #n_light_ev = np.zeros((n_bin+1,n_bin+1,n_bin+2))

    for i,vl in enumerate(itertools.product(np.arange(n_bin)+1,np.arange(n_bin)+1,np.arange(n_bin+1)+1)):
        selection_idx = np.where(np.sum((vxl == vl).reshape(-1,3),axis=1) == 3)[0]

        #print vl
        #print lim_x[vl[0]-1], lim_y[vl[1]-1], lim_z[vl[2]-1]

        if  selection_idx.shape[0] == 0: continue

        light_energy_voxel = light_energy_cut[selection_idx]
        ly_matrix[vl[0],vl[1],vl[2]] = mean_light_energy/np.mean(light_energy_voxel)
        #ly_matrix[vl[0],vl[1],vl[2]] = np.mean(light_energy_voxel)
        #n_light_ev[vl[0],vl[1],vl[2]] = selection_idx.shape[0]

        plt.figure(1)

        plt.clf()
        
        plt.hist2d(charge_energy_cut[selection_idx], light_energy_cut[selection_idx], 
                    bins=[25,25], range=[[570-100,570+100],[200,1000]],
                    norm=colors.LogNorm(vmin=1,vmax=100))
    

        #print len(charge_energy_cut[selection_idx]), np.mean(charge_energy_cut[selection_idx]), np.mean(light_energy_voxel)
        plt.plot(np.mean(charge_energy_cut[selection_idx]), np.mean(light_energy_voxel), 
                    marker='x', ms=30, mew=7, color='r')

        plt.title("Ents=%i, Pos=(%.2f, %.2f, %.2f)" % (len(charge_energy_cut[selection_idx]),lim_x[vl[0]-1], lim_y[vl[1]-1], drift_length-lim_z[vl[2]-1]))

        plt.savefig("./plots/lightmap/ac_plot_%i_%i_%i.png" % (vl[0]-1,vl[1]-1,vl[2]-1))

        plt.show()   
        #raw_input("PAUSE")



    return ly_matrix,lim_x,lim_y,lim_z,drift_velocity

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

    #selectcmd  =  struck_analysis_cuts_sipms.get_cut_norise(min_time)
    #if '1320' in filename or '24th' in filename:
    #    selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(14,18))
    #else:
    #    selectcmd = selectcmd + " && " + " && ".join(struck_analysis_cuts_sipms.get_risetime_cut(12,15))

    #selectcmd  = "nfound_channels==32 && multiplicity==1 && nsignals==2 && SignalEnergy > 0"
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
 
    plt.figure(3)

    plt.hist2d(chargeEnergy, lightEnergy, bins=[100,100], range=[[570-100,570+100],[200,800]], 
                norm=colors.LogNorm(vmin=1,vmax=500))    
    

    plt.figure(33)
    plt.hist2d(chargeEnergy, lightEnergy, bins=[100,100], range=[[1100-150,1100+150],[500,1600]],
                norm=colors.LogNorm(vmin=1,vmax=500))


    plt.show()

    print lightCal

    ly_matrix,lim_x,lim_y,lim_z,drift_velocity = lightmap(pos_x,pos_y,driftTime,lightEnergy,chargeEnergy,(490,650),6)
    
    pfile = open('data/light_map_file.p','wb')
    pickle.dump(ly_matrix,pfile)
    pickle.dump(lim_x,pfile)
    pickle.dump(lim_y,pfile)
    pickle.dump(lim_z,pfile)
    pickle.dump(drift_velocity,pfile)
    pfile.close()

    pos_z = driftTime*drift_velocity
    lightEnergy = apply_light_map(ly_matrix,pos_x,pos_y,pos_z,lim_x,lim_y,lim_z)*lightEnergy


    plt.figure(4)
    
    plt.hist2d(chargeEnergy, lightEnergy, bins=[100,100], range=[[570-100,570+100],[200,800]],
                norm=colors.LogNorm(vmin=1,vmax=500))


    plt.figure(44)
    plt.hist2d(chargeEnergy, lightEnergy, bins=[100,100], range=[[1100-150,1100+150],[500,1600]],
                norm=colors.LogNorm(vmin=1,vmax=500))

    plt.show()

    raw_input("PAUSE-2")


if __name__ == "__main__":
    filename    =   "/home/teststand/23rd_LXe/tier3_all/tier3_added_23rd_dn2_newgains.root"
    process_file(filename)


