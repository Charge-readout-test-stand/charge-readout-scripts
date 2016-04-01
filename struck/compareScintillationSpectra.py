#!/bin/env python

"""
Compare scintillation spectra collected at different E field strengths
"""

import os
import sys
import math
import glob

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TH1D

import struck_analysis_parameters

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def compare_spectra(directory, filename_prefixes):

    pmt_channel = struck_analysis_parameters.pmt_channel
    print "PMT channel: %i" % pmt_channel

    # options:
    min_bin = 0
    max_bin = 8000
    bin_width = 50
    if struck_analysis_parameters.is_6th_LXe:
        min_bin = 0
        max_bin = 8000
        bin_width = 50
    elif struck_analysis_parameters.is_7th_LXe:
        min_bin = 0
        max_bin = 3000
        bin_width = 5
        

    n_bins = int(math.floor((max_bin - min_bin)/bin_width))
    #-------------------------------------------------------------------------------



    colors = struck_analysis_parameters.get_colors()
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)

    hists = []

    for filename_prefix in filename_prefixes:
        print "--> processing %s*.root" % filename_prefix

        files = glob.glob("%s/%s*.root" % (directory, filename_prefix))
        print "\t%i files" % len(files)

        try:
            if struck_analysis_parameters.is_6th_LXe:
                # 6th LXe format:
                cathode_bias = filename_prefix.split("_")[3]
                cathode_bias = cathode_bias.split("V")
                cathode_bias = int(cathode_bias[0])
            elif struck_analysis_parameters.is_7th_LXe:
                # 7th LXe format:
                cathode_bias = filename_prefix.split("_")[5]
                cathode_bias = cathode_bias.split("V")
                cathode_bias = int(cathode_bias[0])
        except ValueError:
            cathode_bias = 0
            print "default bias:", cathode_bias
        except IndexError:
            cathode_bias = 1700
            print "default bias:", cathode_bias

        print "\t %i V bias" % cathode_bias

        hist = TH1D(
            "hist%i" % len(hists),
            "",
            n_bins,
            min_bin,
            max_bin
        )
        hist.SetLineWidth(2)
        hist.SetLineColor(colors[len(hists)])
        hist.SetXTitle("Energy [keV]")
        hist.SetYTitle("Counts / %i keV / second" % bin_width)
        if struck_analysis_parameters.is_7th_LXe:
            hist.SetXTitle("Energy [ADC units]")
            hist.SetYTitle("Counts / %i ADC units / second" % bin_width)

        run_duration = 0.0

        multiplier = 1.0
        for i_file in files:
            #print i_file
            tfile = TFile(i_file)
            hist.GetDirectory().cd()
            tree = tfile.Get("tree")
            run_tree = tfile.Get("run_tree")
            tree.GetEntry(0)
            for i, channel in enumerate(tree.channel):
                channel = ord(channel)
                #print "tree channels:", i, channel
                if channel == pmt_channel:
                    pmt_index = i
            try:
                calibration = tree.calibration[pmt_index]
                print "PMT calibration:", calibration
            except:
                tree.Show(0)
                return

            for entry in xrange(run_tree.GetEntries()):
                run_tree.GetEntry(entry)
                try:
                    run_duration += run_tree.run_duration
                except AttributeError: # old version
                    run_duration += run_tree.run_time

            try:
                if tree.baseline_mean_file[pmt_index] < 8000:
                    multiplier /= 2.5
            except AttributeError:
                print "no baseline_mean_file info available"

            #if cathode_bias == 0:
            #    multiplier *= 2

            
            draw_command = "lightEnergy*%s >>+ %s" % (multiplier, hist.GetName())
            if struck_analysis_parameters.is_7th_LXe:
                draw_command = "lightEnergy/%s >>+ %s" % (calibration, hist.GetName())
            try:
                print "\tbaseline mean:", tree.baseline_mean_file[pmt_index]
                print "\tbaseline RMS:", tree.baseline_rms_file[pmt_index]
                print "\tis amplified:", tree.is_amplified[pmt_index]
            except AttributeError:
                pass
            print "\t draw_command:", draw_command
            n_entries = tree.Draw(draw_command, "", "goff")

            print "\t %i tree entries" % n_entries
        #tree.Show(0)

        print "\t%i hist entries" % hist.GetEntries()
        hist.Scale(1.0/run_duration)

        hists.append(hist)

        legend_entry = "%i V (%i kV/cm), %.1E counts" % (
            cathode_bias, 
            cathode_bias/1.7,
            hist.GetEntries()
        )

        legend.AddEntry(hist, legend_entry, "l")


    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    canvas.SetLogy(1)


    print "%i hists" % len(hists)
    hists[0].Draw()
    for hist in hists:
        hist.Draw("same")

    legend.Draw()

    canvas.Update()
    canvas.Print("scintillationSpectraForDifferentEFields.pdf")

    raw_input("--> enter to continue ")



    
if __name__ == "__main__":


    #directory = "/u/xo/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2"
    directory = "/u/xo/alexis4/test-stand/2016_03_07_7thLXe/tier3_external"

    # data from 6th LXe at +1200V PMT bias
    #filename_prefixes = [
    #    #"tier3_xenon8300g_1200VPMT_0Vcathode_amplified_PMT_shaper_",
    #    "tier3_xenon8300g_1200VPMT_100Vcathode_amplified_shaped_",
    #    "tier3_xenon8300g_1200VPMT_300Vcathode_amplified_shaped_",
    #    "tier3_xenon8300g_1200VPMT_500Vcathode_amplified_shaped_",
    #    "tier3_xenon8300g_1200VPMT_1000Vcathode_amplified_shaped_",
    #    #"tier3_xenon8300g_1200VPMT_1700Vcathode_amplified_2",
    #    #"tier3_Xxenon8300g_1200VPMT_1700Vcathode_amplified_600delay",
    #]


    # data from 6th LXe at +1300V PMT bias
    #filename_prefixes = [
    #    "tier3_xenon8300g_1300VPMT_0Vcathode_amplified_PMT_shaper_2",
    #    "tier2to3_overnight",
    #]

    # data from 7th LXe at +1250V PMT 9921QB bias
    filename_prefixes = [
        "tier3_cell_full_cathode_bias_off_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016",
        "tier3_cell_full_cathode_bias_36V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016",
        "tier3_cell_full_cathode_bias_300V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016",
        "tier3_cell_full_cathode_bias_500V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016",
        "tier3_cell_full_cathode_bias_1000V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016", 
        "overnight7thLXe",
    ]

    compare_spectra(directory, filename_prefixes)
