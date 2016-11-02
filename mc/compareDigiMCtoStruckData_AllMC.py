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
# it seems like if this is commented out the legend has red background
gROOT.SetBatch(True) # comment out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle
from ROOT import TRandom3


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(mc_filename, struck_filename):

    print "processing file: ", mc_filename

    # options:

    run_duration_minutes = 10.0 # estimate of run length
    
    # this isn't the right scaling any more, since we are using the pre-scaler
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
    sigma_keV =  5.0/100.0*570 # charge-signal sigma, in keV, for energy smearing

    #sigma_keV = 51.3 # from 6th LXe
    sigma_keV = 20 # from 6th LXe


    print "\tsigma_keV", sigma_keV

    # construct a basename from the input filename
    basename = os.path.basename(mc_filename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix

    # open the root file and grab the tree
    mc_file = TFile(mc_filename)
    mc_tree = mc_file.Get("tree")
    print "\t%.2e events in MC tree" % mc_tree.GetEntries()

    # make a histogram to hold energies
    hist = TH1D("hist", "", 200, 0, 2500)
    hist.SetLineColor(TColor.kRed)
    hist.SetFillColor(TColor.kRed)
    hist.SetFillStyle(3004)
    hist.SetLineWidth(2)

    hist_struck = TH1D("hist_struck","",200,0,2500)
    hist_struck.SetLineColor(TColor.kBlue)
    hist_struck.SetFillColor(TColor.kBlue)
    hist_struck.SetFillStyle(3004)
    hist_struck.SetLineWidth(2)

    # open the struck file and get its entries
    print "processing file: ", mc_filename
    struck_file = TFile(struck_filename)
    struck_tree = struck_file.Get("tree")
    hist_struck.GetDirectory().cd()
    struck_entries = struck_tree.Draw(
        "chargeEnergy >> %s" % hist_struck.GetName(),
        "chargeEnergy>0",
        "goff"
    )
    #hist_struck.SetMaximum(20e3)
    print "\t%.1e struck entries" % struck_entries

    mc_tree.SetLineColor(TColor.kRed)
    #mc_tree.SetFillColor(TColor.kRed)
    #mc_tree.SetFillStyle(3005)
    mc_tree.SetLineWidth(2)

    # make a histogram to hold smearing info
    resolution_hist = TH1D("resolution_hist","sigma = %.2f keV" % sigma_keV, 200, -1000, 1000)
    resolution_hist.SetLineColor(TColor.kRed)
    resolution_hist.SetFillColor(TColor.kRed)
    resolution_hist.SetFillStyle(3004)
    resolution_hist.SetLineWidth(2)
    resolution_hist.SetXTitle("energy [keV]")

    # random number generator
    generator = TRandom3(0)

    # fill the hist in a loop so we can smear the energy resolution
    print "filling hist..."
    for i_entry in xrange(mc_tree.GetEntries()):

        mc_tree.GetEntry(i_entry)
        
        if (mc_tree.MCchargeEnergy > 0.0):

            # multiplying energy by 115% for now -- 18 Dec 2015
            mc_energy_keV = mc_tree.MCchargeEnergy*1.15

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
        #    break # debugging

    print "done filling hist with %.2f percent of tree entries" % (
        i_entry*100.0/mc_tree.GetEntries(),
    )


    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    # use i_entry instead of mc_tree.GetEntries() so we can debug with less
    # than the full statistics in the mc_tree tree
    print "%.2e of %.2e events (%.2f percent) had non-zero energy deposits" % (
        hist.GetEntries(),
        i_entry+1,
        hist.GetEntries()/(i_entry+1)*100.0,
    )

    # scale the hist to show expected counts in a run of run_duration_minutes,
    # given the estimated activity of the source
    seconds_per_minute = 60.0
    scale_factor = source_activity_Bq*seconds_per_minute*run_duration_minutes/(i_entry+1)
    print "scale_factor", scale_factor
    struck_height = hist_struck.GetBinContent(hist_struck.FindBin(570))
    mc_height = hist.GetBinContent(hist.FindBin(570))
    scale_factor = struck_height/mc_height
    hist.Scale(scale_factor)

    hist_struck.SetXTitle("Energy [keV]")
    hist_struck.SetYTitle("Counts  / %i keV" % (
        hist.GetBinWidth(1),
    ))

    # set up a legend
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.AddEntry(hist, "MC, #sigma_{addl}=%i keV" % sigma_keV, "fl")
    legend.AddEntry(hist_struck, "Struck data", "fl")

    hist_struck.Draw()
    hist.Draw("same") 
    #hist_struck.Draw("same")
    print "%i struck entries" % hist_struck.GetEntries()
    print "%i mc entries" % hist.GetEntries()

    legend.Draw()
    canvas.Update()

    if not gROOT.IsBatch():
        raw_input("pause...")
    canvas.Print("%s_spectrumALL_sigma_%i_keV.pdf" % (basename, sigma_keV))

    # print a linear scale version
    canvas.SetLogy(0)
    canvas.Print("%s_spectrumALL_sigma_%i_keV_lin.pdf" % (basename, sigma_keV))

    
    canvas.SetLogy(0)
    resolution_hist.Draw()
    canvas.Update()
    canvas.Print("%s_smearingALL_sigma_%i_keV.pdf" % (basename, sigma_keV))
    print "sigma of resolution_hist: %.2f, specified sigma: %.2f" % (
        resolution_hist.GetRMS(),
        sigma_keV,
    )


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "arguments: [MC root file, sis root file]"
        sys.exit(1)


    # loop over all provided arguments
    process_file(sys.argv[1], sys.argv[2])



