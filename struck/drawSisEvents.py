#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* totalEnergy
* energy
* nHits

arguments [sis tier 2 root files of events]
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
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TH1D
from ROOT import TH2D


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(filename):

    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    print "%i total entries" % tree.GetEntries()

    # set up parameters for histograms
    n_bins = 100
    min_bin = 0
    #max_bin = 4000
    max_bin = 8000


    # draw coherent sum hist
    hist0 = TH1D("hist0", "", n_bins, min_bin, max_bin)
    hist0.SetLineWidth(2)
    hist0.SetLineColor(TColor.kBlue)
    tree.Draw("totalEnergy >> hist0","totalEnergy>0","goff")
    #tree.Draw("energy[1]+energy[2] >> hist0","energy[1]+energy[2]>0","goff")
    print "entries in coherent hist0:", hist0.GetEntries()
    print "mean:", hist0.GetMean()

    # draw incoherent sum hist
    hist1 = TH1D("hist1", "", n_bins, min_bin, max_bin)
    hist1.SetLineWidth(2)
    hist1.SetLineColor(TColor.kRed)
    tree.Draw("energy >> hist1","energy>0","goff")
    #tree.Draw("energy[1] >> hist1","energy[1]>0","goff")
    #print "entries in hist1:", hist1.GetEntries()
    #tree.Draw("energy[2] >> +hist1","energy[2]>0","goff")
    print "entries in incoherent hist1:", hist1.GetEntries()
    print "mean:", hist1.GetMean()

    # single-wire hist
    hist2 = TH1D("hist2", "", n_bins, min_bin, max_bin)
    hist2.SetLineWidth(2)
    hist2.SetLineColor(TColor.kGreen+1)
    tree.Draw("totalEnergy >> hist2","nHits==1","goff")
    #tree.Draw("energy[1] >> hist2","energy[2]==0 && energy[1]>0","goff")
    #print "entries in hist2:", hist2.GetEntries()
    #tree.Draw("energy[2] >> +hist2","energy[1]==0 && energy[2]>0","goff")
    print "entries in single-wire hist2:", hist2.GetEntries()
    print "mean:", hist2.GetMean()

    # multi-wire hist
    hist3 = TH1D("hist3", "", n_bins, min_bin, max_bin)
    hist3.SetLineWidth(2)
    hist3.SetLineColor(TColor.kBlack)
    tree.Draw("totalEnergy >> hist3","nHits>1","goff")
    #tree.Draw("energy[1]+energy[2] >> hist3","energy[1]>0 && energy[2]>0","goff")
    print "entries in multi-wire hist3:", hist3.GetEntries()
    print "mean:", hist3.GetMean()

    # set up a legend
    legend = TLegend(0.11, 0.91, 0.9, 0.99)
    legend.AddEntry(hist0, "total energy", "l")
    legend.AddEntry(hist1, "wire energies", "l")
    legend.AddEntry(hist2, "total energy, n wires == 1", "l")
    legend.AddEntry(hist3, "total energy, n wires > 1", "l")
    legend.SetNColumns(2)

    hist0.SetXTitle("Energy [keV]")
    hist0.SetYTitle("Counts / %i keV" % (max_bin/n_bins))

    hist0.Draw()
    hist1.Draw("same")
    hist2.Draw("same")
    hist3.Draw("same")
    canvas.SetLeftMargin(0.11)
    hist0.GetYaxis().SetTitleOffset(1.2)
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_event_spectrum.png" % basename)
    canvas.SetLogy(0)
    hist0.SetMaximum(1800)
    canvas.Update()
    canvas.Print("%s_event_spectrum_lin.png" % basename)


    #-------------------------------------------------------------------------------
    # repeat for different channel pair combinations
    #-------------------------------------------------------------------------------

    # I have just been modifying these options by hand and running the script
    # multple times...
    #pair = [0, 1] # modify this line only
    #pair = [0, 2] # modify this line only
    pair = [1, 2] # modify this line only


    # these are the channel assignments
    title = ["X29", "X28", "X27"]
    # [0] = X29
    # [0] = X28
    # [0] = X27

    # make titles for plot naming
    ch1_title = title[pair[0]]
    ch2_title = title[pair[1]]

    # make strings to use with TTree:Draw()
    ch1 = "energy[%i]" % pair[0]
    ch2 = "energy[%i]" % pair[1]

    print "drawing %s vs %s: %s and %s" % (ch1_title, ch2_title, ch1, ch2)


    # draw coherent sum hist
    #tree.Draw("totalEnergy >> hist0","","goff")
    tree.Draw("%s+%s >> hist0" % (ch1, ch2),"%s+%s>0" % (ch1, ch2),"goff")
    print "entries in coherent hist0:", hist0.GetEntries()

    # draw incoherent sum hist
    #tree.Draw("energy >> hist1","","goff")
    tree.Draw("%s >> hist1" % ch1,"%s>0" % ch1,"goff")
    print "entries in hist1:", hist1.GetEntries()
    tree.Draw("%s >> +hist1" % ch2,"%s>0" % ch2,"goff")
    print "entries in incoherent hist1:", hist1.GetEntries()

    # single-wire hist
    #tree.Draw("totalEnergy >> hist2","nHits==1","goff")
    tree.Draw("%s >> hist2" % ch1,"%s==0 && %s>0" % (ch2, ch1),"goff")
    print "entries in hist2:", hist2.GetEntries()
    tree.Draw("%s >> +hist2" % ch2,"%s==0 && %s>0" % (ch1, ch2),"goff")
    print "entries in single-wire hist2:", hist2.GetEntries()

    # multi-wire hist
    #tree.Draw("totalEnergy >> hist3","nHits>1","goff")
    tree.Draw("%s+%s >> hist3" % (ch1, ch2),"%s>0 && %s>0" % (ch1, ch2),"goff")
    print "entries in multi-wire hist3:", hist3.GetEntries()

    # set up a legend
    legend = TLegend(0.11, 0.91, 0.9, 0.99)
    legend.AddEntry(hist0, "total energy", "l")
    legend.AddEntry(hist1, "wire energies", "l")
    legend.AddEntry(hist2, "total energy, n wires == 1", "l")
    legend.AddEntry(hist3, "total energy, n wires > 1", "l")
    legend.SetNColumns(2)

    hist0.SetXTitle("Energy [keV]")
    hist0.SetYTitle("Counts / %i keV" % (max_bin/n_bins))

    hist0.Draw()
    hist1.Draw("same")
    hist2.Draw("same")
    hist3.Draw("same")
    canvas.SetLeftMargin(0.11)
    hist0.GetYaxis().SetTitleOffset(1.2)
    legend.Draw()
    canvas.SetLogy(1)
    hist0.SetMaximum(-1111)
    canvas.Update()
    canvas.Print("%s_event_spectrum_%s_%s.png" % (basename, ch1_title, ch2_title))
    canvas.SetLogy(0)
    hist0.SetMaximum(1500)
    canvas.Update()
    canvas.Print("%s_event_spectrum_lin_%s_%s.png" % (basename, ch1_title, ch2_title))


    #-------------------------------------------------------------------------------
    # draw some 2D correlation plots
    #-------------------------------------------------------------------------------

    canvas.SetLogy(0)
    canvas.SetLeftMargin(0.11)
    #canvas.SetLogz(1)
    n_bins = 60
    max_bin = 2000
    min_bin = 120
    #hist = TH2D("hist","", 100, 120, 2000, 100, 120, 2000)
    hist = TH2D("hist","", n_bins, min_bin, max_bin, n_bins, min_bin, max_bin)
    hist.GetYaxis().SetTitleOffset(1.2)


    # 2: 27
    # 1: 28
    # 0: 29

    tree.Draw("energy[1]:energy[2] >> hist","energy[1] > 120 && energy[2] > 120","goff")
    hist.SetYTitle("X28 Energy [keV]")
    hist.SetXTitle("X27 Energy [keV]")
    hist.Draw("colz")
    canvas.Update()
    canvas.Print("%s_X28_vs_X27.png" % basename)

    tree.Draw("energy[1]:energy[0] >> hist","energy[1] > 120 && energy[0] > 120","goff")
    hist.SetYTitle("X28 Energy [keV]")
    hist.SetXTitle("X29 Energy [keV]")
    hist.Draw("colz")
    canvas.Update()
    canvas.Print("%s_X28_vs_X29.png" % basename)

    tree.Draw("energy[0]:energy[2] >> hist","energy[0] > 120 && energy[2] > 120","goff")
    hist.SetYTitle("X27 Energy [keV]")
    hist.SetXTitle("X29 Energy [keV]")
    hist.Draw("colz")
    canvas.Update()
    canvas.Print("%s_X27_vs_X29.png" % basename)



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



