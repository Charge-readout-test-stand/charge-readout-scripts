"""
This script find the average RMS (in keV) for charge waveforms from different
channels. 
"""


import os
import sys
import math
import time

from ROOT import gROOT
gROOT.SetBatch(True) #comment out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TTree
from ROOT import TGraph
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TColor
from ROOT import gStyle
from ROOT import gSystem
from ROOT import TPaveText

# definition of calibration constants, decay times, channels
import struck_analysis_parameters

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       


def process_file(file_name):

    # options:
    min_bin = -10
    max_bin = 100
    n_bins = max_bin - min_bin

    print "---> processing", file_name

    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    tfile = TFile(file_name)
    tree = tfile.Get("tree")
 
    charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    calibration_values = struck_analysis_parameters.calibration_values
    channel_map = struck_analysis_parameters.channel_map
    rms_keV = struck_analysis_parameters.rms_keV


    hist = TH1D("hist","",n_bins, min_bin, max_bin)
    hist.SetXTitle("Baseline RMS [keV]")
    hist.SetYTitle("Counts / keV")

    for channel in xrange(len(charge_channels_to_use)):
        if charge_channels_to_use[channel] == 0: continue

        calibration = calibration_values[channel]
        channel_name = channel_map[channel]

        hist.GetDirectory().cd()
        colors = struck_analysis_parameters.get_colors()
        color = colors[channel % len(colors)]
        hist.SetLineColor(color)
        hist.SetLineWidth(2)
        hist.SetFillColor(color)
        hist.SetFillStyle(3004)

        tree.Draw(
            "baseline_rms*calibration >> %s" % hist.GetName(),
            "channel==%i" % channel,
            #"goff" # graphics off
        )
        n_entries =  hist.GetEntries()
        rms = hist.GetMean()

        # find percentage difference between this value and the one in
        # struck_analysis_parameters:
        try:
            rms_ref = rms_keV[channel]
        except:
            #print "no ref info available for channel %i" % channel
            rms_ref = rms

        diff = (rms - rms_ref)/rms_ref*100.0

        title = "%s: RMS = %.2f keV" % (channel_name, rms)
        hist.SetTitle(title)
        #print "channel %s | %i entries | rms=%.3f keV | diff=%.2f" % (channel_name, n_entries, rms, diff)
        print "rms_keV[%i] = %.5f" % (channel, rms)
        canvas.Update()
        canvas.Print("rms_%s.pdf" % channel_name)
        if not gROOT.IsBatch(): 
            val = raw_input("enter to continue (q to quit) ")
            if val == 'q': sys.exit()



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)



