"""
Based on Manisha's test.C in LXe_Test_Stand_Analysis_light_map/scripts, this script takes a data.root file from Ako's Chroma
simulations and produces a TH2D. 
"""

import sys
import os
import ROOT
ROOT.gROOT.SetBatch(True)

# options:
n_trials = 100.0 # number of trials at each position
offset = 0.001 # small offset so that points don't fall on hist bin boundaries

# grab data_file_name from provided arguments, open the root file and grab the
# tree
data_file_name = sys.argv[1]
data_file = ROOT.TFile(data_file_name)
data = data_file.Get("data")

# Ako's spacing is 0.2mm
tfile = ROOT.TFile("SIPM_36_array_2016_12_09.root","recreate")
hist = ROOT.TH2D("hist","Light detection probability, 36-SIPM array", 35, 0.0, 7.0, 15, 0.0, 3.0)
hist.GetDirectory().cd()
hist.SetXTitle("r [cm]")
hist.SetYTitle("z [cm]")

# Ako simulated multiple trials at each point, so weight by photon_nr/n_trials.
n_drawn = data.Draw("zdir+%f:radius+%f >> hist" % (offset, offset),"photon_nr/%f" % n_trials,"goff")
hist.SetMinimum(0) # prevent 0 from showing as white

canvas = ROOT.TCanvas("canvas","")
canvas.SetRightMargin(0.15)
hist.Draw("colz")
canvas.Update()
canvas.Print("hist.pdf")
canvas.Print("hist.png")

hist.Write()

