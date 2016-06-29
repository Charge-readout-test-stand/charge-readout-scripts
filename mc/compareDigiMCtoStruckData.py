#!/usr/bin/env python

"""
# FIXME? change from TChain to adding to hists? this took 8 hours last time!!
This script draws a spectrum from a root tree of digitized nEXO_MC results.

Arguments: [MC root filename] [tier3 Struck data]

takes ~1 hour, 42 minutes (no TChain) 20 MAy 2016

for 6th LXe:
python compareDigiMCtoStruckData.py
/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207_Full_Ralph/Tier3/all_tier3_Bi207_Full_Ralph.root
/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root


Conti et al. paper:
  "Correlated fluctuations between luminescence and ionization in liquid xenon"
  PHYSICAL REVIEW B 68, 054201 2003
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
from ROOT import TRandom3
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
    mc_filenames, 
    struck_filename,
    i_channel=None,
    draw_cmd="energy1_pz",
    #draw_cmd = "chargeEnergy",
    do_use_drift_time_cut=True,
    do_use_single_strip_cut=True,
):

    print "====> processing MC files:", mc_filenames
    print "====> processing Struck data file:", struck_filename
    print "\t i_channel:", i_channel
    print "\t draw_cmd:", draw_cmd
    print "\t do_use_drift_time_cut:", do_use_drift_time_cut
    print "\t do_use_single_strip_cut:", do_use_single_strip_cut

    # options:
    chargeEnergy_cut = "(%s>0)" % draw_cmd

    # drift-time cut info
    drift_time_low = struck_analysis_parameters.drift_time_threshold 
    #drift_time_low = 8.0 # for investigating electrons from cathode
    print "drift_time_low:", drift_time_low
    
    drift_time_high = 9.5 # for electrons from cathode
    #drift_time_high = drift_time_low+1.0 # for a slice
    #drift_time_high = 8.0
    #drift_time_high = 11.0 # microseconds
    print "drift_time_low:", drift_time_high

    #struck_draw_cmd = draw_cmd 
    struck_energy_multiplier = struck_analysis_parameters.struck_energy_multiplier
    struck_draw_cmd = "%s*%s" % (draw_cmd, struck_energy_multiplier) # until e-calibration is fixed
    print "\t struck_draw_cmd:", struck_draw_cmd

    # this isn't the right scaling anymore, since we are using the pre-scaler
    # which throws away some data
    #source_activity_Bq = 400.0 # activity of 207-Bi source installed on cathode on Aug 7 2015

    # estimate of ionization resolution comes from here:
    # https://confluence.slac.stanford.edu/download/attachments/162955571/EXO-200_public_material_28Feb2014.pptx?version=1&modificationDate=1394478396000&api=v2
    # sigma/E = 3.5% at the 2615-keV peak (91.5 keV)
    # the simplest thing is to assume this resolution does not vary with energy
    #sigma_keV =  3.5/100.0*2615 # charge-signal sigma, in keV, for energy smearing

    # from the Conti paper at 0.2 kV/cm, ~11.5% @ 570 keV:
    #sigma_keV =  11.5/100.0*570 # charge-signal sigma, in keV, for energy smearing

    # from the Conti paper at 1.0 kV/cm, ~5% @ 570 keV:
    #sigma_keV =  5.0/100.0*570 # charge-signal sigma, in keV, for energy smearing

    #sigma_keV = 51.3 # from 6th LXe

    sigma_keV = 0.0 # we don't add sigma anymore since RMS noise is added in tier3

    #sigma_keV = 50.0 # testing


    print "\t sigma_keV", sigma_keV

    mc_files = glob.glob(mc_filenames)
    mc_files.sort()

    # construct a basename from the input filename
    basename = os.path.commonprefix(mc_files)
    basename = os.path.basename(basename) # get rid of file path
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

    # make a histogram to hold MC energies
    hist = TH1D("hist", "", 250, 0, 2500)
    hist.SetLineColor(TColor.kRed)
    hist.SetFillColor(TColor.kRed)
    hist.SetFillStyle(3004)
    hist.SetLineWidth(2)

    # setup struck hist & formatting
    hist_struck = TH1D("hist_struck","",250,0,2500)
    hist_struck.SetLineColor(TColor.kBlue)
    hist_struck.SetFillColor(TColor.kBlue)
    hist_struck.SetFillStyle(3004)
    hist_struck.SetLineWidth(2)
    hist_struck.GetYaxis().SetTitleOffset(1.3)

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


    # MC drawing selection
    mc_selection = [chargeEnergy_cut]
    if do_use_drift_time_cut:
        if "energy1_pz" in draw_cmd:
            mc_selection.append(
                "rise_time_stop95-trigger_time>=%s && rise_time_stop95-trigger_time<=%s" % (
                    drift_time_low,
                    drift_time_high))
        else:
            mc_selection.append(struck_analysis_cuts.get_drift_time_cut(
              drift_time_low=drift_time_low, 
              drift_time_high=drift_time_high,
              isMC=True,
            ))
    if do_use_single_strip_cut:
        part = struck_analysis_cuts.get_single_strip_cut(isMC=True)
        mc_selection.append(part)
    if "energy1_pz" in draw_cmd:
        if i_channel != None:
            mc_channel = struck_analysis_parameters.struck_to_mc_channel_map[i_channel]
            mc_selection.append("channel==%i" % mc_channel)
        else:
            mc_selection.append(struck_analysis_cuts.get_channel_selection(isMC=True))
    mc_selection = "&&".join(mc_selection)
    print "mc_selection:"
    print "\t", "\n\t || ".join(mc_selection.split("||"))

    if sigma_keV == 0: # we don't add sigma anymore, since it's added in tier3


        # open the root file and grab the tree
        mc_draw_cmd = draw_cmd
        print "mc_draw_cmd:", mc_draw_cmd
        print "%i MC files" % len(mc_files)
        for i_file, mc_file in enumerate(mc_files):
            tfile = TFile(mc_file)
            mc_tree = tfile.Get("tree")
            n_entries = mc_tree.GetEntriesFast()

            hist.GetDirectory().cd()
            mc_entries = mc_tree.Draw(
                "%s >>+ %s" % (mc_draw_cmd, hist.GetName()),
                mc_selection,
                "goff"
            )

            #print "---> file %i of %i: %i events in MC tree, %i entries drawn, %.2e hist entries" % (
            #    i_file,
            #    len(mc_files),
            #    n_entries,
            #    mc_entries,
            #    hist.GetEntries(),
            #)

    else: # for non-zero sigma -- FIXME -- this doesn't work anymore

        # random number generator
        generator = TRandom3(0)

        # make a histogram to hold smearing info
        resolution_hist = TH1D("resolution_hist","sigma = %.2f keV" % sigma_keV, 200, -50, 50)
        resolution_hist.SetLineColor(TColor.kRed)
        resolution_hist.SetFillColor(TColor.kRed)
        resolution_hist.SetFillStyle(3004)
        resolution_hist.SetLineWidth(2)
        resolution_hist.SetXTitle("energy [keV]")


        # fill the hist in a loop so we can smear the energy resolution
        print "filling hist..."
        for i_entry in xrange(mc_tree.GetEntries()):
            mc_tree.GetEntry(i_entry)
            #if (mc_tree.chargeEnergy > 0.0):
            if True:
                mc_energy_keV = mc_tree.chargeEnergy
                smearing_keV = generator.Gaus()*sigma_keV
                # print some debugging info:
                #print "mc_energy_keV: %.2f | smearing_keV: %.2f | sum: %.2f" % (
                #    mc_energy_keV,
                #    smearing_keV,
                #    mc_energy_keV+smearing_keV,
                #)
                hist.Fill(mc_energy_keV + smearing_keV)
                resolution_hist.Fill(smearing_keV)

            #if i_entry > 1e4: 
            #    print "stopping early for debugging..."
        
        # use i_entry instead of mc_tree.GetEntries() so we can debug with less
        # than the full statistics in the mc_tree tree
        print "%.2e of %.2e events (%.2f percent) had non-zero energy deposits" % (
            hist.GetEntries(),
            i_entry+1,
            hist.GetEntries()/(i_entry+1)*100.0,
        )

        #    break # debugging

        print "done filling hist with %.2f percent of tree entries" % (
            i_entry*100.0/mc_tree.GetEntries(),
        )

        # end handling of smearing 


    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    # scale MC to match struck data, many different methods... 

    peak_energy = 570
    # struck_height used for scaling (sometimes) and also for plotting
    struck_height = hist_struck.GetBinContent(hist_struck.FindBin(peak_energy))
    if False: # use peak height
        print "scale factor based on height at %i keV" % peak_energy
        mc_height = hist.GetBinContent(hist.FindBin(peak_energy))
        scale_factor = struck_height/mc_height

    integral_energy_min = 300.0
    integral_energy_max = 2500.0
    if True: # use integral counts
        # normalize each channel independently
        min_bin = hist.FindBin(integral_energy_min)
        max_bin = hist.FindBin(integral_energy_max) 
        mc_counts = hist.Integral(min_bin, max_bin)
        struck_counts = hist_struck.Integral(min_bin, max_bin)
        scale_factor = struck_counts/mc_counts
        print "scale factor based on spectrum integral above %i keV" % integral_energy_min

    else:
        # normalize based on number of counts in all charge channels, use same
        # normalization for each channel
        print "scale factor based on integral %s above %i keV with selections" % (
            draw_cmd, integral_energy_min)
        do_use_n_events = True # whether to use n events or n channel hits
        if do_use_n_events:
            mc_selection = "%s>%s && %s<%s" % (
                draw_cmd, integral_energy_min,
                draw_cmd, integral_energy_max,
            )
            mc_selection+= "&&" + struck_analysis_cuts.get_drift_time_cut(
                energy_threshold=200.0,
                drift_time_low=drift_time_low,
                drift_time_high=drift_time_high,
                isMC=True
            )
        else:
            print "need drift time cut!!!"
            mc_selection = "%s>%s && %s<%s && %s" % (
                draw_cmd, integral_energy_min,
                draw_cmd, integral_energy_max,
                struck_analysis_cuts.get_channel_selection(isMC=True))

        print "scale factor MC selection:", mc_selection
        mc_counts = mc_tree.Draw(draw_cmd,mc_selection,"goff")
        print "mc_counts:", mc_counts
        if do_use_n_events:
            struck_selection = "%s>%s && %s<%s" % ( 
                struck_draw_cmd, integral_energy_min,
                struck_draw_cmd, integral_energy_max,)
            struck_selection += "&&"+struck_analysis_cuts.get_drift_time_cut(
                energy_threshold=200.0/struck_energy_multiplier,
                drift_time_low=drift_time_low,
                drift_time_high=drift_time_high,
            )
        else:
            struck_selection = "%s>%s && %s<%s && %s" % ( 
                struck_draw_cmd, integral_energy_min,
                struck_draw_cmd, integral_energy_max,
                struck_analysis_cuts.get_channel_selection())
        print "scale factor Struck selection:", struck_selection
        struck_counts = struck_tree.Draw(struck_draw_cmd,struck_selection,"goff")
        print "struck_counts:", struck_counts
        scale_factor = struck_counts*1.0/mc_counts

    #scale_factor *= 0.5 # extra offset for viewing
    print "scale_factor", scale_factor
    hist.Scale(scale_factor)

    hist_struck.SetXTitle("Energy [keV]")
    hist_struck.SetYTitle("Counts  / %i keV" % (
        hist.GetBinWidth(1),
    ))

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)
    if sigma_keV == 0:
        mc_title = "MC "
        if "energy1_pz" in draw_cmd and i_channel != None:
            mc_title += "Ch%i " % i_channel
        mc_title += "(%.1e cts x %.2f)" % (hist.GetEntries(), scale_factor)
        legend.AddEntry(hist, mc_title,"f")
    else:
        legend.AddEntry(hist, "MC, #sigma_{addl}=%i keV" % sigma_keV, "f") 
    legend.AddEntry(hist_struck, "Struck data (%.1e cts)" % hist_struck.GetEntries(), "f")

    hist_struck.Draw()
    hist.Draw("same") 
    #hist_struck.Draw("same")
    print "%i entries in hist_struck" % hist_struck.GetEntries()
    print "%i entries in MC hist" % hist.GetEntries()

    pave_text = TPaveText(0.65, 0.8, 0.9, 0.9, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    if do_use_drift_time_cut:
        pave_text.AddText("drift time: %.2f to %.2f #mus\n" % (
            drift_time_low, drift_time_high,))
    pave_text.Draw()

    energy_min = 430.0
    energy_max = 700.0
    get_integral(hist_struck, energy_min, energy_max)
    get_integral(hist, energy_min, energy_max)

    energy_min = 900.0
    energy_max = 1200.0
    get_integral(hist_struck, energy_min, energy_max)
    get_integral(hist, energy_min, energy_max)

    # print log scale
    legend.Draw()
    canvas.Update()
    canvas.Print("%s.pdf" % plot_name)

    # print a linear scale version
    canvas.SetLogy(0)
    hist_max = hist_struck.GetMaximum()
    hist_struck.SetMaximum(struck_height*2.4)
    canvas.Update()
    canvas.Print("%s_lin.pdf" % plot_name)

    if not gROOT.IsBatch():
        canvas.SetLogy(1)
        hist_struck.SetMaximum(hist_max*2.0)
        canvas.Update()
        raw_input("pause...")

    if sigma_keV > 0:
        canvas.SetLogy(0)
        resolution_hist.Draw()
        canvas.Update()
        canvas.Print("%s_smearing_sigma_%i_keV.pdf" % (basename, sigma_keV))
        print "sigma of resolution_hist: %.2f, specified sigma: %.2f" % (
            resolution_hist.GetRMS(),
            sigma_keV,
        )


if __name__ == "__main__":

    #if len(sys.argv) < 2:
    #    print "arguments: [sis root files]"
    #    sys.exit(1)

    # loop over all provided arguments
    #process_file(sys.argv[1], sys.argv[2])


    #mc_file = "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/Bi207_Full_Ralph/Tier3/all_tier3_Bi207_Full_Ralph.root"
    #mc_file = "207biMc.root"
    #data_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root"

    # 7th LXe
    #mc_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/old_Bi207_Full_Ralph/tier3_5x/all_dcoef200_pcd_size_5x.root"
    mc_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff50/tier3/tier3_*.root"
    data_file = "/u/xo/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/overnight7thLXe.root" 

    process_file(mc_file, data_file,draw_cmd="chargeEnergy", do_use_single_strip_cut=False)
    #sys.exit()  # testing
    process_file(mc_file, data_file,draw_cmd="chargeEnergy")
    process_file(mc_file, data_file,i_channel=None, do_use_single_strip_cut=False)
    process_file(mc_file, data_file,i_channel=None)
    process_file(mc_file, data_file,draw_cmd="chargeEnergy", do_use_single_strip_cut=False, do_use_drift_time_cut=False)
    for i_channel in xrange(8):
        process_file(mc_file, data_file,
            i_channel=i_channel,
            do_use_single_strip_cut=True,
        )



