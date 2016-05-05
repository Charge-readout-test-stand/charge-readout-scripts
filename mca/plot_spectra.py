#!/bin/env python

from ROOT import gROOT
#gROOT.SetBatch(True)
import ROOT
import sys
import os.path

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)




if __name__ == "__main__":


    """
    If this script is called from the command line, save a root file
    """
    
    # grab filenames from arguments:
    filenames = sys.argv[1:]
    filenames.sort()

    # if no arguments are provided, print some usage info
    if len(filenames) < 1:
        print "arguments: [mca files]"
        sys.exit(1)

    tfiles = []
    hists = []

    colors = [
        ROOT.TColor.kBlack,
        ROOT.TColor.kBlue,
        ROOT.TColor.kRed,
        ROOT.TColor.kGreen+2,
        ROOT.TColor.kViolet+1,
        ROOT.TColor.kOrange+1,
        ROOT.TColor.kTeal+1, 
        ROOT.TColor.kMagenta, 
        ROOT.TColor.kGray+1, 
    ]

    canvas = ROOT.TCanvas("canvas","",850,1100)
    canvas.SetGrid(1,1)
    canvas.SetLogy(1)
    canvas.SetTopMargin(0.15)
    legend = ROOT.TLegend(0.1, 0.85, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)

    # loop over all provided MCA files, call  getMCAhist(), and save root output:
    for (i, filename) in enumerate(filenames):

        basename = os.path.basename(filename) # remove path
        print "--> processing", basename
        basename = os.path.splitext(basename)[0] # remove file extension


        tfile = ROOT.TFile(filename)
        tfiles.append(tfile)

        hist = tfile.Get("hist")
        hists.append(hist)

        tree = tfile.Get("tree")
        tree.GetEntry(0)
        livetime = tree.livetime

        hist.SetLineColor(colors[i % len(colors)])
        if i >= len(colors):
            hist.SetLineStyle(2)
        hist.SetLineWidth(2)
        hist.SetFillStyle(0)
        hist.GetYaxis().SetTitleOffset(1.2)

        legend.AddEntry(hist, "%s (%.1f hrs)" % (basename, livetime/60.0/60.0) , "l")

        # print some info
        print hist.GetTitle()
        hist.SetTitle("")
        #print "\t %i entries in hist" % hist.GetEntries()
        print "\t livetime: %.2f hours" % (livetime/3600.0)
        total_integral = hist.Integral()
        print "\t total counts in hist: %i" % total_integral
        print "\t total counts / second: %.2f" % (total_integral/livetime)
        
        # scale hist by 1 / livetime
        hist.Scale(1.0/livetime)

        hist.Rebin(16)


        if i == 0:
            hist.SetMaximum(1.0)
            hist.SetAxisRange(0, 3000)
            hist.SetXTitle("ADC units")
            hist.SetYTitle("Counts / second / %i ADC units" % hist.GetBinWidth(0))
            hist.Draw()
        else:
            hist.Draw("same")


    legend.Draw()
    canvas.Update()
    #canvas.Print("mca_comparison.png")
    canvas.Print("mca_comparison.pdf")
    val = raw_input("press any key to continue ")


