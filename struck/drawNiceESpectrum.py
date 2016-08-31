#!/usr/bin/env python

"""
Draw "nice" plot of energy spectrum -- for Liang, exo week June 2016. 
"""

import os
import sys
import glob

from ROOT import gROOT
gROOT.SetBatch(True) # comment out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle
from ROOT import TChain
from ROOT import TPaveText


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

from struck import struck_analysis_cuts
from struck import struck_analysis_parameters

def get_integral(hist, energy_min, energy_max):

    min_bin = hist.FindBin(energy_min)
    max_bin = hist.FindBin(energy_max)
    integral = hist.Integral(min_bin, max_bin)
    print "integral of %s between %.1f and %.1f keV (bins %i and %i): %.2f" % (
        hist.GetName(),
        energy_min,
        energy_max,
        min_bin,
        max_bin,
        integral,
    )
    return integral

def process_file(
    struck_filename,
    i_channel=None,
    draw_cmd="energy1_pz",
    #draw_cmd = "chargeEnergy",
    do_use_drift_time_cut=True,
    do_use_single_strip_cut=True,
    drift_time_low = struck_analysis_parameters.drift_time_threshold,
    drift_time_high=9.5
):

    print "====> processing Struck data file:", struck_filename
    print "\t i_channel:", i_channel
    print "\t draw_cmd:", draw_cmd
    print "\t do_use_drift_time_cut:", do_use_drift_time_cut
    print "\t do_use_single_strip_cut:", do_use_single_strip_cut

    # options:
    chargeEnergy_cut = "(%s>0)" % draw_cmd

    # drift-time cut info
    #drift_time_low = struck_analysis_parameters.drift_time_threshold 
    #drift_time_low = 8.0 # for investigating electrons from cathode
    print "drift_time_low:", drift_time_low
    
    #drift_time_high = 9.5 # for electrons from cathode
    #drift_time_high = drift_time_low+1.0 # for a slice
    #drift_time_high = 8.0
    #drift_time_high = 11.0 # microseconds
    print "drift_time_low:", drift_time_high

    #struck_draw_cmd = draw_cmd 
    struck_energy_multiplier = struck_analysis_parameters.struck_energy_multiplier
    struck_draw_cmd = "%s*%s" % (draw_cmd, struck_energy_multiplier) # until e-calibration is fixed
    print "\t struck_draw_cmd:", struck_draw_cmd

    sigma_keV = 0.0 # we don't add sigma anymore since RMS noise is added in tier3

    print "\t sigma_keV", sigma_keV

    # construct a basename from the input filename
    basename = os.path.basename(struck_filename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix
    print "\t basename:", basename 


    plot_name = "%s_spectrum_sigma_%i_keV" % (
        basename, 
        sigma_keV,
    )
    if do_use_drift_time_cut:
        plot_name += "_%ins_to_%ins" % (
            drift_time_low*1e3,
            drift_time_high*1e3,
        )
    if do_use_single_strip_cut:
        plot_name += "_SS"
    if "energy1_pz" in draw_cmd:
        plot_name += "_E1PZ"
        if i_channel != None:
            plot_name += "_ch%i_singleMcCh" % i_channel
    print "\t plot_name:", plot_name

    # setup struck hist & formatting
    max_bin = 2000
    n_bins = int(max_bin*1.0/10.0)
    hist_struck = TH1D("hist_struck","",n_bins,0,max_bin)
    hist_struck.SetLineColor(TColor.kBlue)
    hist_struck.SetFillColor(TColor.kBlue)
    hist_struck.SetFillStyle(3004)
    hist_struck.SetLineWidth(2)
    hist_struck.GetYaxis().SetTitleOffset(1.5)

    # struck TTree:Draw() selection string
    struck_selection = [chargeEnergy_cut]
    if do_use_drift_time_cut:
        if "energy1_pz" in draw_cmd:
            struck_selection.append(
                "rise_time_stop95-trigger_time>=%s && rise_time_stop95-trigger_time<=%s" % (
                    drift_time_low,
                    drift_time_high))
        else:
            struck_selection.append(struck_analysis_cuts.get_drift_time_cut(
                energy_threshold=200.0/struck_energy_multiplier,
                drift_time_low=drift_time_low,
                drift_time_high=drift_time_high,
            ))
    if do_use_single_strip_cut:
        part = struck_analysis_cuts.get_single_strip_cut(
            energy_threshold=10.0/struck_energy_multiplier)
        struck_selection.append(part)
    if "energy1_pz" in draw_cmd:
        if i_channel != None:
            struck_selection.append("channel==%i" % i_channel)
        else:
            struck_selection.append(struck_analysis_cuts.get_channel_selection())
    struck_selection = "&&".join(struck_selection)
    print "struck_selection:"
    print "\t", "\n\t || ".join(struck_selection.split("||"))


    # open the struck file and get its entries
    print "processing file: ", struck_filename
    struck_file = TFile(struck_filename)
    struck_tree = struck_file.Get("tree")
    hist_struck.GetDirectory().cd()
    struck_entries = struck_tree.Draw(
        "%s >> %s" % (struck_draw_cmd, hist_struck.GetName()), 
        struck_selection,
        "goff"
    )
    print "\t%.1e struck entries drawn" % struck_entries


    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLeftMargin(0.13)
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    # scale MC to match struck data, many different methods... 

    peak_energy = 570
    peak_energy = 400
    y_max = hist_struck.GetMaximum()
    print "y_max before axis range:", y_max
    hist_struck.SetAxisRange(400,max_bin)
    y_max = hist_struck.GetMaximum()
    hist_struck.SetAxisRange(0,max_bin)
    print "y_max after axis range:", y_max
    # struck_height used for scaling (sometimes) and also for plotting
    struck_height = hist_struck.GetBinContent(hist_struck.FindBin(peak_energy))

    #scale_factor *= 0.5 # extra offset for viewing

    hist_struck.SetXTitle("Energy [keV]")
    hist_struck.GetXaxis().SetTitleOffset(1.2)
    hist_struck.SetYTitle("Counts  / %i keV" % (
        hist_struck.GetBinWidth(1),
    ))

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.AddEntry(hist_struck, "Struck data (%.1e cts)" % hist_struck.GetEntries(), "f")

    hist_struck.Draw()
    #hist_struck.Draw("same")
    print "%i entries in hist_struck" % hist_struck.GetEntries()

    pave_text = TPaveText(0.65, 0.8, 0.9, 0.9, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    if do_use_drift_time_cut:
        pave_text.AddText("drift time: %.2f to %.2f #mus\n" % (
            drift_time_low, drift_time_high,))
    #pave_text.Draw()

    # print log scale
    #legend.Draw()
    canvas.Update()
    #canvas.Print("%s.pdf" % plot_name)

    # print a linear scale version
    canvas.SetLogy(0)
    hist_max = hist_struck.GetMaximum()
    #hist_struck.SetMaximum(struck_height*1.2)
    hist_struck.SetMaximum(y_max*1.2)
    canvas.Update()
    canvas.Print("%s_lin.pdf" % plot_name)

    if not gROOT.IsBatch():
        canvas.SetLogy(1)
        hist_struck.SetMaximum(hist_max*2.0)
        canvas.Update()
        raw_input("pause...")



if __name__ == "__main__":

    # 7th LXe
    data_file = "/u/xo/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/overnight7thLXe.root" 

    process_file(data_file, draw_cmd="chargeEnergy", do_use_single_strip_cut=False, drift_time_high=9.5)
    process_file(data_file, draw_cmd="chargeEnergy", do_use_single_strip_cut=False, drift_time_low=8.0, drift_time_high=9.5)
    process_file(data_file, draw_cmd="chargeEnergy", do_use_single_strip_cut=False, drift_time_low=8.0, drift_time_high=9.0)
    process_file(data_file, draw_cmd="chargeEnergy", do_use_single_strip_cut=False, drift_time_low=8.5, drift_time_high=9.0)
    process_file(data_file, draw_cmd="chargeEnergy", do_use_single_strip_cut=False, drift_time_low=7.0, drift_time_high=8.0)
    process_file(data_file, draw_cmd="chargeEnergy", do_use_single_strip_cut=False, drift_time_high=8.0)
    #process_file(data_file, draw_cmd="chargeEnergy")
    #process_file(data_file, draw_cmd="chargeEnergy", do_use_single_strip_cut=False, do_use_drift_time_cut=False)
    #process_file(data_file, i_channel=None)
    #process_file(data_file, i_channel=None, do_use_single_strip_cut=False)
    #for i_channel in xrange(8): process_file( data_file, i_channel=i_channel, do_use_single_strip_cut=True,)

