import os
import numpy as np
import matplotlib.pyplot as plt
import ROOT
import MakeTile
import math

posion  = True #Use Positive Ion
cathsupress = True #Use Cathode Supression
cathodeToAnodeDistance = 18.16 # + 16 # mm
#cathodeToAnodeDistance = 1000.0 # mm
#cathodeToAnodeDistance = 33.23 # mm
drift_velocity = 2.0 # mm/microsecond
sampling_period = 0.04 # microseconds, 40 ns
e_lifetime=None # e- lifetime, microseconds
consider_capturedQ=False # electrons captured on impurities

def f(xi, yi, h):
    inside = (xi*yi)/(h*np.sqrt(xi*xi + yi*yi + h*h))
    return np.arctan(inside)

def Q_rot(xpcd, ypcd, zpcd, chx, chy):
    #Get the induced Charge at (x,y,z) using analytic solution from Ralph
    #Just one pad located at chx,chy

    l = 3.0 #3mm on the diagonal

    #Rotate into the Rectangles Frame for this calculation
    #45degrees
    xpcdn = (np.sqrt(2)/2)*(xpcd - ypcd)
    ypcdn = (np.sqrt(2)/2)*(xpcd + ypcd)
    
    chxn = (np.sqrt(2)/2)*(chx - chy)
    chyn = (np.sqrt(2)/2)*(chx + chy)

    chx = chxn
    chy = chyn

    #Assume the charge is centered at (0,0)
    #And the Diagonal is 3mm
    #Find the Corners of the Square
    x1 = chx - l/(2*np.sqrt(2))
    y1 = chy - l/(2*np.sqrt(2))
    x2 = chx + l/(2*np.sqrt(2))
    y2 = chy + l/(2*np.sqrt(2))

    #Shift so that the charge is at (0,0)
    f22 = f(x2 - xpcdn, y2 - ypcdn, zpcd)
    f12 = f(x1 - xpcdn, y2 - ypcdn, zpcd)
    f21 = f(x2 - xpcdn, y1 - ypcdn, zpcd)
    f11 = f(x1 - xpcdn,  y1 - ypcdn, zpcd)

    return (f22 - f21 - f12 + f11)*(1/(2*np.pi))


def sum_channel(xpcd,ypcd,zpcd,chID,chx,chy):
    #xpcd,ypcd,zpcd --- x,y,z of intial pcd
    #z = 0 is cathode 18.16 is anode for 7th LXe
    #chID is ID for channel < 30 is X Channel
    #chx, chy is x,y pos of channel
    
    #Use rotated channel positions
    if(chID < 30): chy = -42.0 #this is weird but trust me
    else: chx = -42.0 #weird but works 1.5 offset
    Q = 0
    for n in np.arange(0,30,1):
        Q += Q_rot(xpcd, ypcd, zpcd, chx, chy)
        if(chID < 30):
            #Its a xChannel
            chy += 3.0
        else:
            #Its a yChannel
            chx += 3.0
    return Q

def make_WF(xpcd, ypcd, zpcd, Epcd, chID, 
    cathodeToAnodeDistance=cathodeToAnodeDistance,
    #dZ=cathodeToAnodeDistance/100.0, # 100 steps per full drift
    dZ=sampling_period*drift_velocity, # one step per digitizer sample
    wfm_length=800,
    ):

    """
    Calculate the instantaneous induced charge at each point in time. 
    """

    # return waveform array

    #xch_list, ych_list =  np.loadtxt("/nfs/slac/g/exo/mjewell/nEXO/nEXO_Analysis/utilities/scripts/localChannelsMap.txt", usecols = (1,2) ,unpack=True)

    directory = os.path.dirname(__file__) # directory containing this script

    xch_list, ych_list =  np.loadtxt(
            "%s/localChannelsMap.txt" % directory, 
            usecols = (1,2),
            unpack=True)


    chx = xch_list[chID]
    chy = ych_list[chID]
    WF = np.zeros(wfm_length)

    #Ralph's anode is at z = 0.0mm
    zpcd = cathodeToAnodeDistance - zpcd
    
    ionQ = sum_channel(xpcd,ypcd,zpcd,chID,chx,chy)
    
    #Cathode Supression
    #Anode at z = 0 has no supression
    if cathsupress: ionQ = ionQ*(cathodeToAnodeDistance-zpcd)/cathodeToAnodeDistance

    # electron lifetime:
    z0 = zpcd # initial z position
    capturedQ = 0.0 # for electrons captured on impurities

    #cathodeToAnodeDistance is top in Dave's COMSOL
    #0 is top in Ralph's??
    ki = 0
    for k in np.arange(ki,len(WF),1):    
        zpcd -= dZ
        if zpcd < 0: zpcd = 0.0
        if e_lifetime != None:
            drift_time = (z0-zpcd)/drift_velocity # so far
            #exp_factor = math.exp(-drift_time/e_lifetime)
            frac_captured = 1.0 - math.exp(-dZ/drift_velocity/e_lifetime)
            if False: # debugging
                print "z: %.1f | drift_time: %.1f | exp_factor: %.3f | frac_captured: %.3f | capturedQ: %.3f" % (
                    zpcd,
                    drift_time,
                    exp_factor,
                    frac_captured,
                    capturedQ,
                )
        if(zpcd <= 0.0):
            Q = sum_channel(xpcd,ypcd,0.00001,chID,chx,chy) 
            if e_lifetime != None: Q = Q*exp_factor
            if cathsupress: Q = Q*(cathodeToAnodeDistance-zpcd)/cathodeToAnodeDistance
            if e_lifetime != None and consider_capturedQ: 
                capturedQ += Q*frac_captured
                Q += capturedQ
            if posion: Q -= ionQ
            WF[k:] = Q*Epcd # set rest of waveform to final value
            break
        else:
            Q = sum_channel(xpcd,ypcd,zpcd,chID,chx,chy) 
            if e_lifetime: Q = Q*exp_factor
            if cathsupress: Q = Q*(cathodeToAnodeDistance-zpcd)/cathodeToAnodeDistance
            if e_lifetime and consider_capturedQ: 
                capturedQ += Q*frac_captured
                Q += capturedQ
            if posion: Q -= ionQ
            WF[k] = Q*Epcd
 
    return WF


def df_dh(xi, yi, h):
    # derivative of f with respect to h
    # from Mathematica, df/dt = df/dh*dh/dt = -drift_velocity*df/dh
    # alexis's RalphCurrent.nb on corn, in bucket/farmShare
    val = -(xi*yi* (xi*xi + yi*yi + 2*h*h))/((xi*xi+h*h)*(yi*yi+h*h)*np.sqrt(xi*xi + yi*yi + h*h))
    return val

def I_rot(xpcd, ypcd, zpcd, chx, chy):
    # current divided by drift_velocity [charge/mm], from one pad
    # modified from Q_rot

    l = 3.0 #3mm on the diagonal

    #Rotate into the Rectangles Frame for this calculation
    #45degrees
    xpcdn = (np.sqrt(2)/2)*(xpcd - ypcd)
    ypcdn = (np.sqrt(2)/2)*(xpcd + ypcd)
    
    chxn = (np.sqrt(2)/2)*(chx - chy)
    chyn = (np.sqrt(2)/2)*(chx + chy)

    chx = chxn
    chy = chyn

    #Assume the charge is centered at (0,0)
    #And the diagonal is 3mm
    #Find the Corners of the Square
    x1 = chx - l/(2*np.sqrt(2))
    y1 = chy - l/(2*np.sqrt(2))
    x2 = chx + l/(2*np.sqrt(2))
    y2 = chy + l/(2*np.sqrt(2))

    #Shift so that the charge is at (0,0)
    f22 = df_dh(x2 - xpcdn, y2 - ypcdn, zpcd)
    f12 = df_dh(x1 - xpcdn, y2 - ypcdn, zpcd)
    f21 = df_dh(x2 - xpcdn, y1 - ypcdn, zpcd)
    f11 = df_dh(x1 - xpcdn,  y1 - ypcdn, zpcd)

    return (f22 - f21 - f12 + f11)*(1/(2*np.pi))


def current_sum_channel(xpcd,ypcd,zpcd,chID,chx,chy):
    # this returns the current divided by the drift velocity

    #xpcd,ypcd,zpcd --- x,y,z of intial pcd
    #z = 0 is cathode 18.16 is anode for 7th LXe
    #chID is ID for channel < 30 is X Channel
    #chx, chy is x,y pos of channel
    
    #Use rotated channel positions
    if(chID < 30): chy = -42.0 #this is weird but trust me
    else: chx = -42.0 #weird but works 1.5 offset
    I = 0
    for n in np.arange(0,30,1):
        I += I_rot(xpcd, ypcd, zpcd, chx, chy)
        if(chID < 30):
            #Its a xChannel
            chy += 3.0
        else:
            #Its a yChannel
            chx += 3.0
    return I



def make_current_WF(xpcd, ypcd, zpcd, Epcd, chID,
    cathodeToAnodeDistance=cathodeToAnodeDistance,
    #dZ=cathodeToAnodeDistance/100.0, # 100 steps per full drift
    dZ=sampling_period*drift_velocity, # one step per digitizer sample
    wfm_length=800,
    drift_velocity=drift_velocity,
):
    """
    Calculate the instantaneous current at each point in time. 
    """

    directory = os.path.dirname(__file__) # directory containing this script

    xch_list, ych_list =  np.loadtxt(
            "%s/localChannelsMap.txt" % directory, 
            usecols = (1,2),
            unpack=True)

    chx = xch_list[chID]
    chy = ych_list[chID]
    WF = np.zeros(wfm_length)

    #Ralph's anode is at z = 0.0mm
    zpcd = cathodeToAnodeDistance - zpcd
    
    #ionQ = sum_channel(xpcd,ypcd,zpcd,chID,chx,chy)
    
    #Cathode Supression
    #Anode at z = 0 has no supression
    #if cathsupress: ionQ = ionQ*(cathodeToAnodeDistance-zpcd)/cathodeToAnodeDistance

    # electron lifetime:
    z0 = zpcd # initial z position

    #0 is top in Ralph's??
    ki = 0
    for k in np.arange(ki,len(WF),1):    
        zpcd -= dZ
        if(zpcd <= 0.0):
            WF[k:] = 0 # set rest of waveform to 0
            break
        else:
            I = -drift_velocity*current_sum_channel(xpcd,ypcd,zpcd,chID,chx,chy)
            WF[k] = I*Epcd
 
    return WF


def make_current_from_derivative(xpcd, ypcd, zpcd, Epcd, chID, 
    cathodeToAnodeDistance=cathodeToAnodeDistance,
    dZ=sampling_period*drift_velocity, # one step per digitizer sample
    wfm_length=800,
    ):

    """
    Calculate current from numerical derivative of charge wfm. 
    """

    charge_WF = make_WF(xpcd, ypcd, zpcd, Epcd, chID, cathodeToAnodeDistance,
        dZ, wfm_length)
    #print "charge_WF len:", len(charge_WF)

    dt = dZ/drift_velocity # time step

    current_WF = np.zeros(wfm_length-1)
    #print "current_WF len:", len(current_WF)

    for i in xrange(wfm_length-1):
        current_WF[i] = (charge_WF[i+1] - charge_WF[i])/dt

    #print "current_WF len:", len(current_WF)

    return current_WF



if __name__ == "__main__":
 
    print "RalphWF options:"
    print "\t use positive ion:", posion
    print "\t use cathode suppression:", cathsupress 
    print "\t cathodeToAnodeDistance:", cathodeToAnodeDistance
    print "\t drift_velocity [mm/microsecond]: ", drift_velocity
    print "\t electron lifetime: ", e_lifetime
    print "\t consider electrons captured on impurities:", consider_capturedQ
 
    pcdx= 1.5
    pcdy = 0.0
    pcdz = 0.0
    print "PCD coords: x=%.1f, y=%.1f, z=%.1f" % (pcdx, pcdy, pcdz)

    plt.figure(0)
    MakeTile.make_tile()
    plt.scatter([pcdx], [pcdy], c='r', s=100.0)
    plt.xlim(-6, 6)
    plt.ylim(-6, 6)
    plt.savefig("./plots/charge_location_arbitrary.png")
    plt.show()
    raw_input("enter to continue")

    plt.figure(1)
    #Collection signal on channel X16
    plt.title("Collection signal X16")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WF = make_WF(pcdx, pcdy, pcdz, 1, 15)
    sample_times = np.arange(len(WF))*sampling_period
    plt.plot(sample_times, WF)
    plt.ylim([-np.max(WF)*0.1, np.max(WF)*1.1])
    plt.savefig("./plots/collect_X16.png")
 
    plt.figure(2)
    #Collection current signal on channel X16
    plt.title("Collection current signal X16")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("I/Itotal")
    WF = make_current_WF(pcdx, pcdy, pcdz, 1, 15)
    sample_times = np.arange(len(WF))*sampling_period
    plt.plot(sample_times, WF)
    plt.ylim([-np.max(WF)*0.1, np.max(WF)*1.1])
    plt.savefig("./plots/collect_current_X16.png")
    
    """
    plt.figure(2)
    #Induction signal X15
    plt.title("Induciton siganl X15")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WF = make_WF(pcdx, pcdy, pcdz, 1, 14)
    plt.plot(sample_times, WF)
    plt.ylim([-np.max(WF)*0.1,np.max(WF)*1.1])
    plt.savefig("./plots/induct_X15.png")
    
    plt.figure(3)
    #Induction signal Y16
    plt.title("Induction siganl Y16")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WF = make_WF(pcdx, pcdy, pcdz, 1, 45)
    plt.plot(sample_times, WF)
    plt.ylim([-np.max(WF)*0.1,np.max(WF)*1.1])
    plt.savefig("./plots/induct_Y16.png")

    pcdx= 1.5
    pcdy = 0.0
    pcdz = 15.0
    
    plt.figure(4)
    #Induction signal Y16
    plt.title("Induction siganl Y16 (zstart = 2mm from anode)")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WF = make_WF(pcdx, pcdy, pcdz, 1, 45)
    plt.plot(sample_times, WF)
    plt.ylim([np.min(WF)*1.1,np.max(WF)*1.1])
    plt.savefig("./plots/induct_Y16_neg.png")
    """

    plt.show()
    raw_input("enter to continue")

   

