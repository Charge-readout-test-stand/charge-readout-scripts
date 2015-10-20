#!/usr/bin/env python

"""
This script draws a spectrum from a root tree. The following branches are
assumed to exist:
* max
* channel

arguments [sis tier 1 root files]
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


def draw_hist(basename, tree, channel, color=TColor.kBlack, fill_style=3004):

    # set up parameters for histograms
    min_bin = 0
    max_bin = pow(2, 14) # ADC max is 2^14
    n_bins = max_bin

    # find baseline
    canvas = TCanvas("canvas1","")
    canvas.SetLogy(1)
    max_bin = pow(2, 14) # ADC max is 2^14
    baseline_hist = TH1D("baseline_hist", "ch %i baseline" % channel, max_bin, 0, max_bin)
    n_entries = tree.Draw("wfm >> baseline_hist","channel == %i && Iteration$<350" % channel)
    baseline_hist.SetLineColor(TColor.kBlue+1)
    baseline_hist.SetFillColor(TColor.kBlue+1)
    mean = baseline_hist.GetMean()

    if n_entries > 0:
        print "%i entries in baseline hist" % n_entries
        baseline_hist.SetAxisRange(mean-200, mean+200)
        print "mean", mean
        canvas.Update()
        canvas.Print("%s_ch%i_baseline.png" % (basename, channel))
    

    name = "hist%i" % channel
    hist = TH1D(name, "", n_bins, min_bin, max_bin)
    hist.SetLineWidth(2)
    hist.SetLineColor(color)
    hist.SetFillColor(color)
    hist.SetFillStyle(fill_style)
    n_entries = tree.Draw("adc_max - %s >> %s" % (mean, name), "channel==%i" % channel, "goff")
    if n_entries > 0:
        print "entries in ch %i:" % channel, n_entries
    max_bin_height = hist.GetBinContent(hist.GetMaximumBin())

    return hist, max_bin_height


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
    canvas.SetTopMargin(0.2)

    # find the maximum energy value in the tree, among all channels
    print "total entries in tree", tree.GetEntries()
    max_mca_value = tree.GetMaximum("adc_max")
    min_mca_value = tree.GetMinimum("adc_max")
    print "max digitized value", max_mca_value
    print "min digitized value", min_mca_value

    max_bin_height = 0

    colors = [TColor.kBlue, TColor.kRed, TColor.kGreen+1, TColor.kViolet]
    fillStyle = [3004, 3005, 3006, 3007, 3001, 3002, 3003, 3016,
      3017, 3018, 3020, 3021] 

    hists = []

    # set up a legend
    legend = TLegend(0.1, 0.81, 0.9, 0.99)
    legend.SetNColumns(4)

    for channel in xrange(16):

        i_color = channel % len(colors)
        i_fill = channel % len(fillStyle)
        hist, i_max_bin_height = draw_hist(basename, tree, channel, colors[i_color],
        fillStyle[i_fill])
        n_entries = hist.GetEntries()

        legend.AddEntry(hist, "ch %i (%i)" % (channel, n_entries), "f")
        hists.append(hist)

        if i_max_bin_height > max_bin_height:
            max_bin_height = i_max_bin_height

    hists[0].SetAxisRange(0, 200)
    hists[0].SetMaximum(max_bin_height*1.1)
    hists[0].SetXTitle("Energy [ADC units]")
    hists[0].SetYTitle("Counts")
    hists[0].Draw()


    for hist in hists[1:]:
        hist.Draw("same")
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_spectrum.png" % basename)



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



