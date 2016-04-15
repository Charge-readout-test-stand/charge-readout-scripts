#!/usr/bin/env python

"""
this script compares struck and MC drift times
"""

import os
import sys

from ROOT import gROOT
#gROOT.SetBatch(True) # comment out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle

from struck import struck_analysis_parameters
from struck import struck_analysis_cuts


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(
    struck_filename,
    mc_filenames, 
):


    # options:
    energy_threshold = 10.0 # for each channel
    charge_energy_low_threshold = 400.0
    charge_energy_high_threshold = 1500.0
    hist_max = 9.5
    hist_min = -0.5
    #n_bins = int((hist_max - hist_min)*1.0)*(len(mc_filenames)+2)
    n_bins = int((hist_max - hist_min)*1.0)
    print hist_min, hist_max, n_bins
    
    selection = "chargeEnergy>%s && chargeEnergy<%s" % (charge_energy_low_threshold, charge_energy_high_threshold)

    print "charge_energy_low_threshold:", charge_energy_low_threshold
    print "charge_energy_high_threshold:", charge_energy_high_threshold


    mc_draw_cmd = []
    mc_channels = struck_analysis_parameters.MCcharge_channels_to_use
    for (channel, value)  in enumerate(mc_channels):
        if mc_channels[channel]:
            print "MC channel %i" % channel
            mc_draw_cmd.append("(energy1_pz[%i]>%.2f)" % (channel, energy_threshold))

    mc_draw_cmd = " + ".join(mc_draw_cmd)
    print mc_draw_cmd


    draw_cmd = struck_analysis_cuts.get_multiplicity_cmd(energy_threshold)
    print draw_cmd



    # construct a basename from the input filename
    basename = os.path.basename(struck_filename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix

    hist_struck = TH1D("hist_struck","", n_bins, hist_min, hist_max)
    hist_struck.Sumw2()
    hist_struck.SetLineColor(TColor.kBlue)
    hist_struck.SetFillColor(TColor.kBlue)
    hist_struck.SetFillStyle(3004)
    hist_struck.SetLineWidth(2)

    # open the struck file and get its entries
    print "processing Struck file: ", struck_filename
    struck_file = TFile(struck_filename)
    struck_tree = struck_file.Get("tree")
    n_entries = struck_tree.GetEntries()
    print "\t%.1e struck tree entries" % n_entries
    hist_struck.GetDirectory().cd()
    struck_entries = struck_tree.Draw(
        "%s >> %s" % (draw_cmd, hist_struck.GetName()),
        selection,
        "goff"
    )
    print "\t%.1e struck hist entries" % struck_entries

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)

    mc_hists = []
    for mc_i, mc_filename in enumerate(mc_filenames):

        print "--> processing", mc_filename
        mc_basename = os.path.basename(mc_filename)
        mc_basename = os.path.splitext(mc_basename)[0]

        # make a histogram to hold energies
        hist = TH1D("hist", "", n_bins, hist_min, hist_max)
        hist.Sumw2()
        color = struck_analysis_parameters.get_colors()[mc_i]
        hist.SetLineColor(color)
        #hist.SetFillColor(color)
        #hist.SetFillStyle(3004)
        hist.SetMarkerStyle(24+mc_i)
        hist.SetMarkerSize(1.0)
        hist.SetMarkerColor(color)
        hist.SetLineWidth(2)


        print "processing MC file: ", mc_filename
        # open the root file and grab the tree
        mc_file = TFile(mc_filename)
        mc_tree = mc_file.Get("tree")
        print "\t%.2e events in MC tree" % mc_tree.GetEntries()

        hist.GetDirectory().cd()
        offset = (mc_i+1.0)/(len(mc_filenames)+2)
        print "offset:", offset
        offset = 0.0
        mc_entries = mc_tree.Draw(
            "%s + %s >> %s" % (mc_draw_cmd, offset, hist.GetName()),
            selection,
            "goff"
        )
        print "\t%s: %.1e MC hist entries" % (mc_basename, mc_entries)
        hist.Scale(1.0/mc_entries)
        legend.AddEntry(hist, mc_basename, "lp")
        mc_hists.append(hist)

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)

    hist_struck.Scale(1.0/struck_entries)

    hist_struck.SetXTitle("Number of strips with E > %s keV" % energy_threshold)

    legend.AddEntry(hist_struck, "Struck data", "fl")

    hist_struck.SetMaximum(1.0)
    hist_struck.Draw("hist")
    for hist in mc_hists:
        hist.Draw("p same") 
        print "%i mc entries" % hist.GetEntries()
    legend.Draw()
    #hist_struck.Draw("same")
    print "%i struck entries" % hist_struck.GetEntries()

    header =  "n | struck"
    for mc_filename in mc_filenames:
        mc_basename = os.path.basename(mc_filename)
        mc_basename = os.path.splitext(mc_basename)[0]
        header += " | %s" % mc_basename  
    print header
    for i_bin in xrange(hist_struck.GetNbinsX()):
        i = i_bin+1
        #print hist_struck.GetBinCenter(i)
        result = "%i" % i_bin
        result += " | %.3e +/- %.3e" % (
            hist_struck.GetBinContent(i),
            hist_struck.GetBinError(i),
        )
        for hist in mc_hists:
            result += " | %.3e +/- %.3e" % (
                hist.GetBinContent(i),
                hist.GetBinError(i),
            )
        print result
                


    plot_name = "%s_multiplicity%i_to_%i_keV_%i_threshold" % (
        basename,
        charge_energy_low_threshold,
        charge_energy_high_threshold,
        energy_threshold,
    )

    canvas.Update()
    canvas.Print("%s_lin.pdf" % plot_name)

    canvas.SetLogy(1)
    canvas.Update()
    canvas.Print("%s_log.pdf" % plot_name)

    if not gROOT.IsBatch():
        canvas.Update()
        raw_input("pause...")

if __name__ == "__main__":

    #if len(sys.argv) < 2:
    #    print "arguments: [sis root files]"
    #    sys.exit(1)

    # loop over all provided arguments
    #process_file(sys.argv[1], sys.argv[2])


    #data_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root"
    #mc_file = "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207_Full_Ralph/Tier3/all_tier3_Bi207_Full_Ralph.root"
    #mc_file = "207biMc.root"

    # 7th LXe
    data_file = "/u/xo/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/overnight7thLXe.root" 
    mc_files = [
        "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_5x/all_dcoef200_pcd_size_5x.root",
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_5x/all_dcoef200_pcd_size_5x.root",
        "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_5x/all_dcoef0_pcd_size_5x.root",
        "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_2x/all_dcoef200_2x.root",
    ]

    process_file(
        data_file,
        mc_files, 
    )



