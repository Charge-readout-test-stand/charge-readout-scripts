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

import ROOT
ROOT.gROOT.SetBatch(True) # comment this out to run interactively

import struck_analysis_parameters
import struck_analysis_cuts

ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       



def setup_hist(hist, color, xtitle, xUnits):
    """ Set color, line and marker style of hist """
    hist.SetLineColor(color)
    hist.SetMarkerStyle(21)
    hist.SetMarkerSize(0.8)
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
    do_draw_energy = 0
    do_draw_drift_times = 0
    do_draw_rms = 0
    do_draw_rms_keV = 0
    do_draw_rms_mV = 0
    do_draw_ADC_units = 0
    do_draw_mV = 0
    do_draw_one_strip_channels = 1

    #do_draw_sum = False # sum energy
    do_draw_sum = True # sum energy

    # default values:
    xUnits = ""
    prefix = "plots"
    selections = []
    #selections.append("Entry$<50") # debugging

    if do_draw_energy:
        print "---> drawing energies... "
        #draw_command = "energy1_pz"
        draw_command = "energy1"
        min_bin = 50
        max_bin = 2000
        bin_width = 10

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

    elif do_draw_one_strip_channels:
        print "---> drawing single-strip channel energies... "
        draw_command = "energy1_pz"
        min_bin = 100
        max_bin = 2000
        bin_width = 20

        xUnits = "keV"
        xtitle = "Energy"
        prefix = "single_strip_ch_energy_"
        
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
        selections.append("energy1>200")
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
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)
    #canvas.SetLeftMargin(0.15)

    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(10)

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

    frame_hist = ROOT.TH1D("frame_hist","",n_bins,min_bin,max_bin)
    frame_hist.SetLineWidth(2)
    frame_hist.SetMinimum(1.0)
    selection = " && ".join(selections)

    # setup hists:
    i_channel = 0
    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        if not value:
            continue
        hist = ROOT.TH1D("hist%i" % channel,"",n_bins,min_bin,max_bin)
        try:
            color = colors[i_channel]
        except IndexError:
            color = ROOT.kBlack
        setup_hist(hist, color, xtitle, xUnits)
        hists.append(hist)
        legend.AddEntry(hist, struck_analysis_parameters.channel_map[channel],"p")
        i_channel+=1


    for i_file, filename in enumerate(filenames):

        # open the root file and grab the tree
        print "--> processing",filename
        root_file = ROOT.TFile(filename)
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
                #energy_cmd = "chargeEnergy"
                energy_cmd = struck_analysis_cuts.get_few_channels_cmd_baseline_rms()
                print "sum energy cmd:"
                print energy_cmd
                print "%i entries in sum hist" % tree.Draw(
                    "%s >>+ frame_hist" % energy_cmd, 
                    selection, 
                    ""
                    )
            elif do_draw_one_strip_channels:
                energy_cmd = struck_analysis_cuts.get_few_one_strip_channels()
                print "sum energy cmd:"
                print energy_cmd
                print "%i entries in sum hist" % tree.Draw(
                    "%s >>+ frame_hist" % energy_cmd, 
                    "", 
                    ""
                    )
            else:
                selection = " && ".join(selections + [struck_analysis_cuts.get_channel_selection(isMC)])
                print "selection:", selection
                print "sum draw_command:", draw_command
                print "sum selection:", selection
                print "%i entries in sum hist" % tree.Draw("%s >>+ frame_hist" % draw_command, selection)
            setup_hist(frame_hist, ROOT.kBlack, xtitle, xUnits)

            canvas.SetLogy(0)
            canvas.Update()
            canvas.Print("%s_lin_sum.pdf" % basename)
            canvas.SetLogy(1)
            canvas.Update()
            canvas.Print("%s_log_sum.pdf" % basename)

        y_max = 0

        i_channel = 0
        for (channel, value) in enumerate(charge_channels_to_use):

            if not value:
                continue
     
            if do_draw_one_strip_channels:
                if struck_analysis_parameters.one_strip_channels[channel] != 1:
                    print "==> skipping channel %i: %s" % (channel, struck_analysis_parameters.channel_map[channel])
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

            n_entries = tree.Draw(draw_cmd, selection)

            title = "ch %i: %s {%s}" % (channel, channel_map[channel], selection)
            hist.SetTitle(title)
            canvas.SetLogy(0)
            canvas.Update()
            canvas.Print("%s_lin_ch%i.pdf" % (basename, channel))
            canvas.SetLogy(1)
            canvas.Update()
            canvas.Print("%s_log_ch%i.pdf" % (basename, channel))
            hist.SetTitle("")

            hist_mean = hist.GetMean()
            hist_rms = hist.GetRMS()
            
            if i_file == len(filenames)-1:
                print "\t draw command: %s" % draw_cmd, "selection: %s" % selection
                print "\t %i entries drawn, %i entries in hist" % (n_entries, hist.GetEntries())
            i_channel += 1
            # end loop over files
    
    
    for hist in hists:
        if y_max < hist.GetMaximum(): y_max = hist.GetMaximum()
        print "\t hist %s | max: %.2e | mean: %.4f | sigma: %.4f" % (
            hist.GetName(),
            hist.GetMaximum(),
            hist.GetMean(), 
            hist.GetRMS(),
        )

    if do_draw_sum:
        frame_hist.Draw()
        legend.AddEntry(frame_hist, "sum","p")
        if y_max < frame_hist.GetMaximum(): y_max = frame_hist.GetMaximum()
        frame_hist.SetMaximum(y_max*1.2)
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
        line = ROOT.TLine(line_energy, frame_hist.GetMinimum(), line_energy, frame_hist.GetMaximum())
        line.SetLineStyle(2)
        line.Draw()

    canvas.Update()
    #canvas.Print("%s_log.png" % (basename))
    canvas.Print("%s_log.pdf" % (basename))
    if not ROOT.gROOT.IsBatch():
        val = raw_input("--> enter to continue ")

    canvas.SetLogy(0)
    if do_draw_energy:
        # set maximum to the bin content at XXX keV
        y_max = frame_hist.GetBinContent(frame_hist.FindBin(570))
        frame_hist.SetMaximum(y_max*1.2)
    elif do_draw_drift_times:
        print "frame hist max:", frame_hist.GetMaximum()

    else:
        frame_hist.SetMaximum(12000)
    #canvas.Print("%s_lin.png" % (basename))
    canvas.Print("%s_lin.pdf" % (basename))
    if not ROOT.gROOT.IsBatch():
        val = raw_input("--> enter to continue ")



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    filenames = sys.argv[1:]
    process_files(filenames)



