#!/usr/bin/env python

"""
This script draws a spectrum from a root tree of MC data. 

arguments [MC root files]
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

# some style settings for ROOT
gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(filename):

    print "processing file: ", filename

    # construct a basename from the input file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    nEXOevents = root_file.Get("nEXOevents")


    n_bins = 200
    max_bin = 2000

    smearing = "1.18*sqrt(TotalEventEnergy*1e3)*sin(2*pi*rndm)*sqrt(-2*log(rndm))"
    z_corrected_energy = "Sum$(EnergyDeposit*1e3*(8.5-Zpos)/17)"
    selection = "TotalEventEnergy>0"

    # draw unsmeared MC energy:
    hist0 = TH1D("hist0", "", n_bins, 0, max_bin)
    hist0.SetLineWidth(2)
    hist0.SetLineColor(TColor.kBlack)
    nEXOevents.Draw("TotalEventEnergy*1e3 >> hist0", selection, "goff")

    # draw smeared MC energy:
    hist1 = TH1D("hist1", "", n_bins, 0, max_bin)
    hist1.SetLineWidth(2)
    hist1.SetLineColor(TColor.kBlue)
    nEXOevents.Draw("TotalEventEnergy*1e3 + %s>> hist1" % smearing, selection, "goff")

    # draw z-corrected MC energy:
    hist2 = TH1D("hist2", "", n_bins, 0, max_bin)
    hist2.SetLineWidth(2)
    hist2.SetLineColor(TColor.kRed)
    nEXOevents.Draw("%s >> hist2" % z_corrected_energy, selection, "goff")

    # draw smeared & z corrected MC energy:
    hist3 = TH1D("hist3", "", n_bins, 0, max_bin)
    hist3.SetLineWidth(2)
    hist3.SetLineColor(TColor.kGreen+2)
    nEXOevents.Draw("%s + %s >> hist3" % (z_corrected_energy, smearing), selection, "goff")



    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,0)
    hist0.SetXTitle("Energy [keV]")
    hist0.SetYTitle("Counts / %i keV" % (max_bin/n_bins))

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.AddEntry(hist0, "raw MC", "l")
    legend.AddEntry(hist1, "smeared", "l")
    legend.AddEntry(hist2, "z-corrected", "l")
    legend.AddEntry(hist3, "smeared + z-corrected", "l")
    legend.SetNColumns(4)

    hist0.Draw() # raw MC
    hist1.Draw("same") # smeared MC
    hist2.Draw("same") # z-corrected
    hist3.Draw("same") # smeared & z-corrected
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_spectrum.png" % basename)
    hist0.SetAxisRange(500, 1500)
    canvas.Update()
    canvas.Print("%s_spectrum_zoom.png" % basename)
    hist0.SetAxisRange(0, max_bin) # unzoom 


    # set up some colors & fill patterns for individual plots
    hist0.SetFillColor(TColor.kBlack)
    hist0.SetFillStyle(3004)
    hist1.SetFillColor(TColor.kBlue)
    hist1.SetFillStyle(3005)
    hist2.SetFillColor(TColor.kRed)
    hist2.SetFillStyle(3005)
    hist3.SetFillColor(TColor.kGreen+2)
    hist3.SetFillStyle(3005)

    # draw raw & smeared
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.AddEntry(hist0, "raw MC", "l")
    legend.AddEntry(hist1, "smeared", "l")
    legend.SetNColumns(2)
    hist0.Draw() # raw MC
    hist1.Draw("same") # smear
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_smear_spectrum.png" % basename)
    hist0.SetAxisRange(400, 1400)
    canvas.Update()
    canvas.Print("%s_smear_spectrum_zoom.png" % basename)
    hist0.SetAxisRange(0, max_bin) # unzoom 

    # draw raw & z-corrected
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.AddEntry(hist0, "raw MC", "l")
    legend.AddEntry(hist2, "z-corrected", "l")
    legend.SetNColumns(4)
    hist0.Draw() # raw MC
    hist2.Draw("same") # z-corrected
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_zcorr_spectrum.png" % basename)
    hist0.SetAxisRange(400, 1400)
    canvas.Update()
    canvas.Print("%s_zcorr_spectrum_zoom.png" % basename)
    hist0.SetAxisRange(0, max_bin) # unzoom 

    # draw raw & smeared + z-corected
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.AddEntry(hist0, "raw MC", "l")
    legend.AddEntry(hist3, "smeared and z-corrected", "l")
    legend.SetNColumns(2)
    hist0.Draw() # raw MC
    hist3.Draw("same") # smear & z-corrected
    legend.Draw()
    canvas.Update()
    canvas.Print("%s_smear_plus_zcorr__spectrum.png" % basename)
    hist0.SetAxisRange(400, 1400)
    canvas.Update()
    canvas.Print("%s_smear_plus_zcorr_spectrum_zoom.png" % basename)
    hist0.SetAxisRange(0, max_bin) # unzoom 




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [MC root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



