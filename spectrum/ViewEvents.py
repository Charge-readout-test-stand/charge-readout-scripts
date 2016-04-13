#!/usr/bin/env python

"""
This script should be run after "spectrum.py"
It reads from the event list file "ChargeSpectrum_eventlist.txt" (must be in the same directory)

To run, the module "struck_analysis_parameters.py" must be in the directory
"""

import os
import sys
import glob

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TH2D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TMath
from ROOT import TTree


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import CLHEP
from struck import struck_analysis_parameters

def process_file(filename):

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    calibration_values = struck_analysis_parameters.calibration_values
    channels = struck_analysis_parameters.channels
    colors = [
        TColor.kBlue, 
        TColor.kGreen+2, 
        TColor.kViolet+1,
        TColor.kRed, 
        TColor.kOrange+1,
    ]

    canvas = TCanvas("canvas","", 1700, 900)

    tree.GetEntry(0)
    trigger_time_0 = tree.trigger_time

    import json
    with open("ChargeSpectrum_eventlist.txt", "r") as fin:
        eventlists = json.load(fin)

    eventlist1 = eventlists['list1']
    for i_entry in eventlist1:
        canvas.Clear()
        pad = canvas.cd(1)
        pad.SetGrid(1,1)
        
        tree.GetEntry(i_entry)
        energy = 0
        for i in xrange(5):
            energy = energy + tree.energy1_pz[i]
        pad.DrawFrame(0., -200., 32., 3000., "Event %i, total energy=%f" % (i_entry, energy))

        original_file = TFile("/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_10_20_5th_LXe/tier3/%s" % tree.filename.GetString(), "READ")
        original_tree = original_file.Get("tree")
        original_tree.GetEntry(tree.event)

        for (i, channel) in enumerate(channels):
            print "channel%i: drift time = %f us, energy = %f keV" % (i, 
                                                                      tree.rise_time_stop95[i] - tree.trigger_time, 
                                                                      tree.energy1_pz[i]) 
            try:
                color = colors[channel]
            except IndexError:
                color = TColor.kBlack
            original_tree.SetLineColor(color)
            
            offset = 1000 - i * 250
            if channel == 8:
                offset = 2000

            multiplier = calibration_values[original_tree.channel[i]]

            draw_command = "((wfm%i - wfm%i[0])*%s+%i):Iteration$*40/1e3" % (channel, channel, multiplier, offset)
            original_tree.Draw(draw_command, "Entry$==%i" % i_entry, "l same")

        canvas.Update()
        val = raw_input("Press Enter to continue, p to print, q to quit...")
        if val == 'q':
            break
        elif val == 'p':
            canvas.Print("Event_%i.png" % i_entry)
        
        


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



