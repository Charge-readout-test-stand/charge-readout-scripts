"""
Draw multiplicity plot
"""


import os
import sys
import TileEventViewer

import ROOT
from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TLegend
from ROOT import gStyle


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

import struck_analysis_cuts
import struck_analysis_parameters

def process_files(filenames):

    hists = []
    ch_hists = []

    threshold = 10


    for (i, filename) in enumerate(filenames):
        
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        print "processing file: ", filename

        hist = TH1D("hist%i" % len(hists), basename,64, -0.25, 31.75)
        hists.append(hist)

        # open the root file and grab the tree
        root_file = TFile(filename)
        tree = root_file.Get("tree")
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
        hist = hists[i]
        hist.GetDirectory().cd()

        is_MC = True
        try:
            tree.GetEntry(0)
            tree.MCchargeEnergy
        except:
            is_MC = False
        print "is_MC:", is_MC

        multiplier = 1.0
        if is_MC:
            multiplier = 1.15

        print "Drawing the Hist"
        # draw channels hit:    
        ch_hist = TH1D("ch_hist%i" % len(hists), basename,64, -0.25, 31.75)
        selection = "signal_map==1"
        n_drawn = tree.Draw("channel >> %s" % ch_hist.GetName(), selection, "goff")
        ch_hist.Scale(1.0/n_entries)
        print "Done draw start the python part"

        hits_per_ch = []
        for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):

            i_bin = ch_hist.FindBin(channel)

            # set contents to 0 for unused channels
            if val == 0:
                if channel == struck_analysis_parameters.pmt_channel: continue
                content = ch_hist.GetBinContent(i_bin)
                ch_hist.SetBinContent(i_bin, 0.0)
                print "set ch %i %s bin %i from %i to 0" % (channel, struck_analysis_parameters.channel_map[channel], i_bin, content)

            print struck_analysis_parameters.channel_map[channel], ch_hist.GetBinContent(i_bin)
            hits_per_ch.append(ch_hist.GetBinContent(i_bin))
        
        TEV = TileEventViewer.TileEventViewer(100, min(hits_per_ch), max(hits_per_ch))
        print len(hits_per_ch)
        TEV.make_tile_event(hits_per_ch)
        raw_input()
        print "Tile Draw"



if __name__ == "__main__":


    filenames = [
        "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v4.root"
            #"/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v4.root ", # LLNL
    ]

    process_files(filenames)



