import ROOT, sys, os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from optparse import OptionParser
import numpy as np
#import COMSOLWF


ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
parser = OptionParser()
options,args = parser.parse_args()

#WFFile = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff50/mc/run5955.root"
WFFile = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff50/mc/run0.root"

#c1 = ROOT.TCanvas("c1")
#c1.SetLogy()


if len(sys.argv) > 1:
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
    for i in np.arange(num_channelsx+1):
        xi = -43.5
        for j in np.arange(num_channelsx):
            rect = patches.RegularPolygon((xi,yi), 4, radius=diag/2, 
                                           orientation=0.0, alpha=0.5)
            plt.gca().add_patch(rect)
            xi+=3.0
        yi+=3.0



fData =  ROOT.TFile(WFFile)
try:
    tData =  fData.Get("nEXOevents")
    nEvents = tData.GetEntries()
    print "There are nEvents = ", nEvents
except AttributeError:
    print "couldn't find TTree"
    sys.exit()

basename = os.path.basename(WFFile)
basename = os.path.splitext(basename)[0]

num_channels = 60
len_WF = 800

t = np.arange(len_WF)*(40/1000.0)

plt.ion()


x = []
y = []
z = []

for ev in np.arange(nEvents):
    print "--> event %i" % ev
    tData.GetEntry(ev)
    
    print "GenX,Y,Z", tData.GenX, tData.GenY, tData.GenZ #, tData.Energy
    #print "Energy in keV", tData.Energy*1000

    x.append(tData.GenX)
    y.append(tData.GenY)
    z.append(tData.GenZ)

    if False and ev > 200: 
        print "stopping at %i for debugging"
        break

make_tile()
plt.scatter(x,y)
plt.xlim([min(x) - 3.0, max(x) + 3.0])
plt.ylim([min(y) - 3.0, max(y) + 3.0])
plt.show()
#plt.clf()
plt.savefig("GenXY"+basename+".pdf")

# x vs z scatter plot
#plt.scatter(x,z)
#plt.show()
#raw_input()
#plt.clf()

print "len x, y:", len(x), len(y)

#plt.xlim([2,15])
#plt.show()
print "white wires are horizontal (y), blue wires are vertical (x)"
print "x=4.5 is the centerline of one wire; y=4.5 is centerline of another wire"
user_in = raw_input("enter to continue ")
#break

