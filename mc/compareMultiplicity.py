#!/usr/bin/env python

"""
this script compares struck and MC drift times
"""

import os
import sys
import glob

from ROOT import gROOT
gROOT.SetBatch(True) # comment out to run interactively
from ROOT import TH1D
from ROOT import TH1
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TPaveText
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
    struck_energy_multiplier = struck_analysis_parameters.struck_energy_multiplier
    energy_threshold = 10.0 # for each channel
    charge_energy_low_threshold = 470.0
    #charge_energy_low_threshold = 400.0
    charge_energy_high_threshold = 670.0
    hist_max = 9.5
    hist_min = -0.5
    #n_bins = int((hist_max - hist_min)*1.0)*(len(mc_filenames)+2)
    n_bins = int((hist_max - hist_min)*1.0)
    print hist_min, hist_max, n_bins
    
    selection = "chargeEnergy>%s && chargeEnergy<%s" % (
        charge_energy_low_threshold/struck_energy_multiplier, 
        charge_energy_high_threshold/struck_energy_multiplier
    )
    print "selection:", selection

    mc_selection = "chargeEnergy>%s && chargeEnergy<%s" % (
        charge_energy_low_threshold, 
        charge_energy_high_threshold
    )
    print "mc_selection:", mc_selection


    print "charge_energy_low_threshold:", charge_energy_low_threshold
    print "charge_energy_high_threshold:", charge_energy_high_threshold

    mc_draw_cmd = struck_analysis_cuts.get_multiplicity_cmd(energy_threshold,isMC=True)
    print "mc_draw_cmd:", mc_draw_cmd

    draw_cmd = struck_analysis_cuts.get_multiplicity_cmd(
        energy_threshold/struck_energy_multiplier)
    print "draw_cmd:", draw_cmd


    # construct a basename from the input filename
    basename = os.path.basename(struck_filename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix

    hist_struck = TH1D("hist_struck","", n_bins, hist_min, hist_max)
    hist_struck.Sumw2()
    hist_struck.SetLineColor(TColor.kBlue)
    hist_struck.SetFillColor(TColor.kBlue)
    hist_struck.SetFillStyle(3004)
    hist_struck.SetLineWidth(2)

    # set up hists
    hist_struck.SetXTitle("Number of strips with E > %s keV" % energy_threshold)
        

    text = "events with total energy %s to %s keV" % (
            charge_energy_low_threshold,
            charge_energy_high_threshold,
    )
    pave_text = TPaveText(0.4, 0.8, 0.9, 0.9, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    pave_text.AddText(text)

    n_chargechannels = struck_analysis_parameters.n_chargechannels
    struck_channels = TH1D("struck_channels","", n_chargechannels, 0, n_chargechannels)
    mc_channels = struck_channels.Clone("mc_channels")
    struck_channels.Sumw2()
    struck_channels.SetLineColor(TColor.kBlue)
    struck_channels.SetFillColor(TColor.kBlue)
    struck_channels.SetFillStyle(3004)
    struck_channels.SetLineWidth(2)
    struck_channels.SetXTitle("charge channels hit with > 10 keV")

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

    struck_channel_selection = "energy1_pz>%s && energy1_pz<%s && %s" %(
        charge_energy_low_threshold/struck_energy_multiplier,
        charge_energy_high_threshold/struck_energy_multiplier,
        struck_analysis_cuts.get_channel_selection(),
    )
    print "struck_channel_selection:", struck_channel_selection

    struck_channel_entries = struck_tree.Draw(
        "channel >> %s" % struck_channels.GetName(),
        struck_channel_selection, 
        "goff"
    )
    print "\t%.1e struck channel hist entries" % struck_channel_entries


    mc_channel_selection = "energy1_pz>%s && energy1_pz<%s && %s" %(
        charge_energy_low_threshold,
        charge_energy_high_threshold,
        struck_analysis_cuts.get_channel_selection(isMC=True),
    )
    print "mc_channel_selection:", mc_channel_selection


    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)

    color = struck_analysis_parameters.get_colors()[0]
    color = TColor.kRed

    # make a hists for MC multiplicity, channels
    mc_hist = TH1D("hist", "", n_bins, hist_min, hist_max)
    for hist in [mc_hist, mc_channels]: # format these hists...
        print hist.GetName()
        hist.Sumw2()
        hist.SetLineColor(color)
        hist.SetMarkerStyle(24)
        hist.SetMarkerSize(1.0)
        hist.SetMarkerColor(color)
        hist.SetLineWidth(2)

    # a weird command to map MC channel numbers to integers 0 to 7:
    mc_channel_draw_cmd = "channel-15-26*(channel>40)>>+ %s" % mc_channels.GetName()
    print mc_channel_draw_cmd

    for mc_i, mc_filename in enumerate(mc_filenames):

        print "--> processing", mc_filename
        mc_basename = os.path.basename(mc_filename)
        mc_basename = os.path.splitext(mc_basename)[0]

    
        #print "processing MC file: ", mc_filename
        # open the root file and grab the tree
        mc_file = TFile(mc_filename)
        mc_tree = mc_file.Get("tree")
        try:
            print "\t%.2e events in MC tree, file %i of %i" % (mc_tree.GetEntries(), mc_i, len(mc_filenames))
        except AttributeError:
            print "\t skipping this file..."
            continue

        mc_hist.GetDirectory().cd()
        mc_entries = mc_tree.Draw(
            "%s >>+ %s" % (mc_draw_cmd, mc_hist.GetName()),
            mc_selection,
            "goff"
        )
        print "\t%s: %.2e MC entries drawn" % (mc_basename, mc_entries)
        print "\t%s: %.2e MC hist entries" % (mc_basename, mc_hist.GetEntries())

        mc_entries = mc_tree.Draw(
            mc_channel_draw_cmd,
            mc_channel_selection,
            "goff"
        )
        print "\t%s: %.2e MC channel entries drawn" % (mc_basename, mc_entries)
        print "\t%s: %.2e MC channels hist entries" % (mc_basename, mc_hist.GetEntries())

    mc_hist.Scale(1.0/mc_hist.GetEntries())
    mc_channels.Scale(1.0/mc_channels.GetEntries())
    legend.AddEntry(mc_hist, mc_basename, "lp")

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)

    hist_struck.Scale(1.0/struck_entries)
    struck_channels.Scale(1.0/struck_channels.GetEntries())


    legend.AddEntry(hist_struck, "Struck data", "f")

    hist_struck.SetMaximum(1.0)
    hist_struck.Draw("hist")
    mc_hist.Draw("p same") 
    #mc_hist.Draw("hist")
    #hist_struck.Draw("p same")
    mc_hist.GetEntries()
    pave_text.Draw()
    legend.Draw()
    #hist_struck.Draw("same")
    print "%i struck entries" % hist_struck.GetEntries()

    header =  "n | struck"
    mc_basename = os.path.basename(mc_filenames[0])
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
        result += " | %.3e +/- %.3e" % (
            mc_hist.GetBinContent(i),
            mc_hist.GetBinError(i),
        )
        print result
                


    plot_name = "%s_vs_%s_%i_to_%i_keV_%i_threshold" % (
        basename,
        mc_basename,
        charge_energy_low_threshold,
        charge_energy_high_threshold,
        energy_threshold,
    )

    canvas.SetLogy(1)
    canvas.Update()
    canvas.Print("%s_multiplicity_log.pdf" % plot_name)

    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("%s_multiplicity_lin.pdf" % plot_name)

    if not gROOT.IsBatch():
        canvas.Update()
        raw_input("enter to continue...")

    # use labels for X axis
    xaxis = struck_channels.GetXaxis()
    for channel, value in enumerate(struck_analysis_parameters.charge_channels_to_use):
        if value != 1: continue
        label = struck_analysis_parameters.channel_map[channel]
        i_bin = channel+1
        #print "bin %i: channel %i | %s" % (i_bin, channel, label)
        xaxis.SetBinLabel(i_bin, label)
    struck_channels.SetMaximum(1.0)
    struck_channels.Draw("hist")
    mc_channels.Draw("p same")
    pave_text.Draw()
    legend.Draw()

    canvas.SetLogy(1)
    canvas.Update()
    canvas.Print("%s_channels_log.pdf" % plot_name)

    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("%s_channels_lin.pdf" % plot_name)

    if not gROOT.IsBatch():
        canvas.Update()
        raw_input("enter to continue...")




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
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_5x/all_dcoef200_pcd_size_5x.root",
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_5x/all_dcoef200_pcd_size_5x.root",
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_5x/all_dcoef0_pcd_size_5x.root",
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_2x/all_dcoef200_2x.root",
    ]
    mc_files = glob.glob(
        "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff50/tier3/tier3_*00*.root"
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff70/tier3/tier3_*.root"
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff49/tier3/tier3_*.root"
        #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff51/tier3/tier3_*.root"
    )
    mc_files.sort()

    process_file(
        data_file,
        mc_files, 
    )



