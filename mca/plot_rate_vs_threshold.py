#!/bin/env python

from ROOT import gROOT
#gROOT.SetBatch(True)
import ROOT
import sys
import os.path

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


def get_rate_vs_threshold(hist, livetime):
    print hist.GetTitle()
    print "\t %i entries in hist" % hist.GetEntries()
    print "\t livetime: %.2f seconds" % livetime


    # scale hist by 1 / livetime
    total_integral = hist.Integral()
    print "\t total counts in hist:", total_integral
    print "\t total counts / second:", total_integral/livetime
    hist.Scale(1.0/livetime)
    #hist.Rebin(64)


    graph = ROOT.TGraph()

    n_bins = hist.GetNbinsX()
    print "n_bins:", n_bins
    #n_bins = 10 # debugging

    for i_bin in xrange(n_bins + 2):

        # integrate from the last bin to first
        energy = hist.GetBinLowEdge(i_bin)
        content = hist.GetBinContent(i_bin)
        integral = hist.Integral(i_bin, n_bins+2)
        if i_bin < 10:
            print "bin %i | energy %.2f | content %.2f | integral % .2f" % (i_bin, energy, content, integral)

        graph.SetPoint(i_bin, energy, integral)
        
    canvas = ROOT.TCanvas("canvas")
    canvas.SetGrid(1,1)
    canvas.SetLogy(1)

    #hist.SetAxisRange(0, 3000)
    #hist.Draw()
    #canvas.Update()
    #val = raw_input("press any key to continue")

    graph.SetLineWidth(2)
    graph.SetLineColor(ROOT.TColor.kGreen+2)
    #graph.SetFillColor(ROOT.TColor.kGreen+2)
    graph.Draw("apl")
    frame_hist = graph.GetHistogram()
    frame_hist.SetXTitle("Energy [MCA units]")
    frame_hist.SetYTitle("Data rate [counts / second]")
    frame_hist.SetMinimum(1e-3)
    frame_hist.SetMaximum(2.0*frame_hist.GetMaximum())
    frame_hist.SetAxisRange(0, 1000)

    # give some arbitrary scaling to the hist so we can see its features:
    #hist.Scale(livetime/10.0)
    hist.Draw("same")
    graph.Draw("pl")

    canvas.Update()
    canvas.Print("rate_%s.png" % basename)
    canvas.Print("rate_%s.pdf" % basename)
    val = raw_input("press any key to continue")


if __name__ == "__main__":


    """
    If this script is called from the command line, save a root file
    """
    
    # grab filenames from arguments:
    filenames = sys.argv[1:]

    # if no arguments are provided, print some usage info
    if len(filenames) < 1:
        print "arguments: [mca files]"
        sys.exit(1)

    # loop over all provided MCA files, call  getMCAhist(), and save root output:
    for filename in filenames:

        basename = os.path.basename(filename) # remove path
        print "--> processing", basename
        basename = os.path.splitext(basename)[0] # remove file extension


        tfile = ROOT.TFile(filename)
        hist = tfile.Get("hist")

        tree = tfile.Get("tree")
        tree.GetEntry(0)
        livetime = tree.livetime
        
        get_rate_vs_threshold(hist, livetime)

