#!/usr/bin/env python

"""
This script draws a spectrum from a root tree of nEXO_MC results.

Arguments: [nEXO root filename] [tier3 Struck data]


for 6th LXe:
python compareMCtoStruckData.py /nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/testing/Bi207_Full_3mm.root /nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root 

for 5th LXe:
python compareMCtoStruckData.py /nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/testing/Bi207_Full_3mm.root ~/5th_LXe/tier3/good_tier3.root

Conti et al. paper:
  "Correlated fluctuations between luminescence and ionization in liquid xenon"
  PHYSICAL REVIEW B 68, 054201 2003
"""

import os
import sys
import glob

from ROOT import gROOT
gROOT.SetBatch(True)
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
    source_activity_Bq = 400.0 # activity of 207-Bi source installed on cathode on Aug 7 2015
    run_duration_minutes = 10.0 # estimate of run length


    # estimate of ionization resolution comes from here:
    # https://confluence.slac.stanford.edu/download/attachments/162955571/EXO-200_public_material_28Feb2014.pptx?version=1&modificationDate=1394478396000&api=v2
    # sigma/E = 3.5% at the 2615-keV peak (91.5 keV)
    # the simplest thing is to assume this resolution does not vary with energy
    #sigma_keV =  3.5/100.0*2615 # charge-signal sigma, in keV, for energy smearing

    # from the Conti paper at 0.2 kV/cm, ~11.5% @ 570 keV:
    #sigma_keV =  11.5/100.0*570 # charge-signal sigma, in keV, for energy smearing

    # from the Conti paper at 1.0 kV/cm, ~5% @ 570 keV:
    sigma_keV =  5.0/100.0*570 # charge-signal sigma, in keV, for energy smearing

    sigma_keV = 51.3 # from 6th LXe

    print "sigma_keV", sigma_keV

    # construct a basename from the input filename
    basename = os.path.basename(mc_filename) # get rid of file path
    basename = os.path.splitext(basename)[0] # get rid of file suffix


    # open the root file and grab the tree
    mc_file = TFile(mc_filename)
    nEXOevents = mc_file.Get("nEXOevents")
    print "%.2e events in tree" % nEXOevents.GetEntries()

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
    struck_file = TFile(struck_filename)
    struck_tree = struck_file.Get("tree")
    hist_struck.GetDirectory().cd()
    struck_entries = struck_tree.Draw(
        "chargeEnergy >> %s" % hist_struck.GetName(),
        "energy>0 && channel==1",
        "goff"
    )
    hist_struck.SetMaximum(20e3)
    print "%i struck entries" % struck_entries

    nEXOevents.SetLineColor(TColor.kRed)
    #nEXOevents.SetFillColor(TColor.kRed)
    #nEXOevents.SetFillStyle(3005)
    nEXOevents.SetLineWidth(2)

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
    for i_entry in xrange(nEXOevents.GetEntries()):

        nEXOevents.GetEntry(i_entry)
        
        if (nEXOevents.TotalEventEnergy > 0.0):

            mc_energy_keV = nEXOevents.TotalEventEnergy*1e3
            smearing_keV = generator.Gaus()*sigma_keV
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
        i_entry*100.0/nEXOevents.GetEntries(),
    )


    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    # use i_entry instead of nEXOevents.GetEntries() so we can debug with less
    # than the full statistics in the nEXOevents tree
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
    #legend.AddEntry(nEXOevents, "MC", "l")
    legend.AddEntry(hist, "MC, #sigma=%i keV" % sigma_keV, "fl")
    legend.AddEntry(hist_struck, "Struck data, X27", "fl")

    hist_struck.Draw()
    hist.Draw("same") 
    #hist_struck.Draw("same")
    print "%i struck entries" % hist_struck.GetEntries()
    print "%i mc entries" % hist.GetEntries()

    # also draw the true energy spectrum, scaled appropriately:
    #nEXOevents.Draw("TotalEventEnergy*1e3","(TotalEventEnergy>0)*%s" % scale_factor,"same")
    #hist.Draw("same") # draw again, on top of the tree



    legend.Draw()
    canvas.Update()
    if not gROOT.IsBatch():
        raw_input("pause...")
    canvas.Print("%s_spectrum_sigma_%i_keV.pdf" % (basename, sigma_keV))

    # print a linear scale version
    canvas.SetLogy(0)
    canvas.Print("%s_spectrum_sigma_%i_keV_lin.pdf" % (basename, sigma_keV))

    
    canvas.SetLogy(0)
    resolution_hist.Draw()
    canvas.Update()
    canvas.Print("%s_smearing_sigma_%i_keV.pdf" % (basename, sigma_keV))
    print "sigma of resolution_hist: %.2f, specified sigma: %.2f" % (
        resolution_hist.GetRMS(),
        sigma_keV,
    )


if __name__ == "__main__":


    data_file = "/u/xo/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/overnight7thLXe.root" 
    mc_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph/tier3_5x/all_pcd_size_5x_dcoeff200.root",

    if len(sys.argv) < 2:
        print "optional arguments: [sis root files]"
        process_file(data_file, mc_file)


    else:
        process_file(sys.argv[1], sys.argv[2])



