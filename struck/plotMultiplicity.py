"""
Draw multiplicity plot
"""


import os
import sys

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
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

        hist = TH1D("hist%i" % len(hists), basename,7, -0.5, 6.5)
        print "hist:", hist.GetName()
        color = colors[len(hists)]
        hist.SetLineColor(color)
        hist.SetLineWidth(2)
        hist.SetLineStyle(len(hists)+1)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(1.5)
        hist.SetXTitle("Multiplicity [channels above 100 keV]")
        hists.append(hist)



    for (i, filename) in enumerate(filenames):

        print "processing file: ", filename
        # open the root file and grab the tree
        root_file = TFile(filename)
        tree = root_file.Get("tree")
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
        hist = hists[i]
        hist.GetDirectory().cd()

        is_MC = True
        try:
            tree.GetEntry(0)
            tree.MCchargeEnergy
        except:
            is_MC = False
        print "is_MC:", is_MC

        threshold = 100
        selection = "chargeEnergy>1000 & chargeEnergy<1200"
        title = selection

        draw_cmd = [
            "(energy1_pz[0]>%.1f)" % threshold,
            "(energy1_pz[1]>%.1f)" % threshold,
            "(energy1_pz[2]>%.1f)" % threshold,
            "(energy1_pz[3]>%.1f)" % threshold,
            "(energy1_pz[4]>%.1f)" % threshold,
        ]

        if is_MC:
            # MC uses different channels and different energy calibration than
            # data

            multiplier = 1.15 # fix MC energy calibration
            threshold /= multiplier
            selection = "chargeEnergy*%s>1000 & chargeEnergy*%s<1200" % (
                multiplier,
                multiplier,
            )
            draw_cmd = [
                "(energy1_pz[25]>%.1f)" % threshold,
                "(energy1_pz[26]>%.1f)" % threshold,
                "(energy1_pz[28]>%.1f)" % threshold,
                "(energy1_pz[52]>%.1f)" % threshold,
                "(energy1_pz[53]>%.1f)" % threshold,
            ]


        draw_cmd = " + ".join(draw_cmd) + " >> %s" % hist.GetName()
        print "draw_cmd:", draw_cmd
        print "selection", selection

        options = "goff"

        n_entries = tree.Draw(
            draw_cmd,
            selection,
            options,
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
    canvas.Print("multiplicity.pdf")
    raw_input("any key to continue  ")


if __name__ == "__main__":


    # data and MC after 6th LXe
    filenames = [
    "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root",
    "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/gamma_1MeV_Ralph/Tier3/all_tier3_gamma_1MeV_Ralph_dcoef0.root",
    "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization_NEW/Bi207_Full_Ralph/combined/all_tier3_Bi207_Full_Ralph_dcoef0.root",
    "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/electron_1MeV_Ralph/Tier3/all_tier3_electron_1MeV_Ralph_dcoef0.root",
    ]

    process_files(filenames)



