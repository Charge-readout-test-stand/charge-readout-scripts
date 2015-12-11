#!/usr/bin/env python

"""
This script draws histograms of total energies for different event categories
See "Event categories" in the script for further information

The script saves the histograms into file "ChargeSpectrum.root" (Warning: will replace the old file!)

The script also saves the event lists for categories into file "ChargeSpectrum_eventlist.txt", using json

To run:
python /path/to/this/script /path/to/tier3_root_file
"""

import os
import sys
import glob
import time

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

def process_file(filename):

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    fout = TFile("ChargeSpectrum.root", "RECREATE") ## file to save histograms

    canvas = TCanvas("canvas","", 1700, 900)

    ## Event categories
    hist_charge0 = TH1D("spectrum_charge0", "Spectrum: no energy cut", 250, 100., 2100.) # all events   
    hist_charge1 = TH1D("spectrum_charge1", "Spectrum: no energy cut", 250, 100., 2100.)
    # all kept events: at least one channel has energy > 300 and drift time between 8.5 and 10.0 us, and not meeting any criteria below
    eventlist1 = []
    hist_charge2 = TH1D("spectrum_charge2", "Spectrum: no energy cut", 250, 100., 2100.)
    # events with negative energy < -50 keV
    eventlist2 = []
    hist_charge3 = TH1D("spectrum_charge3", "Spectrum: no energy cut", 250, 100., 2100.)
    # events where at least one channel has drift time < 5 us and energy > 100 keV
    eventlist3 = []
    hist_charge4 = TH1D("spectrum_charge4", "Spectrum: no energy cut", 250, 100., 2100.)
    # events where more than two channels have energy > 200 keV
    eventlist4 = []
    hist_charge5 = TH1D("spectrum_charge5", "Spectrum: no energy cut", 250, 100., 2100.)
    # all other events
    eventlist5 = []

    tree.GetEntry(0)
    trigger_time_0 = tree.trigger_time

    events = 0
    reporting_period = 10000
    now = time.clock()
    start_time = now
    last_time = now
    n_events = tree.GetEntries()
    for i_entry in xrange(n_events):
        if i_entry % reporting_period == 0:
            now = time.clock()
            print "==> event %i of %i (%.2f percent, %i events in %.1f seconds, %.2f seconds elapsed)" % (
                i_entry,
                n_events, 
                100.0*i_entry/n_events,
                reporting_period,
                now - last_time,
                now - start_time,
            )
            last_time = now

        tree.GetEntry(i_entry)

        energy = 0
        for i in xrange(5):
            energy = energy + tree.energy1_pz[i]
        hist_charge0.Fill(energy)  ## Calculate total energy and fill in histogram for all drift times

        if tree.trigger_time == 0:
            trigger_time = trigger_time_0
        else:
            trigger_time = tree.trigger_time  ## for trigger_time == 0, set trigger_time to the trigger time in the first entry (for 5th run ONLY)

        ## the following scripts categorizes each event and fill in the histograms and eventlists
        flag = 0
        counts = 0
        for i in xrange(5):
            if tree.energy1_pz[i] < -50:
                flag = 1
                hist_charge2.Fill(energy)
                eventlist2.append(i_entry)
                break
            elif tree.energy1_pz[i] > 200:
                counts = counts + 1
            
            drift_time = tree.rise_time_stop95[i] - trigger_time
            if drift_time < 5.0 and tree.energy1_pz[i] > 100:
                flag = 1
                hist_charge3.Fill(energy)
                eventlist3.append(i_entry)
                break
            
            if tree.energy1_pz[i] > 300 and 8.5 < drift_time and drift_time < 10.0:
                flag = 2

        if counts > 2:
            eventlist4.append(i_entry)
            hist_charge4.Fill(energy)        
        elif flag == 2:
            hist_charge1.Fill(energy)
            eventlist1.append(i_entry)
            events = events + 1
        else:
            hist_charge5.Fill(energy)
            eventlist5.append(i_entry)


    print "Number of events: ", events

    ## draw histograms and legends
    canvas.Clear()
    pad = canvas.cd(1)
    pad.SetGrid(1,1)
    pad.SetLogy()
    legend = TLegend(0.7, 0.8, 0.9, 0.9)

    hist_charge0.SetLineWidth(2)
    hist_charge0.SetLineColor(1)
    hist_charge0.GetXaxis().SetTitle("Combined Energy (keV)")
    hist_charge0.GetYaxis().SetTitle("Counts per 8keV bin")
    legend.AddEntry(hist_charge0, "All events")
    hist_charge0.Draw()

    hist_charge2.SetLineWidth(2)
    hist_charge2.SetLineColor(4)
    legend.AddEntry(hist_charge2, "Negative energy < -50 keV")
    hist_charge2.Draw("same")    

    hist_charge3.SetLineWidth(2)
    hist_charge3.SetLineColor(6)
    legend.AddEntry(hist_charge3, "Drift time < 5 us")
    hist_charge3.Draw("same")   

    hist_charge4.SetLineWidth(2)
    hist_charge4.SetLineColor(7)
    legend.AddEntry(hist_charge4, "More than 2 channels have > 200 keV")
    hist_charge4.Draw("same") 

    hist_charge5.SetLineWidth(2)
    hist_charge5.SetLineColor(8)
    legend.AddEntry(hist_charge5, "Other")
    hist_charge5.Draw("same") 

    hist_charge1.SetLineWidth(2)
    hist_charge1.SetLineColor(2)
    legend.AddEntry(hist_charge1, "Kept events w/ drift time 8.5 to 10.0 us")
    hist_charge1.Draw("same")

    legend.Draw()
    canvas.Update()
    #raw_input("Press Enter to continue...")
    canvas.Print("ChargeSpectrum.png")
    canvas.Print("ChargeSpectrum.pdf")

    ## write histograms to file
    hist_charge0.Write()
    hist_charge1.Write()
    hist_charge2.Write()
    hist_charge3.Write()
    hist_charge4.Write()
    hist_charge5.Write()

    root_file.Close()
    fout.Close()

    ## write eventlists to file
    import json
    eventlists = {'list1': eventlist1, 'list2': eventlist2, 'list3': eventlist3, 'list4': eventlist4, 'list5': eventlist5}
    with open("ChargeSpectrum_eventlist.txt", "w") as fout:
        json.dump(eventlists, fout)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



