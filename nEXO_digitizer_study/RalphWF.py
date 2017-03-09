import numpy as np
import matplotlib.pyplot as plt
import ROOT
#import MakeTile
import math

posion  = True #Use Positive Ion
cathsupress = True #Use Cathode Supression
cathodeToAnodeDistance = 1183 # from TPC assembly drawing(mm)
#cathodeToAnodeDistance = 1000.0 # mm
#cathodeToAnodeDistance = 33.23 # mm
drift_velocity = 1.7 # mm/microsecond
e_lifetime=None # e- lifetime, microseconds
consider_capturedQ=False # electrons captured on impurities
sampling_period = 0.5 #microseconds
wfm_length = 2000
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
    if(chID < 33): chy = -46.5 #this is weird but trust me
    else: chx = -46.5 #weird but works 1.5 offset
    Q = 0
    for n in np.arange(0,33,1):
        Q += Q_rot(xpcd, ypcd, zpcd, chx, chy)
        if(chID < 33):
            #Its a xChannel
            chy += 3.0
        else:
            #Its a yChannel
            chx += 3.0
    return Q

def make_WF(xpcd, ypcd, zpcd, Epcd, chID, tileID):
    dZ = sampling_period * drift_velocity
    dZ = cathodeToAnodeDistance/100.0
  
    TileID_list, xTile_list, yTile_list = np.loadtxt("/afs/slac.stanford.edu/u/xo/manisha2/nEXO_analysis_charge_digitizer_study/utilities/scripts/tilesMap.txt", usecols=(0,1,2), unpack=True)
    tilex = xTile_list[tileID]
    tiley = yTile_list[tileID]

    ChannelID_list, xch_list, ych_list =  np.loadtxt("/afs/slac.stanford.edu/u/xo/manisha2/nEXO_analysis_charge_digitizer_study/utilities/scripts/localChannelsMap.txt", usecols = (0,1,2) ,unpack=True)
     
    chx = xch_list[chID]
    chy = ych_list[chID]
    WF = np.zeros(wfm_length) #number of samples in a waveform
    print "Channel X: %i | Channel Y: %i | Tile X: %i | Tile Y: %i" % (chx, chy, tilex, tiley)
    #Ralphs anode is at z = 0.0mm
    zpcd = cathodeToAnodeDistance - zpcd
    xpcd = xpcd - tilex
    ypcd = ypcd - tiley
    print "Xpcd: %i | Ypcd: %i" % (xpcd, ypcd)
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


if __name__ == "__main__":
    
    sample_times = np.arange(wfm_length)*40*1e-3
 
    pcdx= 34.0
    pcdy = 47.0
    pcdz = 0
    
    """
    plt.figure(0)
    MakeTile.make_tile()
    plt.scatter([pcdx], [pcdy], c='r', s=100.0)
    plt.xlim(-6, 6)
    plt.ylim(-6, 6)
    #plt.savefig("./plots/charge_location_arbitrary.png")
    plt.show()
    raw_input()
    """

    plt.figure(1)
    #Collection signal on channel X16
    plt.title("Collection signal Tile 93")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WF = make_WF(pcdx, pcdy, pcdz, 1, 48, 93)
    plt.plot(sample_times, WF)
    plt.ylim([-np.max(WF)*0.1, np.max(WF)*1.1])
    plt.show()
    #plt.savefig("./plots/collect_X16.png")
    
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
    raw_input("any key to continue")

   

