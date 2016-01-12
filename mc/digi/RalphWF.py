import numpy as np
import matplotlib.pyplot as plt
import ROOT


posion  = True #Use Positive Ion
cathsupress = True #Use Cathode Supression

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
    #z = 0 is cathode 17 is anode
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
    dZ = 0.04 * 0.171 * 10
    
    chx = xch_list[chID]
    chy = ych_list[chID]
    WF = np.zeros(800)

    #Ralphs anode is at z = 0.0mm
    zpcd = 17.0 - zpcd
    
    ionQ = sum_channel(xpcd,ypcd,zpcd,chID,chx,chy)
    
    #Cathode Supression
    #Anode at z = 0 has no supression
    ionQ = ionQ
    if cathsupress: ionQ = ionQ*(17-zpcd)/17.0

    #17 is top in Daves
    #0 is top in Ralphs??
    ki = 200
    for k in np.arange(ki,800,1):    
        zpcd -= dZ
        if(zpcd <= 0.0):
            Q = sum_channel(xpcd,ypcd,0.00001,chID,chx,chy) 
            if cathsupress: Q = Q*(17-zpcd)/17.0
            if posion: Q -= ionQ
            WF[k:] = Q*Epcd
            break
        else:
            Q = sum_channel(xpcd,ypcd,zpcd,chID,chx,chy) 
            if cathsupress: Q = Q*(17-zpcd)/17.0
            if posion: Q -= ionQ
            WF[k] = Q*Epcd
 
    return WF


if __name__ == "__main__":
    
    plt.figure(1)
    #Collection signal on channel X16
    WF = make_WF(1.5, 0.0, 0.0, 1, 15)
    plt.plot(WF)
    plt.ylim([-0.1,1.1])


    plt.figure(2)
    #Induction signal X15
    WF = make_WF(1.5, 0.0, 0.0, 1, 14)
    plt.plot(WF)
    plt.ylim([-0.1,1.1])
    
    
    plt.figure(3)
    #Induction signal Y16
    WF = make_WF(1.5, 0.0, 0.0, 1, 45)
    plt.plot(WF)
    plt.ylim([-0.1,1.1])
    plt.show()

   

