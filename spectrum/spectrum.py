#!/usr/bin/env python

"""
This script creates an eventlist from a tree. The criteria is specified in the script (subject to modification).

The eventlist will be saved to a root file. The script "ViewEventsUsingEventlist.py" can be run afterwards to view the events.

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
from ROOT import gDirectory
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TMath
from ROOT import TTree
from ROOT import TEventList

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

import struck_analysis_parameters
n_chargechannels = struck_analysis_parameters.n_chargechannels

def process_file(filename):

    print "processing file: ", filename
    start_time = time.clock()

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.Draw(">>elist_all", "")  ## save eventlist_all
    elist_all = gDirectory.Get("elist_all")
    tree.SetLineWidth(2)

    canvas = TCanvas("canvas","", 1700, 900)
    pad = canvas.cd(1)
    pad.SetGrid(1,1)

    ## selection1: at least one channel has negative energy < -50keV
    selection1 = "energy1_pz[0]<-50"
    for i in range(1, n_chargechannels):
        selection1 += "||energy1_pz[%i]<-50" % (i)

    ## selection2: at least one channel has drift time < 5us and energy > 100keV
    selection2 = "(energy1_pz[0]>100&&rise_time_stop95[0]-trigger_time<5)"
    for i in range(1, n_chargechannels):
        selection2 +="||(energy1_pz[%i]>100&&rise_time_stop95[%i]-trigger_time<5)" % (i,i)

    ## selection3: at least one channel has energy > energy_threshold and 
    ## drift time according to drifttime_table, and not meeting any criteria above
    
    ## settings
    energy_threshold = 100
    #drifttime_table = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    drifttime_table = [8.5, 9.5]
    with_chargeenergyselection = False
    energylow = 1000 
    energyhigh = 1200
    with_lightenergyselection = False 
    lightenergylow = 450
    lightenergyhigh = 800
    with_channelselection = False 
    channelselection = [0,1,0,0,0] ## 1-selected, 0-unselected
    with_allevents = False 

    for i_drifttime in xrange(len(drifttime_table)-1):
        selection3 = ""
        drifttime_low = drifttime_table[i_drifttime]
        drifttime_high = drifttime_table[i_drifttime + 1]
        append = "_drifttime_%.2fto%.2f" % (drifttime_low, drifttime_high)

        ## start making selection string
        if with_channelselection:
            for i in xrange(len(channelselection)):
                if channelselection[i] == 1:
                    if selection3 == "":
                        selection3 = "(energy1_pz[%i]>%.2f&&rise_time_stop95[%i]-trigger_time>%.2f&&rise_time_stop95[%i]-trigger_time<%.2f)" % (i, energy_threshold, i, drifttime_low, i, drifttime_high) 
                        append += "_channel%i" % i
                    else:
                        selection3 += "||(energy1_pz[%i]>%.2f&&rise_time_stop95[%i]-trigger_time>%.2f&&rise_time_stop95[%i]-trigger_time<%.2f)" % (i, energy_threshold, i, drifttime_low, i, drifttime_high)
                        append +="_%i" % i
            if selection3 == "": ## if no channel is selected
                print "no channel selected!"
                sys.exit(1)
        else:
            append += "_allchannels"
            selection3 = "(energy1_pz[0]>%.2f&&rise_time_stop95[0]-trigger_time>%.2f&&rise_time_stop95[0]-trigger_time<%.2f)" % (energy_threshold, drifttime_low, drifttime_high)
            for i in range(1, n_chargechannels):
                selection3 += "||(energy1_pz[%i]>%.2f&&rise_time_stop95[%i]-trigger_time>%.2f&&rise_time_stop95[%i]-trigger_time<%.2f)" % (i, energy_threshold, i, drifttime_low, i, drifttime_high)
        selection3 = "(%s)" % selection3  ## wrap the conditions

        if with_chargeenergyselection:
            append += "_energy_%ito%i" % (energylow, energyhigh)
            selection3 = "(chargeEnergy>%i&&chargeEnergy<%i&&(%s))" % (
                                        energylow, energyhigh, selection3)

        if with_lightenergyselection:
            append += "_lightenergy_%ito%i" % (lightenergylow, lightenergyhigh)
            selection3 = "(lightEnergy>%i&&lightEnergy<%i&&(%s))" % (
                                        lightenergylow, lightenergyhigh, selection3)
        
        selection3 = "(%s)&&(!(%s))&&(!(%s))" % (selection3, selection1, selection2)

        ## create event list
        if with_allevents:
            append = "_allevents"
            selection3 = ""
        tree.SetEventList(elist_all)
        tree.Draw(">>elist", selection3)
        elist = gDirectory.Get("elist")
        elist.Print()

        ## drawing histograms
        tree.SetEventList(elist)

        canvas.Clear()
        pad.SetLogy()
        tree.Draw("chargeEnergy >> h2(250,0.,2000.)")
        h2 = gDirectory.Get("h2")
        h2.SetXTitle("Sum of charge channel energy (keV)")
        h2.SetYTitle("Counts per 8keV bin")
        canvas.Update()
        canvas.Print("charge%s.pdf" % append)
        canvas.Print("charge%s.png" % append)
        
        canvas.Clear()
        tree.Draw("lightEnergy >> h3(500,0.,4000.)")
        h3 = gDirectory.Get("h3")
        h3.SetXTitle("PMT energy (keV)")
        h3.SetYTitle("Counts per 8keV bin")
        canvas.Update()
        canvas.Print("light%s.pdf" % append)
        canvas.Print("light%s.png" % append)
        
        canvas.Clear()
        pad.SetLogy(False)
        pad.SetLogz()
        tree.Draw("lightEnergy:chargeEnergy >> h4(100,0.,2000.,100,0.,2000.)","","colz")
        h4 = gDirectory.Get("h4")
        h4.SetXTitle("Sum of charge channel energy (keV)")
        h4.SetYTitle("PMT energy (keV)")
        canvas.Update()
        canvas.Print("lightvscharge%s.pdf" % append)
        canvas.Print("lightvscharge%s.png" % append)

        pad.SetLogy(True)
        pad.SetLogz(False)
        for i in xrange(n_chargechannels):
            canvas.Clear()
            tree.Draw("energy1_pz[%i] >> h(250,0.,2000.)" % i)
            h = gDirectory.Get("h")
            h.SetXTitle("Channel %i energy (keV)" % i)
            h.SetYTitle("Counts per 8keV bin")
            canvas.Update()
            canvas.Print("charge%i%s.pdf" % (i, append))
            canvas.Print("charge%i%s.png" % (i, append))

        # write selected events to file
        fout = TFile("event%s.root" % append, "RECREATE") 
        #tree_selected = tree.CopyTree("")
        #tree_selected.Write()
        elist.Write()
        elist.Clear()
        fout.Close()

    end_time = time.clock()
    print "processing time = ", end_time, " s" 

    root_file.Close()



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



