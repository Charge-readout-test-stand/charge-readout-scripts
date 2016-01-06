"""
Draw multiple MC energy spectra, after digitization and tier3 conversion



"""


import os
import sys
import glob

from ROOT import gROOT
#gROOT.SetBatch(True)
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


def process_files(filenames):

    hists = []

    colors = [
        TColor.kBlue,
        TColor.kRed,
        TColor.kGreen+2,
        TColor.kViolet,
    ]
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)

    for filename in filenames:
        
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]

        hist = TH1D("hist%i" % len(hists), basename,500, 0, 2500)
        color = colors[len(hists)]
        hist.SetLineColor(color)
        hist.SetLineWidth(2)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(1.5)
        #hist.SetFillColor(color)
        #hist.SetFillStyle(3004)
        hists.append(hist)
        hist.SetXTitle("Energy [keV]")
        hist.SetYTitle("Counts / %.1f keV" % hist.GetBinWidth(1))


    for (i, filename) in enumerate(filenames):

        print "processing file: ", filename
        # open the root file and grab the tree
        root_file = TFile(filename)
        tree = root_file.Get("tree")
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
        hist = hists[i]
        hist.GetDirectory().cd()

        #draw_cmd = "chargeEnergy*1.15 >> %s" % hist.GetName()
        #selection = "chargeEnergy>0"
        draw_cmd = "MCchargeEnergy >> %s" % hist.GetName()
        selection = "MCchargeEnergy>0"
        print "draw_cmd:", draw_cmd
        n_entries = tree.Draw(
            draw_cmd,
            selection,
            "goff",
        )
        print "%i drawn entries" % n_entries
        n_entries = hist.GetEntries()
        print "%i hist entries" % n_entries
        hist.Scale(1.0/n_entries)
        print "mean", hist.GetMean()

        legend.AddEntry(hist, hist.GetTitle(), "p")


    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    hists[0].SetTitle("")
    hists[0].Draw()
    for hist in hists:
        hist.Draw("same")

    legend.Draw()
    canvas.Update()
    canvas.Print("mc_energy_comparison.pdf")
    raw_input("any key to continue  ")



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [tier3 root files]"
        sys.exit(1)


    process_files(sys.argv[1:])




