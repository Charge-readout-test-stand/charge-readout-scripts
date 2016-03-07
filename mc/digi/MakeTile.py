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


if __name__ == "__main__":

    make_tile()
    plt.show()
    raw_input()

