#!/usr/bin/env python

"""
to do: 
* reset values to peihao's original ones
* make this work for MC
"""

import os
import sys
import glob
import time

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gSystem
from ROOT import gDirectory
from ROOT import gStyle
from ROOT import TMath
from ROOT import TTree
from ROOT import TEventList
from ROOT import TLine

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

from struck import struck_analysis_parameters
from struck import struck_analysis_cuts

n_chargechannels = struck_analysis_parameters.n_chargechannels

gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import CLHEP

def get_elists(tree, selection, selections):

    n_total_entries = tree.GetEntries()
    selections.append(selection)
    elist_name = "elist%i" % len(selections)
    print "%s selection:" % elist_name
    print "\t" + "\n\t|| ".join(selection.split("||"))
    n_total_entries
    n_entries = tree.Draw(">>%s" % elist_name, selection)
    print "\t%.1e entries in selection (excluded %.1e entries)" % (n_entries, n_total_entries-n_entries)
    elist = gDirectory.Get(elist_name)

    n_entries = tree.Draw(">>n%s" % elist_name, "!(%s)" % selection)
    print "\t%.1e entries in !selection (excluded %.1e entries)" % (n_entries, n_total_entries-n_entries)
    nelist = gDirectory.Get("n%s" % elist_name)
    return elist, nelist

def process_file(filename):

    ## settings
    energy_threshold = 200
    #drifttime_low = 8.0
    drifttime_low = struck_analysis_parameters.drift_time_threshold
    drifttime_high = 9.0
    negative_energy_cut = -20
    selections = []


    print "processing file: ", filename
    start_time = time.clock()

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    root_file = TFile(filename, "READ")
    tree = root_file.Get("tree")
    tree.SetLineWidth(2)
    n_entries = tree.GetEntries()
    n_total_entries = n_entries
    print "%.1e entries in tree" % n_entries

    canvas = TCanvas("canvas","")
    canvas.SetLeftMargin(0.15)
    legend = TLegend(0.5, 0.7, 0.9, 0.9)
    pad = canvas.cd(1)
    pad.SetGrid(1,1)

    ## elist0: all events
    tree.Draw(">>elist0", "")
    elist0 = gDirectory.Get("elist0")

    ## selection1: at least one channel has energy < negative_energy_cut keV
    selection = struck_analysis_cuts.get_negative_energy_cut(negative_energy_cut)
    elist1, nelist1 = get_elists(tree, selection, selections)

    ## selection2: at least one channel has drift time < 8us and energy > 200keV
    selection = struck_analysis_cuts.get_short_drift_time_cut(energy_threshold, drifttime_low)
    elist2, nelist2 = get_elists(tree, selection, selections)

    ## selection3: at least one channel has energy > energy_threshold and 
    ## drift time between drifttime_low and drifttime_high (in us), and not meeting any criteria above
    
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
    
    #selection3 = "(%s)&&(!(%s))&&(!(%s))" % (selection3, selection1, selection2)
    selection3 = "(%s)" % (selection3, )
    selection3 = struck_analysis_cuts.get_long_drift_time_cut(energy_threshold, drifttime_low, drifttime_high)

    ## create event list
    if with_allevents:
        append = "_allevents"
        selection3 = ""

    ## drift time slice
    elist3, nelist3 = get_elists(tree, selection3, selections)

    ## fiducial cut
    selection = struck_analysis_cuts.get_fiducial_cut()
    elist4, nelist4 = get_elists(tree, selection, selections)


    ## drawing histograms
    canvas.Clear()
    pad.SetLogy(0)
    tree.Draw("chargeEnergy >> hist0(175, 0.,1400.)")
    hist0 = gDirectory.Get("hist0")
    hist0.SetLineColor(TColor.kBlack)
    hist0.GetXaxis().SetTitle("Charge energy (keV)")
    hist0.GetYaxis().SetTitle("Counts / %.1f keV" % hist0.GetBinWidth(1))
    #hist0.SetTitle("Charge energy spectrum")
    hist0.SetTitle("")
    hist0.GetYaxis().SetTitleOffset(1.5)
    hist0.SetMaximum(2.5e4)
    legend.AddEntry(hist0, "All events", "l")

    tree.SetEventList(elist1)
    tree.Draw("chargeEnergy >> hist1(175, 0., 1400.)", "", "SAME")
    hist1 = gDirectory.Get("hist1")
    hist1.SetLineColor(TColor.kBlue)
    legend.AddEntry(hist1, "After cutting events with strip E < %i keV" % negative_energy_cut, "l")

    tree.SetEventList(elist2)
    tree.Draw("chargeEnergy >> hist2(175, 0., 1400.)", "", "SAME")
    hist2 = gDirectory.Get("hist2")
    hist2.SetLineColor(TColor.kGreen + 3)
    legend.AddEntry(hist2, "After cutting evts with any strip > %i & drift t < %.1f #mus or > %.1f #mus" % (energy_threshold, drifttime_low, drifttime_high), "l")
    #legend.AddEntry(hist2, "After cutting evts with any strip > %i & drift t < %.1f #mus" % (energy_threshold, drifttime_low), "l")

    tree.SetEventList(elist3)
    tree.Draw("chargeEnergy >> hist3(175, 0., 1400.)", "", "SAME")
    hist3 = gDirectory.Get("hist3")
    hist3.SetLineColor(TColor.kRed + 1)
    #legend.AddEntry(hist3, "Kept events"), "l"
    legend.AddEntry(hist3, "Events with any strip E > %i & drift t > %.1f #mus" % (energy_threshold, drifttime_low)), "l"
    
    tree.SetEventList(elist4)
    n_entries = tree.Draw("chargeEnergy >> hist6(175, 0., 1400.)", "", "SAME")
    print "%i entries after fiducial cut" % n_entries
    hist6 = gDirectory.Get("hist6")
    hist6.SetLineColor(TColor.kBlue+1)
    hist6.SetLineWidth(1)
    legend.AddEntry(hist6, "After fiducial cut", "l")

    tree.SetEventList(elist0-nelist1-nelist2-nelist3-nelist4)
    #tree.SetEventList(elist0-nelist1-nelist2-nelist3)
    n_entries = tree.Draw("chargeEnergy >> hist4(175, 0., 1400.)", "", "SAME")
    print "%i entries after all cuts" % n_entries
    hist4 = gDirectory.Get("hist4")
    hist4.SetLineColor(TColor.kViolet - 6)
    legend.AddEntry(hist4, "After all cuts", "l")
    n_entries = tree.Draw(">>elist")
    elist = gDirectory.Get("elist")
    print "%i entries in elist" % elist.GetN()

    cut = struck_analysis_cuts.get_single_strip_cut(10)
    print cut
    n_entries = tree.Draw("chargeEnergy >> hist5(175, 0., 1400.)", cut, "SAME")
    print "%i entries after single-strip cut" % n_entries
    hist5 = gDirectory.Get("hist5")
    hist5.SetLineColor(TColor.kMagenta)
    legend.AddEntry(hist5, "After single-strip cut", "l")


    legend.Draw()
    canvas.Update()
    # line to mark 570-keV peak
    line = TLine(570, 0.0, 570, hist0.GetMaximum())
    line.SetLineColor(TColor.kGray+2)
    line.SetLineStyle(2)
    #line.Draw()
    canvas.Print("chargeSpectrum.pdf")
    canvas.Print("chargeSpectrum.png")
    
#    canvas.Clear()
#    pad.SetLogy(False)
#    pad.SetLogz()
#    tree.Draw("lightEnergy*570/120:chargeEnergy >> h4(100,0.,1600.,100,0.,2000.)","","colz")
#    canvas.Update()
#    canvas.Print("lightvscharge%s.pdf" % append)
#    canvas.Print("lightvscharge%s.png" % append)

    # write selected events to file
    fout = TFile("eventLists.root", "RECREATE") 
    #tree_selected = tree.CopyTree("")
    #tree_selected.Write()
    elist.Write()
    elist1.Write()
    elist2.Write()
    elist3.Write()
    try:
        elist4.Write()
    except: 
        pass

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



