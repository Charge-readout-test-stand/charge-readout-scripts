import ROOT, sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import numpy as np
from optparse import OptionParser
import numpy as np
import matplotlib.cm as cmx
import matplotlib.colors as colors
import matplotlib.colorbar as colorbar
from mpl_toolkits.axes_grid1 import make_axes_locatable


import struck_analysis_parameters

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
parser = OptionParser()
options,args = parser.parse_args()

num_channels = 60
len_WF = 800
t = np.arange(len_WF)*(40/1000.0)

plt.ion()

#Same for y
num_channelsx = 30
num_channelsy = 30
diag = 3.0
ncols = 400
col_min = -100
col_max = 900

def get_color_map( n ):
    jet = plt.get_cmap('jet')
    cNorm  = colors.Normalize(vmin=0, vmax=n-1)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)
    outmap = []
    for i in range(n):
        outmap.append( scalarMap.to_rgba(i) )
    return outmap

custom_map = get_color_map(ncols)

def energy_to_color(E):
    col_range = np.linspace(col_min,col_max,ncols)
    cindex = np.argmin(np.abs(col_range-E))
    return custom_map[cindex]

def DrawChannels(isX, energy):
    #X1 (bottom left corner) x=-43.5, y=-45.0
    xi = -43.5
    for i in np.arange(num_channelsx):
        yi = -45.0
        for j in np.arange(num_channelsx+1):
            if isX:
                tileCh = i
                pCh = struck_analysis_parameters.tileCh_to_PreCh[tileCh] 
                chName = struck_analysis_parameters.channel_map[pCh]
                tc = energy_to_color(energy[pCh])
                rect = patches.RegularPolygon((xi,yi), 4, radius=diag/2,
                                              orientation=0.0,color=tc,alpha=1.0,
                                              ls='solid', ec='k')
            else:
                tileCh = i+30
                pCh = struck_analysis_parameters.tileCh_to_PreCh[tileCh]
                chName = struck_analysis_parameters.channel_map[pCh]
                tc = energy_to_color(energy[pCh])
                rect = patches.RegularPolygon((yi,xi), 4, radius=diag/2,
                                              orientation=0.0,color=tc, alpha=1.0,
                                              ls='solid', ec='k')
            plt.gca().add_patch(rect)
            plt.show()
            yi+=diag
        xi+=diag


def PlotOutline():
    xbig = [-45.0, 45.0, 45.0,  -45.0, -45.0 ]
    ybig = [-45.0, -45.0, 45.0, 45.0,  -45.0 ]
    plt.plot(xbig,ybig,c='g')

    #Make ColorBar
    jet = plt.get_cmap('jet')
    cNorm  = colors.Normalize(vmin=col_min, vmax=col_max)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap='jet')
    scalarMap.set_array(ncols)
    cb = plt.colorbar(scalarMap,fraction=0.035)
    cb.set_label('Energy[keV]')

def make_tile_event(energy):
    PlotOutline()
    print "Draw X"
    DrawChannels(True,energy)
    print "Draw Y"
    DrawChannels(False,energy)

    plt.xlim(-47, 47)
    plt.ylim(-47, 47)
    print "Drawn"
    plt.show()

if __name__ == "__main__":
    fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v4.root"
    rfile = ROOT.TFile(fname)
    tree = rfile.Get("tree")
    nEvents = tree.GetEntries()
    
    for index in xrange(nEvents):
        tree.GetEntry(index)
        energy_hold = tree.energy1_pz
        energy = [energy_hold[i] for i in xrange(31)]
        #for ich, E in enumerate(energy):
        #    print ich, E
        #print "Max: ", max(energy[0:31])
        if tree.SignalEnergy < 200: 
            print "Skip"
            continue
        print "Sig Energy ", tree.SignalEnergy
        make_tile_event(energy)
        plt.show()
        raw_input()
        plt.clf()

