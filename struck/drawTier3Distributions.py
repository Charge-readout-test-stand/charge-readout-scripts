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
import struck_analysis_cuts

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
    print "hist %s bin width" % hist.GetName(), hist.GetBinWidth(1)
    #hist.SetFillColor(color)


def process_files(filenames):

    print "processing %i files: " % len(filenames)

    #-------------------------------------------------------------------------------
    # options

    # choose one:
    do_draw_energy = 1
    do_draw_drift_times = 0
    do_draw_rms = 0
    do_draw_rms_keV = 0
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
        max_bin = 2010
        bin_width = 15

        xUnits = "keV"
        xtitle = "Energy"
        prefix = "energy_"
        #selections.append(struck_analysis_cuts.get_single_strip_cut(10.0))
        #selections.append(struck_analysis_parameters.get_long_drift_time_cut(
        #    energy_threshold=None,
        #    drift_time_high=9.0,
        #))
        #selections.append("(rise_time_stop99-trigger_time>6.43)&&(rise_time_stop99-trigger_time<9.0)")
        #selections.append("(rise_time_stop95-trigger_time>6.43)&&(rise_time_stop95-trigger_time<9.0)")
        
    elif do_draw_drift_times:
        print "---> drawing drift times"
        #draw_command = "rise_time_stop99 - trigger_time"
        draw_command = "rise_time_stop95 - trigger_time"
        #min_bin = -10.02
        #max_bin = 30.02
        min_bin = -5.02
        max_bin = 25.02
        bin_width = 0.04
        xUnits = "#mus"
        xtitle = "Drift time"
        selections.append("energy1_pz>700")
        do_draw_sum=True

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
    print "bin_width:   ", bin_width
    print "n_bins:", n_bins

    #-------------------------------------------------------------------------------

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz
    channels = struck_analysis_parameters.channels
    #pmt_channel = struck_analysis_parameters.pmt_channel
    colors = struck_analysis_parameters.get_colors() 

    basename = os.path.basename(filenames[0])
    basename = os.path.splitext(basename)[0]
    basename = prefix + basename
    basename += "_".join(xtitle.split())

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)
    #canvas.SetLeftMargin(0.15)

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
    #tree.Draw("")
    selection = " && ".join(selections)

    # setup hists:
    i_channel = 0
    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        if not value:
            continue
        hist = TH1D("hist%i" % channel,"",n_bins,min_bin,max_bin)
        try:
            color = colors[i_channel]
        except IndexError:
            color = TColor.kBlack
        setup_hist(hist, color, xtitle, xUnits)
        hists.append(hist)
        legend.AddEntry(hist, struck_analysis_parameters.channel_map[channel],"pl")
        i_channel+=1


    for i_file, filename in enumerate(filenames):

        # open the root file and grab the tree
        print "--> processing",filename
        root_file = TFile(filename)
        tree = root_file.Get("tree")
        try:
            n_entries = tree.GetEntries()
            print "\t %i tree entries, file %i of %i" % (n_entries, i_file, len(filenames))
        except AttributeError:
            print "\t skipping bad file!"
            continue

        # decide if this is a tier1 or tier2 file
        is_tier1 = False
        try:
            tree.GetEntry(0)
            tree.wfm0
            print "this is a tier2 file"
        except AttributeError:
            #print "this is a tier1/tier3 file"
            n_channels = 1
            is_tier1 = True

        isMC = struck_analysis_parameters.is_tree_MC(tree)
        print "isMC:", isMC

        channel_map = struck_analysis_parameters.channel_map
        charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
        if isMC: 
            charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
            channel_map = struck_analysis_parameters.mc_channel_map

        frame_hist.GetDirectory().cd()

        if do_draw_sum:
            if do_draw_energy:
                selection = " && ".join(selections)
                print "sum selection:", selection
                print "%i entries in sum hist" % tree.Draw("chargeEnergy >>+ frame_hist", selection, "goff")
            else:
                selection = " && ".join(selections + [struck_analysis_cuts.get_channel_selection(isMC)])
                print "selection:", selection
                print "sum draw_command:", draw_command
                print "sum selection:", selection
                print "%i entries in sum hist" % tree.Draw("%s >>+ frame_hist" % draw_command, selection, "goff")
            setup_hist(frame_hist, TColor.kBlack, xtitle, xUnits)
            legend.AddEntry(frame_hist, "sum","lp")


        y_max = 0

        i_channel = 0
        for (channel, value) in enumerate(charge_channels_to_use):

            if not value:
                continue
     
            #print "channel %i | %s " % (channel, channel_map[channel])

            
            #draw_command = "wfm%i-baseline_mean" % channel
            hist = hists[i_channel]
            draw_cmd = "%s >>+ %s" % (draw_command, hist.GetName())


            extra_selections = [
                "channel == %i" % channel,
                #"energy > 0",
                #"(rise_time_stop95 - trigger_time) >6",
                #"(adc_max_time - adc_max_time[5])*40.0/1000 < 15"
            ]
            selection = " && ".join(selections + extra_selections)

            n_entries = tree.Draw(draw_cmd, selection, "goff")

            hist_mean = hist.GetMean()
            hist_rms = hist.GetRMS()
            
            if i_file == len(filenames)-1:
                print "\t draw command: %s" % draw_cmd, "selection: %s" % selection
                print "\t %i entries drawn, %i entries in hist" % (n_entries, hist.GetEntries())
            i_channel += 1
            # end loop over files
    
    
    for hist in hists:
        print "hist", hist.GetName()
        if y_max < hist.GetMaximum(): y_max = hist.GetMaximum()
        print "\t hist mean: %.4f | hist sigma: %.4f" % (hist.GetMean(), hist.GetRMS())

    if do_draw_sum:
        frame_hist.Draw()
    else:
        hists[0].SetMaximum(y_max*1.2)
        hists[0].Draw()
        
    for hist in hists:
        hist.Draw("same")

    legend.Draw()
    canvas.Update()

    if do_draw_energy and False:
        line_energy = 570
        print "==> drawing line at %i %s" % (line_energy, xUnits)
        line = TLine(line_energy, frame_hist.GetMinimum(), line_energy, frame_hist.GetMaximum())
        line.SetLineStyle(2)
        line.Draw()

    canvas.Update()
    #canvas.Print("%s_log.png" % (basename))
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
    elif do_draw_drift_times:
        print "frame hist max:", frame_hist.GetMaximum()

    else:
        frame_hist.SetMaximum(12000)
    #canvas.Print("%s_lin.png" % (basename))
    canvas.Print("%s_lin.pdf" % (basename))
    if not gROOT.IsBatch():
        val = raw_input("--> enter to continue ")



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    filenames = sys.argv[1:]
    process_files(filenames)



