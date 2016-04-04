#!/usr/bin/env python

"""

This script draws distributions of tier3 data. For a variable of interest, the
sum spectrum (if chosen ) and individual channels are drawn. The variable of
interest is chosen by editing the options. Possible variables:

* energy in keV
* RMS noise
* energy in ADC units
* drift times

arguments [sis tier 3 root files of events]
"""

import os
import sys
import math

from ROOT import gROOT
gROOT.SetBatch(True) # comment this out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle
from ROOT import TLine

import struck_analysis_parameters

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       



def setup_hist(hist, color, xtitle, xUnits):
    """ Set color, line and marker style of hist """
    hist.SetLineColor(color)
    hist.SetMarkerStyle(8)
    hist.SetMarkerSize(1.5)
    hist.SetMarkerColor(color)
    hist.SetLineWidth(2)
    hist.SetXTitle("%s [%s]" % (xtitle, xUnits))
    hist.SetYTitle("Counts / %s %s" % (hist.GetBinWidth(1), xUnits,))
    #hist.SetFillColor(color)


def process_file(filename):

    print "processing file: ", filename

    #-------------------------------------------------------------------------------
    # options

    # choose one:
    do_draw_energy = 0
    do_draw_drift_times = 0
    do_draw_rms = 0
    do_draw_rms_keV = 1
    do_draw_rms_mV = 0
    do_draw_ADC_units = 0
    do_draw_mV = 0

    #do_draw_sum = False # sum energy
    do_draw_sum = True # sum energy

    # default values:
    xUnits = ""
    prefix = "plots"
    selections = []
    #selections.append("Entry$<50") # debugging

    if do_draw_energy:
        print "---> drawing energies... "
        draw_command = "energy1_pz"
        min_bin = 0
        max_bin = 2000
        bin_width = 10
        bin_width = 15

        xUnits = "keV"
        xtitle = "Energy"
        prefix = "energy_"
        
    elif do_draw_drift_times:
        print "---> drawing drift times"
        draw_command = "rise_time_stop99 - trigger_time"
        #min_bin = -10.02
        #max_bin = 30.02
        min_bin = -5.02
        max_bin = 25.02
        bin_width = 0.04
        xUnits = "#mus"
        xtitle = "Drift time"
        selections.append("energy1_pz>300")

    elif do_draw_rms_keV:
        print "---> drawing RMS noise [keV]"
        draw_command = "baseline_rms*calibration"
        min_bin = 0
        max_bin = 100
        bin_width = 0.5
        xUnits = "keV"
        xtitle = "RMS noise"
        prefix = "keV_"
        do_draw_sum = False

    elif do_draw_rms:
        print "---> drawing RMS noise"
        draw_command = "baseline_rms"
        min_bin = 0
        max_bin = 100
        bin_width = 0.5
        xUnits = "ADC units"
        xtitle = "RMS noise"
        do_draw_sum = False

    elif do_draw_rms_mV:
        print "---> drawing RMS noise [mV]"
        draw_command = "baseline_rms*2.5*1e3/16384"
        min_bin = 0
        max_bin = 6
        bin_width = 0.01
        xUnits = "mV"
        xtitle = "RMS noise"
        prefix = "mV_"
        do_draw_sum = False


    elif do_draw_ADC_units:
        print "---> drawing adc energies... "
        draw_command = "energy1_pz/calibration"
        min_bin = 0
        max_bin = 1000
        bin_width = 5
        do_draw_sum = False

        xUnits = "ADC units"
        xtitle = "Energy"
        prefix = "adc_energy_"

    elif do_draw_mV:
        print "---> drawing mV..."
        draw_command = "energy1_pz/calibration*2.5*1e3/16384"
        min_bin = 0
        max_bin = 160
        bin_width = 1
        do_draw_sum = False

        xUnits = "mV"
        xtitle = "Energy"
        prefix = "energy_mV_"
 
    else:
        print "choose a plot to draw!"
        sys.exit()

    n_bins = int(math.floor((max_bin - min_bin)*1.0 / bin_width))

    #-------------------------------------------------------------------------------

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz
    channels = struck_analysis_parameters.channels
    channel_map = struck_analysis_parameters.channel_map
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    pmt_channel = struck_analysis_parameters.pmt_channel
    colors = struck_analysis_parameters.get_colors() 

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries

    # decide if this is a tier1 or tier2 file
    is_tier1 = False
    try:
        tree.GetEntry(0)
        tree.wfm0
        print "this is a tier2 file"
    except AttributeError:
        print "this is a tier1/tier3 file"
        n_channels = 1
        is_tier1 = True

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    basename = prefix + basename
    basename += "_".join(xtitle.split())

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)
    #canvas.SetLeftMargin(0.15)

    tree.SetLineColor(TColor.kBlue+1)
    #tree.SetFillColor(TColor.kBlue+1)
    #tree.SetFillStyle(3004)
    tree.SetLineWidth(2)

    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(len(channels))



    # set up some hists to hold TTree::Draw results
    hists = []
    
    #selections = [
        #"lightEnergy>700", # keep the light threshold high (some runs had low thresholds)
        #"adc_max_time[5]*40.0/1000<10", # light signal is within 10 microseconds of trigger
        #"is_amplified",
        #"energy>100",
        #"energy[5]>15",
        #"rise_time_stop-trigger_time <15",
        #"rise_time_stop-trigger_time >5"
        #"Iteration$<=50", # baseline average
        #"channel!=%i" % pmt_channel,
        #"channel!=5", # ortec channel
    #]

    frame_hist = TH1D("frame_hist","",n_bins,min_bin,max_bin)
    frame_hist.SetLineWidth(2)
    frame_hist.SetMinimum(1.0)
    tree.Draw("")
    selection = " && ".join(selections)

    if do_draw_sum:
        if do_draw_energy:
            print "%i entries in sum hist" % tree.Draw("chargeEnergy >> frame_hist", selection)
        else:
            print "%i entries in sum hist" % tree.Draw("%s >> frame_hist" % draw_command, selection)
        setup_hist(frame_hist, TColor.kBlack, xtitle, xUnits)
        legend.AddEntry(frame_hist, "sum","lp")


    y_max = 0
    for (channel, value) in enumerate(charge_channels_to_use):

        if not value:
            continue
 
        hist = TH1D("hist%i" % channel,"",n_bins,min_bin,max_bin)
        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack
        
        setup_hist(hist, color, xtitle, xUnits)
        hists.append(hist)
        legend.AddEntry(hist, channel_map[channel],"pl")

        print "channel %i | %s " % (channel, channel_map[channel])

        
        #draw_command = "wfm%i-baseline_mean" % channel
        draw_cmd = "%s >> %s" % (draw_command, hist.GetName())

        print "\t draw command: %s" % draw_cmd

        extra_selections = [
            "channel == %i" % channel,
            #"energy > 0",
            #"(rise_time_stop95 - trigger_time) >6",
            #"(adc_max_time - adc_max_time[5])*40.0/1000 < 15"
        ]
        selection = " && ".join(selections + extra_selections)
        print "\t selection: %s" % selection

        options = "same"
        if not do_draw_sum and channel == 0:
            options = ""
        print "\t options: %s" % options

        try:
            color = colors[channel]
        except IndexError:
            color = TColor.kBlack
        tree.SetLineColor(color)

        n_entries = tree.Draw(draw_cmd, selection, options)

        hist_mean = hist.GetMean()
        hist_rms = hist.GetRMS()
        print "\t hist mean: %.4f" % hist.GetMean()
        print "\t hist sigma: %.4f" % hist.GetRMS()

        if y_max < hist.GetMaximum(): y_max = hist.GetMaximum()
        print "\t %i entries" % n_entries

    legend.Draw()
    if not do_draw_sum:
        hists[0].SetMaximum(y_max)
    canvas.Update()

    if do_draw_energy and False:
        line_energy = 570
        print "==> drawing line at %i %s" % (line_energy, xUnits)
        line = TLine(line_energy, frame_hist.GetMinimum(), line_energy, frame_hist.GetMaximum())
        line.SetLineStyle(2)
        line.Draw()

    canvas.Update()
    canvas.Print("%s_log.png" % (basename))
    canvas.Print("%s_log.pdf" % (basename))
    if not gROOT.IsBatch():
        val = raw_input("--> enter to continue ")

    canvas.SetLogy(0)
    if do_draw_energy:
        # set maximum to the bin content at XXX keV
        frame_hist.SetMaximum(
            frame_hist.GetBinContent(
                frame_hist.FindBin(400)
            )
        )

        frame_hist.SetMaximum(12000)
    canvas.Print("%s_lin.png" % (basename))
    canvas.Print("%s_lin.pdf" % (basename))
    if not gROOT.IsBatch():
        val = raw_input("--> enter to continue ")



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



