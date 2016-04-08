"""
Draw multiplicity plot
"""


import os
import sys

from ROOT import gROOT
gROOT.SetBatch(True)
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
    n_pcds_hists = []

    colors = [
        TColor.kRed,
        TColor.kOrange+1,
        TColor.kGreen+2,
        TColor.kBlue,
        TColor.kCyan+1,
        TColor.kViolet,
    ]
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend2 = TLegend(0.1, 0.91, 0.9, 0.99)
    legend2.SetNColumns(2)
    Wvalue = 20.138 # eV / e-


    for filename in filenames:
        
        # options:
        energy_threshold = 5 # keV
        max_n = 10 # max multiplicity expected

        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]

        hist = TH1D("hist%i" % len(hists), basename,max_n+1, -0.5, max_n+0.5)
        #hist = TH1D("hist%i" % len(hists), basename,100, -0.5, 100.5)
        print "hist:", hist.GetName()
        color = colors[len(hists)]
        hist.SetLineColor(color)
        hist.SetLineWidth(2)
        hist.SetLineStyle(len(hists)+1)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(1.5)
        hist.SetXTitle("Multiplicity [channels above %s keV]" % energy_threshold)
        hists.append(hist)

        n_pcds_hist = TH1D("n_pcd_hist%i" % len(n_pcds_hists), basename, 100, 0, 2000)
        n_pcds_hist.SetLineColor(color)
        n_pcds_hist.SetLineWidth(2)
        n_pcds_hist.SetMarkerColor(color)
        n_pcds_hist.SetMarkerStyle(21)
        n_pcds_hist.SetMarkerSize(1.5)
        n_pcds_hist.SetXTitle("N PCDs")
        n_pcds_hists.append(n_pcds_hist)

    for (i, filename) in enumerate(filenames):

        print "processing file: ", filename
        # open the root file and grab the tree
        root_file = TFile(filename)
        tree = root_file.Get("evtTree")
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
        hist = hists[i]
        n_pcds_hist = n_pcds_hists[i]
        hist.GetDirectory().cd()


        threshold = 100
        selection = "NumPCDs>0&&Energy>0"
        title = selection

        draw_cmd = "Sum$(ChannelWaveform[][799]*%s/1e3>%s)" % (Wvalue, energy_threshold)


        draw_cmd += " >> %s" % hist.GetName()
        print "draw_cmd:", draw_cmd
        print "selection", selection

        options = "goff"

        n_entries = tree.Draw(
            draw_cmd,
            selection,
            options,
        )
        tree.Draw("NumPCDs >> %s" % n_pcds_hist.GetName(), "NumPCDs>0", "goff")
        legend2.AddEntry(n_pcds_hist, n_pcds_hist.GetTitle() + " mean=%.1f" % n_pcds_hist.GetMean(), "p")

        print "%i drawn entries" % n_entries
        n_entries = hist.GetEntries()
        print "%i hist entries" % n_entries
        #hist.Scale(1.0/n_entries)
        print "mean", hist.GetMean()

        legend.AddEntry(hist, hist.GetTitle() + " mean=%.4f" % hist.GetMean(), "p")


    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    hists[0].SetMinimum(0.5)
    hists[0].SetTitle("")
    hists[0].Draw()
    for hist in hists[1:]:
        hist.Draw("same")

    legend.Draw()
    canvas.Update()
    canvas.Print("multiplicity.pdf")
    raw_input("any key to continue  ")

    n_pcds_hists[0].SetMaximum(n_pcds_hists[0].GetEntries())
    n_pcds_hists[0].SetMinimum(0.5)
    n_pcds_hists[0].SetTitle("")
    n_pcds_hists[0].Draw()
    for hist in n_pcds_hists[1:]:
        hist.Draw("same")
    legend2.Draw()
    canvas.Update()
    canvas.Print("nPCDs.pdf")
    raw_input("any key to continue  ")




if __name__ == "__main__":


    filenames = [
    #"/nfs/slac/g/exo_data4/users/alexis4/bucket/slac/test-stand/mcTests/dcoef0.root",
    "/nfs/slac/g/exo_data4/users/alexis4/bucket/slac/test-stand/mcTests/dcoef200.root",
    "/nfs/slac/g/exo_data4/users/alexis4/bucket/slac/test-stand/mcTests/dcoef200_2x_pcd.root",
    "/nfs/slac/g/exo_data4/users/alexis4/bucket/slac/test-stand/mcTests/dcoef200_4x_pcd.root",
    "/nfs/slac/g/exo_data4/users/alexis4/bucket/slac/test-stand/mcTests/dcoef200_5x_pcd.root",
    "/nfs/slac/g/exo_data4/users/alexis4/bucket/slac/test-stand/mcTests/dcoef200_6x_pcd.root",
    "/nfs/slac/g/exo_data4/users/alexis4/bucket/slac/test-stand/mcTests/dcoef200_8x_pcd.root",
    ]

    process_files(filenames)



