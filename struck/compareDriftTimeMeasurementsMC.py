"""
Compare drift times: MC truth vs. different measurements
"""

import os
import sys
import glob

from ROOT import gROOT
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       



def process_file(filename):

    # options
    hist_min = -5
    hist_max = 5
    n_bins = (hist_max - hist_min)*10


    print "processing file: ", filename

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    # legend
    legend = TLegend(0.1, 0.9, 0.9, 0.99)


    rise_time_hist = TH1D("rise_time_hist","", n_bins, hist_min, hist_max)
    rise_time_hist.SetLineWidth(2)
    rise_time_hist.SetXTitle("Measured drift time - MC truth [#mus]")
    rise_time_hist.SetYTitle("Counts / %s #mus" % rise_time_hist.GetBinWidth(1))

    fit_hist = TH1D("fit_hist","", n_bins, hist_min, hist_max)
    fit_hist.SetLineWidth(2)
    fit_hist.SetLineColor(2)

    selection = "(channel==52)" # since we only did fits of this channel
    #selection += "&&(energy>300)"
    print tree.Draw("rise_time95-drift_time_MC >> %s" % rise_time_hist.GetName(), selection)
    legend.AddEntry(
        rise_time_hist, 
        "rise time method: mean = %.2f #mus, #sigma =%.2f #mus" % (
            rise_time_hist.GetMean(),
            rise_time_hist.GetRMS(),
        ), 
        "l"
    )
    print tree.Draw("fit_drift_time-drift_time_MC >> %s" % fit_hist.GetName(), selection, "same")
    legend.AddEntry(
        fit_hist, 
        "fit method: mean = %.2f #mus, #sigma =%.2f #mus" % (
            fit_hist.GetMean(),
            fit_hist.GetRMS(), 
        ),
        "l"
    )
  
    
    legend.Draw()
    basename = os.path.splitext(os.path.basename(filename))[0]
    canvas.Update()
    canvas.Print("drift_time_comparison_%s.pdf" % basename)
    raw_input("enter to continue ")



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)


