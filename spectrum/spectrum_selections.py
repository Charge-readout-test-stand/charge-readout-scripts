#!/usr/bin/env python

"""
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

gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import CLHEP

def process_file(filename):

    print "processing file: ", filename
    start_time = time.clock()

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)

    canvas = TCanvas("canvas","", 1700, 900)
    legend = TLegend(0.5, 0.7, 0.9, 0.9)
    pad = canvas.cd(1)
    pad.SetGrid(1,1)

    ## elist0: all events
    tree.Draw(">>elist0", "")
    elist0 = gDirectory.Get("elist0")

    ## selection1: at least one channel has negative energy < -50keV
    selection1 = "energy1_pz[0]<-50"
    for i in range(1, n_chargechannels):
        selection1 += "||energy1_pz[%i]<-50" % (i)
    tree.Draw(">>elist1", selection1)
    elist1 = gDirectory.Get("elist1")

    ## selection2: at least one channel has drift time < 5us and energy > 100keV
    selection2 = "(energy1_pz[0]>100&&rise_time_stop95[0]-trigger_time<5)"
    for i in range(1, n_chargechannels):
        selection2 +="||(energy1_pz[%i]>100&&rise_time_stop95[%i]-trigger_time<5)" % (i,i)
    tree.Draw(">>elist2", selection2)
    elist2 = gDirectory.Get("elist2")

    ## selection3: at least one channel has energy > energy_threshold and 
    ## drift time between drifttime_low and drifttimme_high (in us), and not meeting any criteria above
    
    ## settings
    energy_threshold = 100
    drifttime_low = 5.0
    drifttime_high = 10.0
    with_energyselection = False 
    energylow = 500
    energyhigh = 700
    with_channelselection = False 
    channelselection = [0,1,0,0,0] ## 1-selected, 0-unselected
    with_allevents = False 

    append = ""
    selection3 = ""

    if with_channelselection:
        for i in xrange(len(channelselection)):
            if channelselection[i] == 1:
                if selection3 == "":
                    selection3 = "(energy1_pz[%i]>%f&&rise_time_stop95[%i]-trigger_time>%f&&rise_time_stop95[%i]-trigger_time<%f)" % (i, energy_threshold, i, drifttime_low, i, drifttime_high) 
                    append += "_channel%i" % i
                else:
                    selection3 += "||(energy1_pz[%i]>%f&&rise_time_stop95[%i]-trigger_time>%f&&rise_time_stop95[%i]-trigger_time<%f)" % (i,energy_threshold, i, drifttime_low, i, drifttime_high)
                    append +="_%i" % i
    else:
        append += "_allchannels"
        selection3 = "(energy1_pz[0]>%f&&rise_time_stop95[0]-trigger_time>%f&&rise_time_stop95[0]-trigger_time<%f)" % (energy_threshold, drifttime_low, drifttime_high)
        for i in range(1, n_chargechannels):
            selection3 += "||(energy1_pz[%i]>%f&&rise_time_stop95[%i]-trigger_time>%f&&rise_time_stop95[%i]-trigger_time<%f)" % (i, energy_threshold, i, drifttime_low, i, drifttime_high)

    if with_energyselection:
        append += "_energy_%ito%i" % (energylow, energyhigh)
        selection3 = "(chargeEnergy>%i&&chargeEnergy<%i)&&(%s)" % (
                                    energylow, energyhigh, selection3)
    
    selection3 = "(%s)&&(!(%s))&&(!(%s))" % (selection3, selection1, selection2)

    ## create event list
    if with_allevents:
        append = "_allevents"
        selection3 = ""
    tree.Draw(">>elist3", selection3)
    elist3 = gDirectory.Get("elist3")
    elist3.Print()

    ## drawing histograms
    canvas.Clear()
    pad.SetLogy()
    tree.Draw("chargeEnergy >> hist0(375, 0.,3000.)")
    hist0 = gDirectory.Get("hist0")
    hist0.SetLineColor(TColor.kBlack)
    hist0.GetXaxis().SetTitle("Charge energy (keV)")
    hist0.GetYaxis().SetTitle("Counts per 8keV bin")
    hist0.SetTitle("Charge energy spectrum")
    legend.AddEntry(hist0, "All events", "l")

    tree.SetEventList(elist1)
    tree.Draw("chargeEnergy >> hist1(375, 0., 3000.)", "", "SAME")
    hist1 = gDirectory.Get("hist1")
    hist1.SetLineColor(TColor.kBlue)
    legend.AddEntry(hist1, "Negative energy < -50 keV", "l")

    tree.SetEventList(elist2)
    tree.Draw("chargeEnergy >> hist2(375, 0., 3000.)", "", "SAME")
    hist2 = gDirectory.Get("hist2")
    hist2.SetLineColor(TColor.kGreen + 3)
    legend.AddEntry(hist2, "Drift time < 5 us", "l")

    tree.SetEventList(elist3)
    tree.Draw("chargeEnergy >> hist3(375, 0., 3000.)", "", "SAME")
    hist3 = gDirectory.Get("hist3")
    hist3.SetLineColor(TColor.kRed + 1)
    legend.AddEntry(hist3, "Kept events"), "l"
    
    tree.SetEventList(elist0-elist1-elist2-elist3)
    tree.Draw("chargeEnergy >> hist4(375, 0., 3000.)", "", "SAME")
    hist4 = gDirectory.Get("hist4")
    hist4.SetLineColor(TColor.kViolet - 6)
    legend.AddEntry(hist4, "Others", "l")

    legend.Draw()
    canvas.Update()
    canvas.Print("chargeSpectrums.pdf")
    canvas.Print("chargeSpectrums.png")
    
#    canvas.Clear()
#    pad.SetLogy(False)
#    pad.SetLogz()
#    tree.Draw("lightEnergy*570/120:chargeEnergy >> h4(100,0.,2000.,100,0.,2000.)","","colz")
#    canvas.Update()
#    canvas.Print("lightvscharge%s.pdf" % append)
#    canvas.Print("lightvscharge%s.png" % append)

    # write selected events to file
    fout = TFile("eventLists.root", "RECREATE") 
    #tree_selected = tree.CopyTree("")
    #tree_selected.Write()
    elist1.Write()
    elist2.Write()
    elist3.Write()

    end_time = time.clock()
    print "processing time = ", end_time, " s" 

    root_file.Close()
    fout.Close()



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



