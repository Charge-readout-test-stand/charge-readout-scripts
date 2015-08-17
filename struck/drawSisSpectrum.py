#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* max
* channel

arguments [sis root files]
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

    # find the maximum energy value in the tree, among all channels
    print "total entries in tree", tree.GetEntries()
    max_mca_value = tree.GetMaximum("adc_max")
    min_mca_value = tree.GetMinimum("adc_max")
    print "max digitized value", max_mca_value
    print "min digitized value", min_mca_value

    # set up parameters for histograms
    #n_bins = 200
    #min_bin = min_mca_value - 1
    #max_bin = max_mca_value + 1
    min_bin = 0
    max_bin = pow(2, 14) # ADC max is 2^14
    n_bins = max_bin/64
    print "n_bins", n_bins

    # draw channel 0
    hist0 = TH1D("hist0", "", n_bins, min_bin, max_bin)
    hist0.SetLineWidth(2)
    hist0.SetLineColor(TColor.kBlue)
    hist0.SetFillColor(TColor.kBlue)
    hist0.SetFillStyle(3004)
    print "entries in ch0:", tree.Draw("adc_max >> hist0","channel==0","goff")
    max_bin_height0 = hist0.GetBinContent(hist0.GetMaximumBin())

    # draw channel 1
    hist1 = TH1D("hist1", "", n_bins, min_bin, max_bin)
    hist1.SetLineWidth(2)
    hist1.SetLineColor(TColor.kRed)
    hist1.SetFillColor(TColor.kRed)
    hist1.SetFillStyle(3005)
    print "entries in ch1:", tree.Draw("adc_max >> hist1","channel==1","goff")
    max_bin_height1 = hist1.GetBinContent(hist1.GetMaximumBin())

    # draw channel 2
    hist2 = TH1D("hist2", "", n_bins, min_bin, max_bin)
    hist2.SetLineWidth(2)
    hist2.SetLineColor(TColor.kGreen+1)
    hist2.SetFillColor(TColor.kGreen+1)
    hist2.SetFillStyle(3006)
    print "entries in ch2:", tree.Draw("adc_max >> hist2","channel==2","goff")
    max_bin_height2 = hist2.GetBinContent(hist2.GetMaximumBin())

    # find the highest max, among all 3 channels:
    max = max_bin_height0
    if (max_bin_height1 > max): max = max_bin_height1
    if (max_bin_height2 > max): max = max_bin_height2

    hist0.SetMaximum(max*1.1)
    hist0.SetXTitle("Energy [ADC units]")
    hist0.SetYTitle("Counts")

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.AddEntry(hist0, "ch 0", "f")
    legend.AddEntry(hist1, "ch 1", "f")
    legend.AddEntry(hist2, "ch 2", "f")
    legend.SetNColumns(3)

    hist0.Draw()
    hist1.Draw("same")
    hist2.Draw("same")
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_spectrum.png" % basename)





if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



