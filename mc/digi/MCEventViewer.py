import ROOT, sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import numpy as np
from optparse import OptionParser
import numpy as np

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
parser = OptionParser()
options,args = parser.parse_args()

num_channels = 60
len_WF = 800
t = np.arange(len_WF)*(40/1000.0)

plt.ion()

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
    for i in np.arange(num_channelsx+1):
        xi = -43.5
        for j in np.arange(num_channelsx):
            rect = patches.RegularPolygon((xi,yi), 4, radius=diag/2, 
                                           orientation=0.0, alpha=0.5)
            plt.gca().add_patch(rect)
            xi+=3.0
        yi+=3.0


def PCDViewer(tData, eventN):
    total_q = 0
    print
    print "Total Energy in keV", tData.Energy*1000
    print "There are npcds = ", tData.NumPCDs
    
    x = []
    y = []
    z = []
    for pcdn in np.arange(tData.NumPCDs):
        print "PCD pos (x,y,z)", tData.PCDx[int(pcdn)], tData.PCDy[int(pcdn)], tData.PCDz[int(pcdn)], 
        print "PCDQ = ", tData.PCDq[int(pcdn)]
        x.append(tData.PCDx[int(pcdn)])
        y.append(tData.PCDy[int(pcdn)])
        z.append(tData.PCDz[int(pcdn)])
        total_q += tData.PCDq[int(pcdn)]

    make_tile()
    plt.scatter(x,y, c= 'r', s=100.0)
    plt.xlim([min(x) - 3.0, max(x) + 3.0])
    plt.ylim([min(y) - 3.0, max(y) + 3.0])
    plt.title("X/Y Event Plane with Tile Grid")
    plt.xlabel("xpos[mm]")
    plt.ylabel("ypos[mm]")
    plt.show()
    save = raw_input("Save figure? (y or n)")
    if save == 'y':
        plt.savefig("./plots/pcds_event"+str(eventN)+".png")
    plt.clf()


def SignalViewer(tData, eventN):
    WF = np.zeros((num_channels,len_WF))
    for nch in np.arange(num_channels):
        if tData.NumPCDs == 0: continue
        for i in np.arange(len_WF):
            WF[nch][i] = tData.ChannelWaveform[int(nch)][int(i)]
        if WF[nch][-1] > 0:
            print "Hit Ch = ", nch, " Qvalue = ", WF[nch][-1]
        plt.plot(t, WF[nch], label='Sim Ch='+str(nch))
    plt.title("Channel Signals")
    plt.xlabel("time[$\mu$s]")
    plt.ylabel("Q[#e-]")
    save = raw_input("Save figure? (y or n)")
    if save == 'y':
        plt.savefig("./plots/signal_event"+str(eventN)+".png")
    plt.clf()

def EventViewer(tData):
    fData =  ROOT.TFile(WFFile)
    tData =  fData.Get("evtTree")
    nEvents = tData.GetEntries()
    print "Opened File"
    print "There are nEvents = ", nEvents

    for ev in np.arange(nEvents):
        tData.GetEntry(ev)
        if tData.NumPCDs == 0: continue
        PCDViewer(tData, ev)
        SignalViewer(tData, ev)

if __name__ == "__main__":
    
    #Need digied file name
    if len(sys.argv) < 2:
        print "Need File Name"
        sys.exit(1)
    
    WFFile = sys.argv[1]

    EventViewer(WFFile)



