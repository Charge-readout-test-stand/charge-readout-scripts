import ROOT, sys
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from optparse import OptionParser
import numpy as np
import COMSOLWF

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
parser = OptionParser()
options,args = parser.parse_args()

WFFile = "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207/Digi/digi1_dcoef100.root"

#c1 = ROOT.TCanvas("c1")
#c1.SetLogy()


if len(sys.argv) < 2:
    print "Need File Name"
    sys.exit(1)

WFFile = sys.argv[1]

def square(centerx, centery, diag):
    x = [centerx+diag/2.0, centerx, centerx-diag/2.0, centerx, centerx+diag/2.0]
    y = [centery, centery+diag/2.0, centery, centery-diag/2.0, centery]
    return x,y
    
def make_tile():
    num_channelsx = 30
    diag = 3.0
    #Make the outline of the tile
    xbig = [-45.0, 45.0, 45.0,  -45.0, -45.0 ]
    ybig = [-45.0, -45.0, 45.0, 45.0,  -45.0 ]
    plt.plot(xbig,ybig,c='r')
    
    #Loop over and create the tile 
    #(0,0) is an intersection
    yi = -45.0
    for i in np.arange(num_channelsx):
        xi = -43.5 
        for j in np.arange(num_channelsx):
            xa,ya = square(xi,yi,diag)
            #xb,yb = square(yi,xi,diag)
            xi+=3.0
            plt.plot(xa,ya,c='r')
            #plt.plot(xb,yb,c='r')
        yi+=3.0
        #plt.show()
        #user_in = raw_input()
        #if user_in == 'q': sys.exit()


fData =  ROOT.TFile(WFFile)
tData =  fData.Get("evtTree")

nEvents = tData.GetEntries()

print "There are nEvents = ", nEvents

num_channels = 60
len_WF = 800

t = np.arange(len_WF)*(40/1000.0)

plt.ion()

for ev in np.arange(nEvents):
    tData.GetEntry(ev)
    if tData.NumPCDs == 0: continue
    total_q = 0
    
    print tData.GenX, tData.GenY, tData.GenZ, tData.Energy
    print "Energy in keV", tData.Energy*1000
    print "There are npcds = ", tData.NumPCDs

    x = []
    y = []
    z = []
    for pcdn in np.arange(tData.NumPCDs):
        print "x,y,z,Q,Q"
        print tData.PCDx[int(pcdn)], tData.PCDy[int(pcdn)], tData.PCDz[int(pcdn)], tData.PCDe[int(pcdn)], tData.PCDq[int(pcdn)]
        x.append(tData.PCDx[int(pcdn)])
        y.append(tData.PCDy[int(pcdn)])
        z.append(tData.PCDz[int(pcdn)])
        total_q += tData.PCDq[int(pcdn)]


    make_tile()
    plt.scatter(x,y)
    plt.xlim([min(x) - 3.0, max(x) + 3.0])
    plt.ylim([min(y) - 3.0, max(y) + 3.0])
    plt.show()
    raw_input()
    plt.clf()

    plt.scatter(x,z)
    plt.show()
    raw_input()
    plt.clf()

    print len(x), len(y)
    print "Total Q = ", total_q

    #if tData.NumChannels != 60:
    #    print "---------------What-----------------------"
    #    sys.exit(1)

    WF = np.zeros((num_channels,len_WF))
    WFmine = np.zeros((num_channels,len_WF))
    for nch in np.arange(num_channels):
        if tData.NumPCDs == 0: continue
        #if nch != 25: continue
        print type(tData.ChannelWaveform[int(nch)])
        for i in np.arange(len_WF):
            #print tData.ChannelWaveform[int(nch)][int(i)]
            WF[nch][i] = tData.ChannelWaveform[int(nch)][int(i)]
        if WF[nch][-1] > 0: 
            print "Hit Ch = ", nch, " value = ", WF[nch][-1]
        
        plt.plot(t, WF[nch], label='Sim Ch='+str(nch))

    #plt.xlim([2,15])
    plt.show()
    user_in = raw_input()
    if(user_in == 'q'): break
    plt.clf()
    #break

