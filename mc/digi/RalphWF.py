import numpy as np
import matplotlib.pyplot as plt
import ROOT
import MakeTile
import math

posion  = True #Use Positive Ion
cathsupress = False #Use Cathode Supression
cathodeToAnodeDistance = 18.16 # mm
drift_velocity = 2.0 # mm/microsecond
e_lifetime=None # e- lifetime, microseconds
consider_capturedQ=False # electrons captured on impurities

def f(xi, yi, h):
    inside = (xi*yi)/(h*np.sqrt(xi*xi + yi*yi + h*h))
    return np.arctan(inside)


def Q_rot(xpcd, ypcd, zpcd, chx, chy):
    #Get the induced Charge at (x,y,z) using analytic solution from Ralph
    #Just one pad located at chx,chy

    l = 3.0 #3mm on the diagnol


    #Rotate into the Rectangles Frame for this calculation
    #45degrees
    xpcdn = (np.sqrt(2)/2)*(xpcd - ypcd)
    ypcdn = (np.sqrt(2)/2)*(xpcd + ypcd)
    
    chxn = (np.sqrt(2)/2)*(chx - chy)
    chyn = (np.sqrt(2)/2)*(chx + chy)

    chx = chxn
    chy = chyn

    #Assume the charge is centered at (0,0)
    #And the Diagnol is 3mm
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

def make_WF(xpcd, ypcd, zpcd, Epcd, chID):

    xch_list, ych_list =  np.loadtxt("/nfs/slac/g/exo/mjewell/nEXO/nEXO_Analysis/utilities/scripts/localChannelsMap.txt", usecols = (1,2) ,unpack=True)
    dZ = 0.04 * 0.2 * 10
    
    chx = xch_list[chID]
    chy = ych_list[chID]
    WF = np.zeros(800)

    #Ralphs anode is at z = 0.0mm
    zpcd = cathodeToAnodeDistance - zpcd
    
    ionQ = sum_channel(xpcd,ypcd,zpcd,chID,chx,chy)
    
    #Cathode Supression
    #Anode at z = 0 has no supression
    ionQ = ionQ
    if cathsupress: ionQ = ionQ*(cathodeToAnodeDistance-zpcd)/cathodeToAnodeDistance

    # electron lifetime:
    z0 = zpcd # initial z position
    capturedQ = 0.0 # for electrons captured on impurities

    #cathodeToAnodeDistance is top in Daves
    #0 is top in Ralphs??
    ki = 200
    for k in np.arange(ki,800,1):    
        zpcd -= dZ
        if zpcd < 0: zpcd = 0.0
        if e_lifetime:
            drift_time = (z0-zpcd)/drift_velocity # so far
            exp_factor = math.exp(-drift_time/e_lifetime)
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
            if e_lifetime: Q = Q*exp_factor
            if cathsupress: Q = Q*(cathodeToAnodeDistance-zpcd)/cathodeToAnodeDistance
            if e_lifetime and consider_capturedQ: 
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


if __name__ == "__main__":
    
    sample_times = np.arange(800)*40*1e-3
 
    pcdx= 1.5
    pcdy = 0.0
    pcdz = 0.0

    plt.figure(0)
    MakeTile.make_tile()
    plt.scatter([pcdx], [pcdy], c='r', s=100.0)
    plt.xlim(-6, 6)
    plt.ylim(-6, 6)
    plt.savefig("./plots/charge_location_arbitrary.png")
    plt.show()
    raw_input()

    plt.figure(1)
    #Collection signal on channel X16
    plt.title("Collection siganl X16")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WF = make_WF(pcdx, pcdy, pcdz, 1, 15)
    plt.plot(sample_times, WF)
    plt.ylim([-np.max(WF)*0.1, np.max(WF)*1.1])
    plt.savefig("./plots/collect_X16.png")

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

    plt.show()
    raw_input()

   

