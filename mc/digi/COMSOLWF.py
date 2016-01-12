import numpy as np
import matplotlib.pyplot as plt
import ROOT
import sys


def make_WF(xpcd, ypcd, zpcd, Epcd, chID):


    xch_list, ych_list =  np.loadtxt("/nfs/slac/g/exo/mjewell/nEXO/nEXO_Analysis/utilities/scripts/localChannelsMap.txt", usecols = (1,2) ,unpack=True)
    dZ = 0.04 * 0.171 * 10 

    chx = xch_list[chID]
    chy = ych_list[chID]

    WF = np.zeros(800)
    #c1 = ROOT.TCanvas("c1")
    inroot = ROOT.TFile("/nfs/slac/g/exo/mjewell/nEXO/nEXO_Analysis/utilities/data/TestStandWP.root")
    WP_ROOT= inroot.Get("WP_ROOT")

    RelPos = None
    Height = None
    
    #print "chx = ", chx, "chy=", chy

    #I think there is a weird offset in the y position of 1.5 in the COMSOL file
    #If xpcd = 1.5 and ypcd = 0.0 for XCh = 15, pos = (1.5,0,0)
    #This should give xpcd = 0.0 and ypcd = 1.5
    if(chID < 30):
        #print "Look up", xpcd - chx, ypcd - chy
        RelPos = WP_ROOT.GetXaxis().FindBin(xpcd - chx)
        Height = WP_ROOT.GetYaxis().FindBin(ypcd + 1.5)
    elif(chID > 30 and chID < 60):
        RelPos = WP_ROOT.GetXaxis().FindBin(ypcd - chy)
        Height = WP_ROOT.GetYaxis().FindBin(xpcd + 1.5)
    else:
        print "Channel ID bad"
        sys.exit(1)

    zbin = WP_ROOT.GetZaxis().FindBin(zpcd)
    
    Q = 0
    ki = 200

    for k in np.arange(ki,800,1):
        zpcd += dZ
        if(zpcd > 17.0):
            zbin_next = WP_ROOT.GetNbinsZ()
            dW = WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin_next)) -  WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin))
            #print "Wi+1", WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin_next)),
            #print "Wi", WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin))
            Q += Epcd*dW
            WF[k:] = Q
            break
        else:
            zbin_next = WP_ROOT.GetZaxis().FindBin(zpcd)
            #print "Wi+1", WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin_next)),
            #print "Wi", WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin))
            dW = WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin_next)) -  WP_ROOT.GetBinContent(WP_ROOT.GetBin(RelPos, Height, zbin)) 
            Q += Epcd*dW
            WF[k] = Q
            zbin = zbin_next

    return WF


if __name__ == "__main__":
    WF = make_WF(3.46944695195e-18, 0.05, 0.247487373415, 1, 45)
    #print WF
    plt.plot(WF)
    plt.show()












