#!/usr/bin/env python

"""
This script draws a spectrum from a root tree of digitized nEXO_MC results.

Arguments: [MC root filename] [tier3 Struck data]

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


def process_file(mc_filename, struck_filename):

    print "processing file: ", mc_filename

    # options:
    #draw_cmd = "chargeEnergy"
    draw_cmd = "energy1_pz"
    chargeEnergy_cut = "(%s>0)" % draw_cmd

    do_use_drift_time_cut = True
    do_use_single_strip_cut = True

    # drift-time cut info
    drift_time_low = struck_analysis_parameters.drift_time_threshold 
    #drift_time_low = 7.0
    
    #drift_time_high = drift_time_low+1.0
    drift_time_high = 9.0
    #drift_time_high = 11.0 # microseconds

    # this isn't the right scaling anymore, since we are using the pre-scaler
    # which throws away some data
    source_activity_Bq = 400.0 # activity of 207-Bi source installed on cathode on Aug 7 2015


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


    print "\tsigma_keV", sigma_keV

    mc_files = glob.glob(mc_filename)

    # open the root file and grab the tree
    if len(mc_filename) == 1:
        mc_file = TFile(mc_filename)
        mc_tree = mc_file.Get("tree")
        n_entries = mc_tree.GetEntries()
        basename = mc_filename
    else:
        mc_tree = TChain("tree")
        mc_tree.Add(mc_filename)
        n_entries = mc_tree.GetEntries()
        basename = os.path.commonprefix(mc_files)
    print "\t%.2e events in MC tree" % mc_tree.GetEntries()

    # construct a basename from the input filename
    basename = os.path.basename(basename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix
    print "basename:", basename 


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
    print "plot_name:", plot_name



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
                drift_time_low=drift_time_low,
                drift_time_high=drift_time_high,
            ))
    if do_use_single_strip_cut:
        part = struck_analysis_cuts.get_single_strip_cut()
        struck_selection.append(part)
    if "energy1_pz" in draw_cmd:
        #struck_selection.append(struck_analysis_cuts.get_channel_selection())
        struck_selection.append("channel==5")
    struck_selection = "&&".join(struck_selection)
    print "struck_selection:", struck_selection

    #struck_draw_cmd = draw_cmd 
    struck_draw_cmd = "%s*0.92" % draw_cmd# until e-calibration is fixed
    print "struck_draw_cmd:", struck_draw_cmd

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
    print "\t%.1e struck entries" % struck_entries

    # set MC color & style
    mc_tree.SetLineColor(TColor.kRed)
    #mc_tree.SetFillColor(TColor.kRed)
    #mc_tree.SetFillStyle(3005)
    mc_tree.SetLineWidth(2)

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
        mc_selection.append(struck_analysis_cuts.get_channel_selection(isMC=True))
        #mc_selection.append("channel==16")
    mc_selection = "&&".join(mc_selection)
    print "mc_selection:", mc_selection

    if sigma_keV == 0: # we don't add sigma anymore, since it's added in tier3

        mc_draw_cmd = draw_cmd
        print "mc_draw_cmd:", mc_draw_cmd

        hist.GetDirectory().cd()
        mc_entries = mc_tree.Draw(
            "%s >> %s" % (mc_draw_cmd, hist.GetName()),
            mc_selection,
            "goff"
        )
        print "\t%.1e MC entries" % mc_entries


    else: # for non-zero sigma

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

    # given the estimated activity of the source
    seconds_per_minute = 60.0
    struck_height = hist_struck.GetBinContent(hist_struck.FindBin(570))
    mc_height = hist.GetBinContent(hist.FindBin(570))
    scale_factor = struck_height/mc_height
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
        legend.AddEntry(hist, "MC (%.1e cts x %.2f)" % (hist.GetEntries(), scale_factor), "fl")
    else:
        legend.AddEntry(hist, "MC, #sigma_{addl}=%i keV" % sigma_keV, "fl") 
    legend.AddEntry(hist_struck, "Struck data (%.1e cts)" % hist_struck.GetEntries(), "fl")

    hist_struck.Draw()
    hist.Draw("same") 
    #hist_struck.Draw("same")
    print "%i struck entries" % hist_struck.GetEntries()
    print "%i mc entries" % hist.GetEntries()

    pave_text = TPaveText(0.7, 0.8, 0.9, 0.9, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    if do_use_drift_time_cut:
        pave_text.AddText("drift time: %.2f to %.2f #mus\n" % (
            drift_time_low, drift_time_high,))
    pave_text.Draw()

    # print log scale
    legend.Draw()
    canvas.Update()
    canvas.Print("%s.pdf" % plot_name)

    # print a linear scale version
    canvas.SetLogy(0)
    hist_max = hist_struck.GetMaximum()
    hist_struck.SetMaximum(struck_height*2.0)
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
    mc_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff50/tier3/tier3*.root"
    data_file = "/u/xo/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/overnight7thLXe.root" 

    process_file(mc_file, data_file)



