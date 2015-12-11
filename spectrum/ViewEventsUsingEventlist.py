#!/usr/bin/env python

"""
This script should be run after running "spectrum.py", which will generate a root file with eventlist

To run:
python /path/to/this/script /path/to/eventlist/file /path/to/original/tree
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
import struck_analysis_parameters

def process_file(eventlist_filename, filename):
    do_debug = False 

    print "processing file: ", filename

    #basename = os.path.basename(filename)
    #basename = os.path.splitext(basename)[0]

    eventlist_file = TFile(eventlist_filename, "READ")
    elist = eventlist_file.Get("elist")

    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    calibration_values = struck_analysis_parameters.calibration_values
    channels = struck_analysis_parameters.channels
    n_channels = struck_analysis_parameters.n_channels
    n_chargechannels = struck_analysis_parameters.n_chargechannels
    colors = [
        TColor.kBlue, 
        TColor.kGreen+2, 
        TColor.kViolet+1,
        TColor.kRed, 
        TColor.kOrange+1,
        TColor.kPink-6
    ]

    canvas = TCanvas("canvas","", 1700, 900)
    
    i_entry = 0
    while i_entry < elist.GetN():
        canvas.Clear()
        pad = canvas.cd(1)
        pad.SetGrid(1,1)
        
        tree.GetEntry(elist.GetEntry(i_entry))
        energy = 0
        for i in xrange(n_chargechannels):
            energy = energy + tree.energy1_pz[i]
        pad.DrawFrame(0., -200., 32., 3000., "Event %i, total energy=%f" % (i_entry, energy))

        original_file = TFile(tree.filename.GetString().Data(), "READ")
        original_tree = original_file.Get("tree")
        original_tree.GetEntry(tree.event)

        if do_debug:
            channels = [3, 3, 3, 3]
            pad.DrawFrame(0., 0., 32., 1000., "Event %i, total energy=%f" % (i_entry, energy))

        print "---- Event %i -----" % (i_entry)
        for (i, channel) in enumerate(channels):
            print "channel%i: drift time = %f us, energy = %f keV" % (channel, 
                                                                      tree.rise_time_stop95[i] - tree.trigger_time, 
                                                                      tree.energy1_pz[i]) 
            try:
                color = colors[channel]
            except IndexError:
                color = TColor.kBlack
            original_tree.SetLineColor(color)
            
            offset = (n_channels - 2 - i) * 250.
            if channel == 8:
                offset = 2000.

            multiplier = calibration_values[original_tree.channel[i]]

            draw_command = "((wfm%i - wfm%i[0])*%f+%i):(Iteration$*40/1e3)" % (channel, channel, multiplier, offset)
            original_tree.Draw(draw_command, "Entry$==%i" % tree.event, "l same")

        canvas.Update()

        val = raw_input("Press Enter to continue, p to print, q to quit, or event # to show event...")
        if val.isdigit():
            i_entry1 = int(val)
            if i_entry1 < 0 or i_entry1 >= tree.GetEntries():
                print "wrong input!"
            else:
                i_entry = i_entry1
                continue
        elif val == 'q':
            break
        elif val == 'p':
            canvas.Print("Event_%i.png" % i_entry)

        i_entry += 1
        
        


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print "arguments: [eventlist file] [sis root files]"
        sys.exit(1)

    process_file(sys.argv[1], sys.argv[2])



