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
gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TMath
from ROOT import TTree
from ROOT import TLine


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
    energy_threshold=1000

    print "processing file: ", filename

    #basename = os.path.basename(filename)
    #basename = os.path.splitext(basename)[0]

    eventlist_file = TFile(eventlist_filename, "READ")
    elist = eventlist_file.Get("elist")
    print "%i entries in elist" % elist.GetN()


    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    calibration_values = struck_analysis_parameters.calibration_values
    channels = struck_analysis_parameters.channels
    n_channels = struck_analysis_parameters.n_channels
    n_chargechannels = struck_analysis_parameters.n_chargechannels

    colors = struck_analysis_parameters.get_colors()

    canvas = TCanvas("canvas","")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid(1,1)
    
    i_entry = 0
    canvas.Print("keptEvents.pdf[")
    frame_hist = TH1D("frame_hist","",100,0,32)
    frame_hist.SetMaximum(5000)
    frame_hist.SetMinimum(-200)
    frame_hist.SetXTitle("time [#mus]")
    frame_hist.SetYTitle("Energy (with arbitrary offset) [keV]")
    n_drawn_events = 0
    while i_entry < elist.GetN():
        if n_drawn_events >= 100: break # debugging
        frame_hist.Draw()
        
        tree.GetEntry(elist.GetEntry(i_entry))
        if tree.chargeEnergy < energy_threshold:
            #print "skipping entry %i" % i_entry
            i_entry += 1
            continue


        original_file = TFile(tree.filename.GetString().Data(), "READ")
        legend = TLegend(0.1, 0.86, 0.9, 0.99)
        legend.SetFillColor(0)
        legend.SetNColumns(4)

        if do_debug:
            channels = [3, 3, 3, 3]

        print "---- kept event %i , event %i, plot %i -----" % (i_entry, elist.GetEntry(i_entry), n_drawn_events)
        lines = []
        for (i, channel) in enumerate(channels):
            if not gROOT.IsBatch():
                print "channel%i: drift time = %.2f us, energy = %.2f keV" % (channel, 
                                                                      tree.rise_time_stop95[i] - tree.trigger_time, 
                                                                      tree.energy1_pz[i]) 

            tree_name = "tree%i" % channel
            original_tree = original_file.Get(tree_name)
            #print "%i entries in original tree %s" % (original_tree.GetEntries(), tree_name)
            original_tree.GetEntry(tree.event)


            try:
                color = colors[i]
            except IndexError:
                color = TColor.kBlack
            original_tree.SetLineColor(color)
            original_tree.SetLineWidth(2)
            chanE = tree.energy1_pz[i]
            if channel == struck_analysis_parameters.pmt_channel:
                chanE = tree.lightEnergy
            channel_name = struck_analysis_parameters.channel_map[channel]
            drift_time = tree.rise_time_stop95[i] - tree.trigger_time
            legend.AddEntry(
                original_tree, 
                channel_name + " E=%.1f, DT=%.2f" % (chanE, drift_time),
                "l"
            )
            offset = (n_channels - 2 - i) * 250.
            offset = 500*i
            #if channel == 8:
            #    offset = 2000.

            # draw drift time for channels above threshold
            if chanE > 200 and channel != struck_analysis_parameters.pmt_channel:
                dt_line = TLine(drift_time+tree.trigger_time, offset, drift_time+tree.trigger_time, offset+chanE)
                dt_line.Draw()
                dt_line.SetLineWidth(2)
                lines.append(dt_line)
            
            multiplier = tree.calibration[i]

            draw_command = "((wfm - wfm[0])*%f+%i):(Iteration$*40/1e3)" % (multiplier, offset)
            original_tree.Draw(draw_command, "Entry$==%i" % tree.event, "l same")

        trigger_line = TLine(tree.trigger_time, -200, tree.trigger_time, 6000)
        trigger_line.SetLineStyle(2)
        trigger_line.Draw()

        max_drift_line = TLine(
            tree.trigger_time + struck_analysis_parameters.max_drift_time, 
            -200, 
            tree.trigger_time + struck_analysis_parameters.max_drift_time, 
            6000
        )
        max_drift_line.SetLineStyle(2)
        max_drift_line.Draw()

        legend.AddEntry(tree,"Sum charge E=%.1f" % tree.chargeEnergy,"p")
        legend.Draw()
        canvas.Update()

        if not gROOT.IsBatch():
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
        canvas.Print("keptEvents.pdf")
        n_drawn_events += 1

        i_entry += 1

    canvas.Print("keptEvents.pdf]")
        
        


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print "arguments: [eventlist file] [sis root files]"
        sys.exit(1)

    process_file(sys.argv[1], sys.argv[2])



