"""
Draw multi-page PDF of energy spectrum from each channel
"""


import os
import sys
import math
from array import array

import ROOT
ROOT.gROOT.SetBatch(True) # comment this out to run interactively

import struck_analysis_parameters
import struck_analysis_cuts

ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       




def process_files(filenames):
    
    # options
    energy_var = "energy1"
    #do_debug = False
    do_debug = True
    plot_name = "individual_channels2.pdf"
    energy_max = 3500
    n_bins = int(energy_max/20)
    #n_bins = 300

    if do_debug:
        plot_name = "test_%s" % plot_name

    tree = ROOT.TChain("tree")
    print "--> adding %i files to chain" % len(filenames)
    for i_file, filename in enumerate(filenames):
        tree.Add(filename)
        if do_debug and i_file > 200: 
            print "==> debugging -- only using %i files" % i_file
            break # debugging


    multiplier = [1.0]*32

    # define recalibration 
    multiplier[1] = 0.5
    multiplier[2] = 0.5
    multiplier[3] = 0.5
    multiplier[4] = 2.0
    multiplier[8] = 0.5
    multiplier[9] = 0.5
    multiplier[10] = 0.5
    multiplier[11] = 0.5
    multiplier[12] = 0.5
    multiplier[13] = 0.5
    multiplier[14] = 0.5
    multiplier[15] = 0.5
    multiplier[16] = 0.5
    multiplier[17] = 0.5
    multiplier[18] = 0.5
    multiplier[19] = 0.5
    multiplier[24] = 0.5
    multiplier[25] = 0.5
    multiplier[26] = 0.5
    multiplier[28] = 0.5
    multiplier[29] = 0.5

    tree.GetEntry(0)
    calibration = array('d',tree.calibration)

    canvas = ROOT.TCanvas()
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()
    canvas.Print("%s[" % plot_name) # open multi-page canvas

    legend = ROOT.TLegend(0.1, 0.85, 0.9, 0.99)
    legend.SetNColumns(8)

    hists = []

    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        #print "channel %i" % channel
        if not value:
            continue
        
        hist = ROOT.TH1D("hist_%i" % channel,"",n_bins,0,energy_max)
        hist.SetXTitle("%s [keV]" % energy_var)
        hist.SetYTitle("Counts / %.1f keV" % hist.GetBinWidth(1))
        hist.GetYaxis().SetTitleOffset(1.2)
        hist.SetLineWidth(3)
        color = struck_analysis_parameters.get_colors()[channel] 
        hist.SetLineColor(color)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.8)

        draw_cmd = "%s*%.4f >> %s" % (energy_var, multiplier[channel], hist.GetName())
        selection = "%s*%.4f>200.0 && channel==%i" % (energy_var, multiplier[channel], channel)
        n_drawn = tree.Draw(draw_cmd, selection)
        #print draw_cmd
        #print selection

        label = struck_analysis_parameters.channel_map[channel]
        #print "channel %i | %s | %i entries drawn" % (channel, label, n_drawn)
        title = "ch %i: %s | %.2e counts | %s | calib: %.4e*%.4e" % (channel, label, n_drawn, selection, calibration[channel], multiplier[channel])
        print title
        hist.SetTitle(title)

        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("%s" % plot_name)

        
        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("%s" % plot_name)

        hist.SetAxisRange(200, 2000)
        canvas.Update()
        canvas.Print("%s" % plot_name)

        hists.append(hist)
        #if channel > 3: break # debugging
        # end loop over channels
        legend.AddEntry(hist, label, "p")

    #tree.Show(0,32)

    # draw all channels on one page
    if len(hists) > 0:
        canvas.SetTopMargin(0.15)
        hists[0].SetTitle("")
        hists[0].Draw()
        y_max = hists[0].GetMaximum()
        for hist in hists:
            if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()
            hist.Draw("same")
        hists[0].SetMaximum(y_max*1.2)
        legend.Draw()

        # print page of all channels 
        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("%s" % plot_name)

        # print all channels with different energy range
        hists[0].SetAxisRange(200, 1800)
        hists[0].SetMaximum(y_max*1.2)
        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("%s" % plot_name)

    # construct a "few channels" draw command, corrected by multiplier
    few_channels_cmd = []
    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        if not value:
            continue
        channel_energy = "%s[%i]*%s" % (energy_var, channel, multiplier[channel])
        print channel_energy
        few_channels_cmd.append("(%s>10.0)*%s" % (channel_energy, channel_energy))
    few_channels_cmd = " + ".join(few_channels_cmd)
    print few_channels_cmd

    hist = ROOT.TH1D("few_ch_hist", "",n_bins,0,energy_max)
    hist.SetXTitle("%s [keV]" % energy_var)
    hist.SetYTitle("Counts / %.1f keV" % hist.GetBinWidth(1))
    hist.GetYaxis().SetTitleOffset(1.2)
    hist.SetLineWidth(3)
    hist.SetLineColor(ROOT.kBlue+1)
    hist.SetMarkerStyle(21)
    hist.SetMarkerSize(0.8)

    n_drawn = tree.Draw("%s >> %s" % (few_channels_cmd, hist.GetName()), "")
    print "%i drawn from few channels" % n_drawn
    hist.SetTitle("%.3e counts" % n_drawn)

    # print few channels plot
    canvas.SetLogy(1)
    canvas.Update()
    canvas.Print("%s" % plot_name)
    y_max = hist.GetBinContent(hist.FindBin(200.0)) # get height at 200 keV
    hist.SetMaximum(y_max*1.2)
    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("%s" % plot_name)

    canvas.Print("%s]" % plot_name) # close multi-page canvas



if __name__ == "__main__":

    process_files(sys.argv[1:])

