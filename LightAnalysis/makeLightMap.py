"""
Based on Manisha's test.C in LXe_Test_Stand_Analysis_light_map/scripts, this
script takes a data.root file from Ako's Chroma simulations and produces a TH2D. 
"""

import sys
import os
import ROOT
ROOT.gROOT.SetBatch(True)

# options:
n_trials = 100.0 # number of trials at each position
epsilon = 0.001 # small offset so that points don't fall on hist bin boundaries

# grab data_file_name from provided arguments, open the root file and grab the
# tree
data_file_name = sys.argv[1]
data_file = ROOT.TFile(data_file_name)
data = data_file.Get("data")

# construct a basename from the filename
basename = os.path.basename(data_file_name)
print "--> processing:", basename
basename = os.path.splitext(basename)[0]

# defaults
z_offset = 1.80 # cm; In Ako's sim, cathode was at 18mm, anode at 0
spacing = 0.20 # Ako's spacing is 0.2cm
r_max = 10.20 
z_min = z_offset - 7.8
z_max = z_offset + spacing
filename = "%s_map" % basename
title = "Light detection probability, PMT 9921QB, %.1f-cm drift" % z_offset 


# 36 SiPMs:
if "2016_12_09_ako_data" in basename:
    filename = "SIPM_36_array_light_map_hist_2016_12_09"
    title = "Light detection probability, 36-SIPM array, cathode at z=0, %.1f-cm drift" % z_offset

    spacing = 0.2 # Ako's spacing is 0.2cm
    r_max = 7.0
    z_min = z_offset - 4.4
    z_max = z_offset

r_bins = int((r_max + spacing/2.0)/ spacing)
z_bins = int((z_max - z_min)/spacing)
print "%i bins in r, from 0 to %.3f" % (r_bins, r_max)
print "%i bins in z, from %.3f to %.3f" % (z_bins, z_min, z_max)

tfile = ROOT.TFile("%s.root" % filename,"recreate")

hist = ROOT.TH2D("hist", 
    title, 
    r_bins, 0.0, r_max, 
    z_bins, z_min, z_max)

hist.GetDirectory().cd()
hist.SetXTitle("r [cm]")
hist.SetYTitle("z [cm]")

# Ako ran multiple trials at each point, so weight by photon_nr/n_trials.
draw_cmd = "%f-zdir-%f:radius+%f >> hist" % (z_offset, epsilon, epsilon)
print "draw_cmd:", draw_cmd

n_drawn = data.Draw(
    draw_cmd,
    "photon_nr/%f" % n_trials,
    "goff")

hist.SetMinimum(0) 
#hist.SetMinimum(-1e-4) 

canvas = ROOT.TCanvas("canvas","")
canvas.SetRightMargin(0.15)

# draw to check binning
n_drawn = data.Draw(
    draw_cmd,
    "1.0/%f" % n_trials,
    "goff")
hist.Draw("colz")
canvas.Print("%s_bins.pdf" % filename)
canvas.Print("%s_bins.png" % filename)

# draw again to make light map
n_drawn = data.Draw(
    draw_cmd,
    "photon_nr/%f" % n_trials,
    "goff")
hist.Draw("colz")
canvas.Update()
canvas.Print("%s.pdf" % filename)
canvas.Print("%s.png" % filename)

print "efficiency at (0, -1):",  hist.GetBinContent(hist.FindBin(0,-1))
print "efficiency at (0, +1):",  hist.GetBinContent(hist.FindBin(0,1))

hist.Write()

