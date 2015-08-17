#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* totalEnergy
* energy
* nHits

arguments [sis root files of events]
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

    # set up parameters for histograms
    n_bins = 200
    min_bin = 0
    max_bin = 2500

    # draw coherent sum hist
    hist0 = TH1D("hist0", "", n_bins, min_bin, max_bin)
    hist0.SetLineWidth(2)
    hist0.SetLineColor(TColor.kBlue)
    tree.Draw("totalEnergy >> hist0","","goff")

    # draw incoherent sum hist
    hist1 = TH1D("hist1", "", n_bins, min_bin, max_bin)
    hist1.SetLineWidth(2)
    hist1.SetLineColor(TColor.kRed)
    tree.Draw("energy >> hist1","","goff")

    # single-wire hist
    hist2 = TH1D("hist2", "", n_bins, min_bin, max_bin)
    hist2.SetLineWidth(2)
    hist2.SetLineColor(TColor.kGreen+1)
    tree.Draw("totalEnergy >> hist2","nHits==1","goff")

    # multi-wire hist
    hist3 = TH1D("hist3", "", n_bins, min_bin, max_bin)
    hist3.SetLineWidth(2)
    hist3.SetLineColor(TColor.kBlack)
    tree.Draw("totalEnergy >> hist3","nHits>1","goff")

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
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
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_event_spectrum.png" % basename)

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



