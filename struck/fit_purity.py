import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os,sys
import scipy.optimize as opt

import FitPeakPy

plt.ion()
plt.figure(1)

def ffnExp(x,A,t):
    exp  = A*np.exp(-x/t)
    return exp

def get_cut():
    selection = []
    selection.append("SignalEnergy > 0")
    #selection.append("nsignals<=2")
    #selection.append("nXsignals==1")
    #selection.append("nYsignals==1")
    #selection.append("file_start_time>0.5")
    selection = " && ".join(selection)
    return selection


def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    draw_array.append("(rise_time_stop95_sum-trigger_time)")
    draw_array.append("file_start_time")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)


def process_file(filename):
    plt.figure(1)
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())

    bname = os.path.basename(filename).split(".")[0]
    print "Working on", bname
    #field = (bname.split("_"))[-2].split("V.")[0]

    #Speed things up by setting on and off branches
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("SignalEnergy",1)
    #tree.SetBranchStatus("SignalEnergyLight",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("nXsignals",1)
    tree.SetBranchStatus("nYsignals",1)
    #tree.SetBranchStatus("channel",1)
    #tree.SetBranchStatus("energy",1)
    #tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)
    tree.SetBranchStatus("file_start_time",1)

    selectcmd = get_cut()
    drawcmd,nvals   = get_dcmd()

    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()

    data = {}
    for key_index,key in enumerate(drawcmd.split(":")):
        if key=='(rise_time_stop95_sum-trigger_time)': key='drift_time'
        data[key] = np.array([tree.GetVal(key_index)[i] for i in xrange(n)])

    return data

def PeakFind(cents, counts):
    
    for i in xrange(len(counts)-1):
        sigma = np.sqrt(counts[i] + counts[i+1])
        print "PF",cents[i], counts[i], counts[i+1], (counts[i+1] - counts[i])/sigma
        #Is sloping up alot??
        if(counts[i+1] - counts[i])/sigma > 3.0:
            return cents[i]
    
    return -100

def FitPurity(fname, purity_guess, name,color):
    data=process_file(fname)
    data['color']    = color
    data['name']     = name

    if name=='10th': 
        #10th LXe is uncalibrated since it was at 511 V/cm not 1kV/cm
        data['SignalEnergy'] *= 1.14
    
    dt=1
    purity_data = {'dt': [], 'Q':[], 'Qerr':[], 'Qres':[], 'Qres_err':[]}
    
    if 'e2' in name or '24th' in name:
        drift_range = np.arange(1,20,dt)
    else:
        drift_range = np.arange(1,16,dt)

    for drift_time in drift_range:
        drift_cut = np.logical_and(data['drift_time']>drift_time, data['drift_time']<drift_time+dt)
        avg_dt    = drift_time + dt/2.0 
        

        #counts,edges=np.histogram(data['SignalEnergy'][drift_cut], bins=100, range=(70,1300))
        counts,edges=np.histogram(data['SignalEnergy'][drift_cut], bins=150, range=(0,1000))
        cents = edges[:-1] + np.diff(edges)/2.0
        
        plt.figure(2)
        plt.clf()

        #peak_guess = PeakFind(cents, counts)
        #print "Peak Guess", peak_guess
        #raw_input()
        #if peak_guess < 0:continue

        peak_guess = 570*np.exp(-avg_dt/purity_guess)
        if 'e2' in name or '24th' in name:
            peak_guess = 500*np.exp(-avg_dt/purity_guess)
        if '21' in name: 
            peak_guess = 580
        plt.axvline(peak_guess, color='g', linewidth=3, linestyle='-')
        plt.errorbar(cents, counts,   yerr=np.sqrt(counts),
                        marker='o', linestyle='None', c='k', label="%.2f<drift<%.2f" % (drift_time,drift_time+dt))
        
        fitx, bp, bcov, fail, full_fit, gaus,exp = FitPeakPy.FitPeak(counts,
                                                                     np.sqrt(counts),
                                                                     cents, peak_guess, 150,sigma_guess=40)

        print "PEAK FIT", bp
        print fail
        print bcov, (type(bcov) != np.ndarray)

        if type(bcov) != np.ndarray or fail:
            purity_data['dt'].append(-1.)
            purity_data['Q'].append(-1.)
            purity_data['Qerr'].append(-1.)
            purity_data['Qres'].append(-1.)
            purity_data['Qres_err'].append(-1.)
        else:
            purity_data['dt'].append(avg_dt)
            purity_data['Q'].append(bp[1])
            purity_data['Qerr'].append(bcov[1,1]**0.5)
            purity_data['Qres'].append(abs(bp[2]/bp[1]))
            purity_data['Qres_err'].append((bcov[2,2]**0.5)/bp[1])


        plt.plot(fitx, full_fit, color='r', linewidth=3, linestyle='-')
        plt.plot(fitx, gaus, color='c', linewidth=3, linestyle='-')
        plt.legend(loc='upper right')
        plt.xlim(100,700)
        print np.max(counts), np.max(counts[np.logical_and(cents>100, cents<700)])
        plt.ylim(0.0, np.max(counts[np.logical_and(cents>100, cents<700)])*1.05)
        plt.grid(True)
        #if 'e2' in name: raw_input("PAUSE")
        plt.savefig("./plots/spectrum_drift%i_%s.png" % (int(avg_dt),data['name']))

    for key in purity_data:
        purity_data[key]=np.array(purity_data[key])
        purity_data[key]=purity_data[key][purity_data[key]>0]

    plt.figure(3, figsize=(10,7))
    
    plt.errorbar(purity_data['dt'], purity_data['Q'], yerr=purity_data['Qerr'], marker='o', linestyle='None', c=color, ms=8)
    bp, bcov = opt.curve_fit(ffnExp, purity_data['dt'], purity_data['Q'], sigma=purity_data['Qerr'], p0=[600,20.0])
    

    dt_fit = np.arange(0,16.1,0.01)
    if 'e2' in name or '24th' in name:
        dt_fit = np.arange(0,19.1,0.01)
    if bp[1] > 1000:
        plt.plot(dt_fit, ffnExp(dt_fit, bp[0], bp[1]), 
                label=r'%s ($\tau_{e}$ = %.2E $\mu$s)' % (name,bp[1]), color=color)
    else:
        plt.plot(dt_fit, ffnExp(dt_fit, bp[0], bp[1]), 
                label=r'%s ($\tau_{e}$ = %.2f $\pm$ %.2f $\mu$s)' % (name,bp[1], np.sqrt(bcov[1,1])), color=color)
    
    plt.title("570keV Peak vs Drift Time", fontsize=17)
    plt.ylabel("Peak Position", fontsize=17)
    plt.xlabel(r"Drift Time [$\mu$s]", fontsize=17)
    
    print "PURITY FIT", bp
    #plt.xlim(0,16)
    plt.xlim(0, 20)
    plt.ylim(50,850)
    data['life_fit'] = bp[1]

    plt.grid(True)
    plt.legend(loc='upper right', ncol=2)
    plt.savefig("./plots/purity_fit.png") 
    #raw_input("PURITY PAUSE")

    plt.figure(33, figsize=(10,7))

    print len(purity_data['dt']), len(purity_data['Qres'])

    plt.errorbar(purity_data['dt'], purity_data['Qres']*100, yerr=purity_data['Qres_err']*100, 
                    marker='o', linestyle='None', c=color, ms=8, label='%s' % (name))
    
    #plt.xlim(0,16)
    plt.xlim(0,20)
    plt.ylim(5,13)
    plt.title("570keV Peak Res vs Drift Time", fontsize=17)
    plt.ylabel("Res (@570keV)", fontsize=17)
    plt.xlabel(r"Drift Time [$\mu$s]", fontsize=17)
    plt.legend(loc='upper right', ncol=2)
    plt.grid(True)
    plt.savefig("./plots/purity_fit_res.png")

    return data

def CompareSpectra(data_list):

    plt.figure(50)
    for data in data_list:
        counts,edges=np.histogram(data['SignalEnergy'], bins=120, range=(70,1200))
        cents = edges[:-1] + np.diff(edges)/2.0

        norm = 1.0/np.sum(counts)
        plt.errorbar(cents, counts*norm,   yerr=np.sqrt(counts)*norm, 
                     linewidth=2, drawstyle='steps-mid', label=data['name'],  color=data['color'])

    plt.grid(True)
    plt.xlim(100,1200)
    plt.ylim(0,0.03)
    plt.legend(loc='upper right')
    plt.ylabel("Norm Counts", fontsize=17)
    plt.xlabel("Charge Energy", fontsize=17)
    plt.show()
    plt.savefig("plots/compare_spectra.png")



def FitTime(data):
    run_start = np.min(data['file_start_time'])
    run_end   = np.max(data['file_start_time'])
    
    dt = 3600
    #dt  = 3600*2
    run_duration = (run_end - run_start)
    time_data = {'tp': [], 'Q':[], 'Qerr':[]}
 
    for i in xrange(int(np.ceil(run_duration/(dt)))):
        run_cut = np.logical_and(data['file_start_time']>run_start+i*dt, data['file_start_time']<run_start+(i+1)*dt)
        #print i, len(data['SignalEnergy'][run_cut])
        drift_cut = np.logical_and(data['drift_time']>10, data['drift_time']<16)
        
        total_cut = np.logical_and(run_cut, drift_cut)
        
        if np.sum(total_cut) < 1.0:continue

        counts,edges=np.histogram(data['SignalEnergy'][total_cut], bins=120, range=(70,1200))
        cents = edges[:-1] + np.diff(edges)/2.0

        plt.figure(4)
        plt.clf()
        peak_guess = 570*np.exp(-(15)/data['life_fit'])
        plt.axvline(peak_guess, color='g', linewidth=3, linestyle='-')
        plt.errorbar(cents, counts,   yerr=np.sqrt(counts),
                      marker='o', linestyle='None', c='k')

        fitx, bp, bcov, fail, full_fit, gaus,exp = FitPeakPy.FitPeak(counts,
                                                                     np.sqrt(counts),
                                                                     cents, peak_guess, 150)

        plt.plot(fitx, full_fit, color='r', linewidth=3, linestyle='-')

        plt.plot(fitx, gaus, color='c', linewidth=3, linestyle='-', label='%.2f'%bp[1])
        plt.grid(True)

        plt.savefig("./plots/spectrum_time%i_%s.png" % (i,data['name']))
        raw_input("Pause")

        #print "Did I fail", fail, bcov[1,1]
        if not fail:
            time_data['tp'].append(((i+0.5)*dt/3600.0))
            time_data['Q'].append(bp[1])
            time_data['Qerr'].append((bcov[1,1])**0.5)
        #else:
        #    continue
        #    time_data['tp'].append(((i+0.5)*dt/3600.0))
        #    time_data['Q'].append(0.0)
        #    time_data['Qerr'].append(0.0)

        plt.figure(6)
        if i%4 == 0: 
            norm = 1.0/np.sum(counts)
            plt.errorbar(cents, counts*norm,   yerr=np.sqrt(counts)*norm,
                         linewidth=2, drawstyle='steps-mid', label='%.2f hr' % ((i+1)*dt/3600.0))
        
        #if '19th' in data['name']:
        #    plt.show()
        #    raw_input("PAUSE2")
    
    plt.figure(6)
    plt.title("Charge Spectrum (10us<drift<16us)", fontsize=17)
    plt.xlim(70, 900)
    plt.ylim(0.0, 0.035)
    plt.grid(True)
    plt.ylabel("Norm Counts", fontsize=17)
    plt.xlabel("Charge Energy", fontsize=17)
    plt.legend()
    plt.show()
    plt.savefig("./plots/spectrum_over_time_%s.png" % data['name'])

    for key in time_data:
        time_data[key]=np.array(time_data[key])

    plt.figure(5)
    plt.clf()

    plt.errorbar(time_data['tp'], time_data['Q'], yerr=time_data['Qerr'], marker='o', linestyle='None', ms=6)

    if data['name'] == '22nd(Full)':
        plt.axvline(18.0, linestyle='--', linewidth=3, color='r')
        plt.axvline(28.0, linestyle='--', linewidth=3, color='r')
    
    plt.xlabel("Hours Since Start [hrs]", fontsize=17)
    plt.ylabel("Peak Position", fontsize=17)
    plt.grid(True)
    plt.savefig("./plots/peak_vs_time_%s.png" % data['name'])

    #raw_input("PAUSE3")
    plt.figure(6)
    plt.clf()
    
def Run():

    #fname="/home/teststand/10th_LXe/overnight10thLXe_v3.root"
    #data=FitPurity(fname, purity_guess=1.e6, name='10th', color='y')
    #FitTime(data)


    #fname="/home/teststand/23rd_LXe/tier3_all/tier3_23rd.root"
    #data=FitPurity(fname, purity_guess=50.0, name='23rd', color='orange')
    #FitTime(data)    
    #raw_input("PAUSE")
    #sys.exit()

    #fname = "/home/teststand/22nd_LXe/overnight_4_17_2019/tier3_added/tier3_22nd_overnight_4_17_2019_v1.root"
    #datan1  = FitPurity(fname, purity_guess=50.0, name='22nd-n1', color='orange')
    
    #fname = "/home/teststand/22nd_LXe/overnight_4_18_2019_aftercirc/tier3_added/tier3_added_22nd_overnight2_aftercirc.root"
    #datan2  = FitPurity(fname, purity_guess=50.0, name='22nd-n2', color='blue')
    
    #fname  = "/home/teststand/22nd_LXe/day_testing_4_18_2019_recirc/tier3_added/tier3_dayruns_recirc_4_18_2019.root"
    #datad1 = FitPurity(fname, purity_guess=50.0, name='22nd-d1', color='red')

    #fname = "/home/teststand/22nd_LXe/day_testing_4_19_2019_newfield/tier3_added/tier3_added_22nd_1320V_v1.root"
    #datae2  = FitPurity(fname, purity_guess=100.0, name='22nd-e2', color='green')

    #fname = "/home/teststand/21st_LXe/overnight_run_3_29_2019/tier3_added/tier3_added_21st_overnight_3_29_2019_v1.root"
    #data  = FitPurity(fname, purity_guess=1.e3, name='21st', color='k')

    #CompareSpectra([datan1, datad1, datan2, datae2])
    #raw_input("PAUSE")
    #sys.exit()

    #fname = "/home/teststand/19th_LXe/day_testing_2_20_2019/tier3_added/tier3_added_2_20_2019_day2_v1.root"
    #fname = "/home/teststand/19th_LXe/tier3_added_day1_overnight1_day2_19th_v1.root"
    #data=FitPurity(fname, purity_guess=23.0, name='19th_full', color='r')
    #data['life_fit'] = 23.0
    #FitTime(data)
    #raw_input()

    #fname = "/home/teststand/20th_LXe/day_testing_2_25_2019/tier3_added/tier3_added_day_2_26_2019_v1.root"
    #data  = FitPurity(fname, purity_guess=15, name='20th', color='purple')
    #raw_input("PPAUSE")

    fname="/home/teststand/11th_LXe/2017_02_01_overnight_vme/tier3_added/tier3_combined_rise10.root"
    #data=FitPurity(fname, purity_guess=1.e6, name='11th', color='r')
    #FitTime(data)

    fname="/home/teststand/12th_LXe/overnight_new_bias_tier3_all_v4_12_7_2017.root"
    #data=FitPurity(fname, purity_guess=1000, name='12th', color='m')
    #FitTime(data)
    
    fname="/home/teststand/13thLXe/all_tier3_overnight_day2_315bias_v3.root"
    #data=FitPurity(fname, purity_guess=1000, name='13th', color='b')
    #FitTime(data)
 
    #fname="/home/teststand/15th_LXe/overnight_fullCell/tier3_added/tier3_allData_v1.root"
    #fname="/home/teststand/15th_LXe/overnight_fullCell/tier3_added/tier3_added_15th_thresh15.root"
    fname = "/home/teststand/16th_LXe/tier3_added_overnight_16th_thresh15.root"
    #data=FitPurity(fname, purity_guess=6.2, name='16th', color='m')
    #FitTime(data)

    #fname="/home/teststand/17th_LXe/overnight_12_18_2018/tier3_added/tier3_added_overnight_12_18_2018_17th_thresh15.root"
    #fname = "/home/teststand/17th_LXe/tier3_added_day+overnight_thresh15.root"
    #data=FitPurity(fname, purity_guess=14.0, name='17th', color='g')
    #FitTime(data)

    #fname="/home/teststand/18th_LXe/overnight_1_22_2019/tier3_added/tier3_added_overnight_18th_1_23_2019_thresh15.root"
    #fname="/home/teststand/18th_LXe/tier3_added_day+overnight_18th.root"
    #data=FitPurity(fname, purity_guess=23.0, name='18th', color='c')
    #FitTime(data)
 
    #fname="/home/teststand/19th_LXe/overnight_2_19_2019/tier3_added/tier3_added_overnight_19th_thresh15_v1.root"
    #data=FitPurity(fname, purity_guess=23.0, name='19thA', color='y')
    #FitTime(data)
    

    #fname="/home/teststand/19th_LXe/overnight_2_20_2019/tier3_added/tier3_added_overnight_2_20_2019_19th_v1.root"
    #data=FitPurity(fname, purity_guess=23.0, name='19thB', color='purple')
    #FitTime(data)
    
    #fname="/home/teststand/19th_LXe/tier3_added_overnight1+2_19th_v1.root"
    #data=FitPurity(fname, purity_guess=23.0, name='19th', color='y')
    #FitTime(data)

    #fname = "/home/teststand/20th_LXe/day_testing_2_25_2019/tier3_added/tier3_added_day_2_26_2019_v1.root"
    #fname = "/home/teststand/20th_LXe/overnight_2_25_2019/tier3_added/tier3_added_overnigh_2_26_2019_v1.root"
    
    #fname = "/home/teststand/20th_LXe/tier3_added_day1_overnight1_20th_v1.root"
    #data  = FitPurity(fname, purity_guess=15, name='20th', color='purple')
    #FitTime(data)

    fname = "/home/teststand/21st_LXe/overnight_run_3_29_2019/tier3_added/tier3_added_21st_overnight_3_29_2019_v1.root"
    #data  = FitPurity(fname, purity_guess=1.e3, name='21st', color='pink')
    #FitTime(data)


    fname = "/home/teststand/22nd_LXe/overnight_4_17_2019/tier3_added/tier3_22nd_overnight_4_17_2019_v1.root"
    #data  = FitPurity(fname, purity_guess=50.0, name='22nd', color='orange')
    #FitTime(data)

    fname = "/home/teststand/23rd_LXe/tier3_all/tier3_23rd.root"
    #data  = FitPurity(fname, purity_guess=200.0, name='23rd', color='yellow')
    #FitTime(data)
    
    fname = "/home/teststand/24th_LXe/tier3_added/tier3_added_24th_dn5_dn6.root"
    data=FitPurity(fname, purity_guess=1.e3, name='24th', color='orange')
    FitTime(data)


    raw_input("END PAUSE")

    return

if __name__ == "__main__":
    Run()


