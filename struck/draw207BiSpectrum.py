#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* max
* channel

arguments [tier1 sis root files]
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
    max_adc_value = tree.GetMaximum("adc_max")
    min_adc_value = tree.GetMinimum("adc_min")
    print "max digitized value", max_adc_value
    print "min digitized value", min_adc_value

    # set up parameters for histograms
    #n_bins = 200
    #min_bin = min_adc_value - 1
    #max_bin = max_adc_value + 1
    min_bin = 0
    #max_bin = pow(2, 14) # ADC max is 2^14
    #n_bins = max_bin/64
    max_bin= 5000
    n_bins = max_bin/20
    print "n_bins", n_bins


    # for 11pm runs on 12 Aug 2015:
    offset = 1600

    # for some pulser tests on 12 Aug 2015 morning:
    if basename == "sis3316_test_data_0_100mVpulser_noHV_noXe":
        print "using Aug 12 pulser offset..."
        offset = 4050

    draw_string = "(adc_max - %s)" % offset
    print "draw_string:", draw_string

    # draw X29
    hist0 = TH1D("hist0", "", n_bins, min_bin, max_bin)
    hist0.SetLineWidth(2)
    hist0.SetLineColor(TColor.kRed)
    #hist0.SetFillColor(TColor.kBlue)
    hist0.SetFillStyle(3004)
    print "entries in ch0:", tree.Draw(
        "%s*570/3800 >> hist0" % draw_string,
        "channel==0",
        "goff"
    )
    max_bin_height0 = hist0.GetBinContent(hist0.GetMaximumBin())

    # draw X28
    hist1 = TH1D("hist1", "", n_bins, min_bin, max_bin)
    hist1.SetLineWidth(2)
    hist1.SetLineColor(TColor.kGreen+1)
    #hist1.SetFillColor(TColor.kRed)
    hist1.SetFillStyle(3005)
    print "entries in ch1:", tree.Draw(
        "%s*570/1900 >> hist1" % draw_string,
        "channel==1",
        "goff"
    )
    max_bin_height1 = hist1.GetBinContent(hist1.GetMaximumBin())

    # draw X27
    hist2 = TH1D("hist2", "", n_bins, min_bin, max_bin)
    hist2.SetLineWidth(2)
    hist2.SetLineColor(TColor.kBlue)
    #hist2.SetFillColor(TColor.kGreen+1)
    hist2.SetFillStyle(3006)
    print "entries in ch2:", tree.Draw(
        "%s*570/2800 >> hist2" % draw_string,
        "channel==2",
        "goff"
    )
    max_bin_height2 = hist2.GetBinContent(hist2.GetMaximumBin())

    # find the highest max, among all 3 channels:
    max = max_bin_height0
    if (max_bin_height1 > max): max = max_bin_height1
    if (max_bin_height2 > max): max = max_bin_height2

    hist0.SetMaximum(max*1.1)
    hist0.SetXTitle("Energy [keV]")
    hist0.SetYTitle("Counts/%.1f keV" % (max_bin/n_bins))

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.AddEntry(hist2, "X27", "l")
    legend.AddEntry(hist1, "X28", "l")
    legend.AddEntry(hist0, "X29", "l")
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



