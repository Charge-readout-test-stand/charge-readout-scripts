import struck_analysis_parameters
import numpy as np 

def get_min_time(runtree):
    runtree.SetEstimate(runtree.GetEntries())
    runtree.Draw("file_start_time","","goff")
    n = runtree.GetSelectedRows()
    start_times = np.array([runtree.GetVal(0)[i] for i in xrange(n)])
    min_time = np.min(start_times)
    return min_time

def get_default_cut(timeStamp):
    selection = []
    #These are DQ cuts that go for everything
    #Cut only events with all digitizer channels found
    if   timeStamp > 1517381996.0:#1517449126.0:
        selection.append("nfound_channels==32") #cut the dead channel events 
    elif timeStamp > 1512040104.0:
        selection.append("nfound_channels==30")
    return selection

def get_ss_cut():
    selection = []
    selection.append("nsignals==2")
    selection.append("(nXsignals==1 && nYsignals==1)")
    return selection

def get_chcal_cut(ch, timeStamp):
    selection = get_default_cut(timeStamp)
    selection.append("SignalEnergy > 100")
    selection.append("channel==%i" % ch)
    selection.append("nsignals==1")
    selection.append("(nXsignals==1 || nYsignals==1)")
    selection = " && ".join(selection)
    return selection

def get_fullcal_cut(timeStamp):
    selection = get_default_cut(timeStamp)
    selection.extend(get_ss_cut())
    selection.append("SignalEnergy > 100")
    selection = " && ".join(selection)
    return selection

def get_risetime_cut(rlow=10, rhigh=15):
    selection = []
    selection.append("(rise_time_stop95_sum-trigger_time) > %f" % rlow)
    selection.append("(rise_time_stop95_sum-trigger_time) < %f" % rhigh)
    return selection

def get_std_cut(timeStamp):
    selection = get_default_cut(timeStamp)
    selection.extend(get_ss_cut())
    selection.extend(get_risetime_cut(9,15))
    selection.append("SignalEnergy > 200")
    selection = " && ".join(selection)
    return selection

def get_cut_norise(timeStamp):
    selection = get_std_cut(timeStamp)
    selection_new = []
    for select in selection.split(" && "):
        if 'rise_time' in select: continue
        selection_new.append(select)
    selection = " && ".join(selection_new)
    return selection

def diag_cut(chargeEnergy,lightEnergy, timeStamp):
    if timeStamp > 1557998400.0:
        m1 = 0.85#6.
        m2 = 0.55#3.
        b1 = 600.0#2000.
        b2 = -50#0.0

    elif timeStamp > 1555372800.0:
        #22nd LXe with 315 bias
        m1 = 0.85#6.
        m2 = 0.55#3.
        b1 = 400.0#2000.
        b2 = -50#0.0
    elif timeStamp > 1517475260.0:
        #13th LXe with 315 bias
        m1 = 0.8#6.
        m2 = 0.55#3.
        b1 = 500.0#2000.
        b2 = -50#0.0
    elif timeStamp > 1517381996.0:
        #13th LXe with 305 bias
        m1 = 0.9
        m2 = 0.5
        b1 = 450
        b2 = -50
    elif timeStamp > 1512040104.0:
        #12th LXe with 305 bias
        m1 = 2.8
        m2 = 2.0
        b1 = 2250
        b2 = 0.0
    elif timeStamp < 0:
        m1 = 1.25
        m2 = 0
        b1 = 250.0
        b2 = 0

    diag_high = m1*chargeEnergy + b1
    diag_low  = m2*chargeEnergy + b2

    diag_cut = np.logical_and(diag_low < lightEnergy, diag_high > lightEnergy)
    
    return chargeEnergy[diag_cut], lightEnergy[diag_cut], [m1,b1,m2,b2], diag_cut

def light_cal(timeStamp):
    #Very rough light calibration to center the anti-correlation blob at ~570 keV (ish)
    #Makes fitting the peak in rotated space slightly easier 
    
    if    timeStamp > 1555706938:
        #22nd but 1320V/cm
        cal = 570.0/200.0
    elif  timeStamp > 1555372800:
        #April 16th (22nd LXe)
        #cal = 570.0/229.0 #without SiPM FFT Filter
        cal = 570.0/150.0 #With SiPM FFT Filter 
    elif timeStamp > 1517475260.0:
        cal = 570.0/3200.0
    elif timeStamp > 1517449126.0: #1517381996.0
        cal = 570/1850.0
    elif timeStamp > 1512040104.0:
        cal = 570./2000.
    elif timeStamp == -1:
        cal = 0.905
    elif timeStamp == -2:
        cal = 0.905*3
    return cal

def get_theta(timeStamp):
    if timeStamp > 1517475260.0:
        theta =  0.19312782843
    elif timeStamp > 1517381996.0:
        theta = 0.198309182675 
    elif timeStamp > 1512040104.0:
        theta = 0.198331320193
    return theta

def rot_cal(timeStamp):
    if timeStamp > 1517475260.0:
        cal = 1.00897086599
    elif timeStamp > 1517381996.0:
        cal = 1.0207306731
    elif timeStamp > 1512040104.0:
        cal= 1.0128243962
    return cal

def charge_cal(timeStamp):
    if timeStamp > 1517475260.0:
        cal = 1.01823515268
    elif timeStamp > 1517381996.0:
        cal =  1.01263212249
    elif timeStamp > 1512040104.0:
        cal= 1.0309595724
    return cal

def PurityCorrection(driftTime, chargeEnergy, timeStamp):
    
    if timeStamp >   1555706938:
        lifetime = 184.0
    elif timeStamp > 1555372800.0:
        lifetime = 50.0
    else:
        lifetime = np.inf

    corr = np.exp(-driftTime/lifetime)
    return chargeEnergy/corr

def LightCorrect(driftTime, lightEnergy, timeStamp):
    
    if timeStamp > 1517475260.0:
        A = 790.7632857 
        B = 12.34331533
    elif timeStamp > 1517449126.0:
        A = 1.0
        B = np.inf
    elif timeStamp > 1512040104.0:
        A = 812.00679879
        B = 13.36824103

    corr=np.exp(-(struck_analysis_parameters.max_drift_time-driftTime)/B)
    return (lightEnergy/corr)*(570.0/A)

if __name__ == "__main__":
    print "Full Cal Cut", get_fullcal_cut()
    print "Ch   Cal Cut", get_chcal_cut(0)
