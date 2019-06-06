import struck_analysis_parameters
import numpy as np 

def get_default_cut(timeStamp):
    selection = []
    #These are DQ cuts that go for everything
    #Cut only events with all digitizer channels found
    if   timeStamp > 1517449126.0:
        selection.append("nfound_channels==32") #cut the dead channel events 
    elif timeStamp > 1512040104.0:
        selection.append("nfound_channels==30")
    return selection

def get_ss_cut():
    selection = []
    selection.append("nsignals==2")
    selection.append("(nXsignals==1 && nYsignals==1)")
    return selection

def get_chcal_cut(ch):
    selection = get_default_cut()
    selection.append("SignalEnergy > 100")
    selection.append("channel==%i" % ch)
    selection.append("nsignals==1")
    selection.append("(nXsignals==1 || nYsignals==1)")
    selection = " && ".join(selection)
    return selection

def get_fullcal_cut():
    selection = get_default_cut()
    selection.extend(get_ss_cut())
    selection.append("SignalEnergy > 100")
    selection = " && ".join(selection)
    return selection

def get_risetime_cut(rlow=10, rhigh=15):
    selection = []
    selection.append("(rise_time_stop95_sum-trigger_time) > %f" % rlow)
    selection.append("(rise_time_stop95_sum-trigger_time) < %f" % rhigh)
    return selection

def get_std_cut(timeStamp=None):
    selection = get_default_cut(timeStamp)
    selection.extend(get_ss_cut())
    selection.extend(get_risetime_cut(9,15))
    selection.append("SignalEnergy > 200")
    selection = " && ".join(selection)
    return selection

def diag_cut(chargeEnergy,lightEnergy, timeStamp):
    
    if timeStamp > 1517475260.0:
        #13th LXe with 315 bias
        m1 = 6.
        m2 = 3.
        b1 = 2000.
        b2 = 0.0
    elif timeStamp > 1517449126.0:
        #13th LXe with 305 bias
        m1 = 2.8
        m2 = 2.0
        b1 = 2000
        b2 = -500
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
    
    return chargeEnergy[diag_cut], lightEnergy[diag_cut], [m1,b1,m2,b2]

def light_cal(timeStamp):
    #Very rough light calibration to center the anti-correlation blob at ~570 keV (ish)
    #Makes fitting the peak in rotated space slightly easier 

    if timeStamp > 1517475260.0:
        cal = 570.0/3200.0
    elif timeStamp > 1517449126.0:
        cal = 570/1850.0
    elif timeStamp > 1512040104.0:
        cal = 570./2000.
    elif timeStamp == -1:
        cal = 0.905
    elif timeStamp == -2:
        cal = 0.905*3

    return cal

if __name__ == "__main__":
    print "Full Cal Cut", get_fullcal_cut()
    print "Ch   Cal Cut", get_chcal_cut(0)
