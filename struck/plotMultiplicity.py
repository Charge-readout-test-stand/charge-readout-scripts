"""
Draw multiplicity plot
"""


import os
import sys

import ROOT
from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TLegend
from ROOT import gStyle


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

import struck_analysis_cuts
import struck_analysis_parameters

def process_files(filenames):

    hists = []
    ch_hists = []

    colors = [
        ROOT.kBlue,
        ROOT.kRed,
        ROOT.kGreen+2,
        ROOT.kViolet,
    ]
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    threshold = 10

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    for (i, filename) in enumerate(filenames):
        
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        print "processing file: ", filename

        hist = TH1D("hist%i" % len(hists), basename,64, -0.25, 31.75)
        print "hist:", hist.GetName()
        color = colors[len(hists)]
        hist.SetLineColor(color)
        hist.SetFillColor(color)
        #hist.SetLineWidth(2)
        hist.SetLineStyle(len(hists)+1)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(1.5)
        hist.SetXTitle("Multiplicity [channels above %.1f keV]" % threshold)
        hists.append(hist)

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

        multiplier = 1.0
        if is_MC:
            multiplier = 1.15

        # draw channels hit:    
        ch_hist = TH1D("ch_hist%i" % len(hists), basename,64, -0.25, 31.75)
        ch_hist.SetLineColor(color)
        #ch_hist.SetLineWidth(2)
        ch_hist.SetFillColor(color)
        ch_hist.SetXTitle("Channel hit [above %.1f keV]" % threshold)
        selection = "energy1_pz>%s" % (threshold/multiplier)
        n_drawn = tree.Draw("channel >> %s" % ch_hist.GetName(), selection)
        ch_hist.Scale(1.0/n_entries)

        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("hitChannels.pdf")
        ch_hists.append(ch_hist)

        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("hitChannels_lin.pdf")

        raw_input("any key to continue  ")



        #selection = "chargeEnergy*%s>1000 & chargeEnergy*%s<1200" % (multiplier, multiplier)
        #selection = ""
        selection = "%s > 200" % struck_analysis_cuts.get_few_channels_cmd_baseline_rms()
        draw_cmd = struck_analysis_cuts.get_multiplicity_cmd(energy_threshold=threshold/multiplier, isMC=is_MC)
        draw_cmd = "%s >> %s" % (draw_cmd, hist.GetName())

        title = selection[:100] + "..."
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


    hists[0].SetTitle("")
    hists[0].Draw()
    for hist in hists:
        hist.Draw("same")

    canvas.SetLogy(1)
    legend.Draw()
    canvas.Update()
    canvas.Print("multiplicity.pdf")

    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("multiplicity_lin.pdf")
    raw_input("any key to continue  ")


if __name__ == "__main__":


    # data and MC after 6th LXe
    #filenames = [
    #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root",
    #"/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/gamma_1MeV_Ralph/Tier3/all_tier3_gamma_1MeV_Ralph_dcoef0.root",
    #"/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization_NEW/Bi207_Full_Ralph/combined/all_tier3_Bi207_Full_Ralph_dcoef0.root",
    #"/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/electron_1MeV_Ralph/Tier3/all_tier3_electron_1MeV_Ralph_dcoef0.root",
    #]

    # 8th LXe
    filenames = [
        #"~/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v2.root", # ubuntu DAQ
        #"~/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v3.root", # ubuntu DAQ
        "/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v3.root ", # LLNL
    ]

    process_files(filenames)



