'''
This script draws spectrums for two root files on the same pad
The second spectrum is scaled so the maximum is at the same height as that of the first spectrum
The script is intended to compare spectrums from two different runs

The script asks for the channel of interest at the beginning
It runs on tier3 files (needs the branch "energy1_pz")

To run this script:
python /path/to/this/script [sis root file 1] [sis root file 2] 
'''

import os
import sys
import glob
import math

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
from ROOT import TH1D
from ROOT import TGaxis


def process_file(filename1, filename2):

    #print "processing file: ", filename
    #basename = os.path.basename(filename)
    #basename = os.path.splitext(basename)[0]
    #basename = "_".join(basename.split("_")[1:])
    #print basename
    
    n_bins = 500
    max_energy = 2000
    max_energy = 4000

    hist1 = TH1D("spectrum1", "Spectrum", n_bins, 0., max_energy)
    hist2 = TH1D("spectrum2", "Spectrum", n_bins, 0., max_energy)

    channel = input("Which channel: ")

    canvas = TCanvas("canvas","", 1700, 900)
    pad = canvas.cd(1)
    pad.SetGrid(1,1)
    pad.SetLogy()
    legend = TLegend(0.6, 0.75, 0.8, 0.85)
 
    energy_var = "energy1_pz"

    # open file1 and grab the tree
    root_file = TFile(filename1,"READ")
    tree = root_file.Get("tree")

    if channel == 8:
        energy_var = "energy"
        #energy_var = "(wfm_max-wfm[0])"

    selection = "channel==%i" % channel
    selection += "&& %s >100" % energy_var

    hist1.GetDirectory().cd()
    print filename1
    print energy_var
    print selection
    tree.Draw("%s >> %s" % (energy_var, hist1.GetName()), selection)

    # open file2 and grab the tree
    root_file = TFile(filename2,"READ")
    tree = root_file.Get("tree")
    hist2.GetDirectory().cd()
    #energy_var += "*2.5"
    #energy_var = "(wfm[0]-wfm_min)*3"
    print filename2
    print energy_var
    print selection
    tree.Draw("%s >> %s" % (energy_var, hist2.GetName()), selection)

    
    hist1.SetLineWidth(2)
    hist1.SetLineColor(1)
    hist1.GetXaxis().SetTitle("Energy (keV)")
    hist1.GetYaxis().SetTitle("Counts per 8 keV bin")
    hist1.SetStats(0)
    legend.AddEntry(hist1,"File 1: %i events" % (hist1.GetEntries()))
    hist1.Draw()
    canvas.Update()

    #print "Uxmin = ", pad.GetUxmin()
    #print "Uxmax = ", pad.GetUxmax()
    #print "Uymin = ", pad.GetUymin()
    #print "Uymax = ", pad.GetUymax()
     
    
# scale the second histogram
    rightmax = 1.874 * hist2.GetMaximum()
    #print "maximum counts", hist2.GetMaximum()
    #scale = math.pow(10,pad.GetUymax())/rightmax
    #scale = 1.0
    scale = hist1.Integral(hist1.GetXaxis().FindBin(300.),hist1.GetXaxis().FindBin(800.)) / hist2.Integral(hist2.GetXaxis().FindBin(300.),hist2.GetXaxis().FindBin(800.))
    hist2.SetLineWidth(2)
    hist2.SetLineColor(4)
    hist2.Scale(scale)
    legend.AddEntry(hist2,"File 2: %i events" % (hist2.GetEntries()))
    hist2.Draw("same")

#draw an axis on the right side
    axis = TGaxis(pad.GetUxmax(), math.pow(10,pad.GetUymin()), pad.GetUxmax(), math.pow(10,pad.GetUymax()), math.pow(10,pad.GetUymin()), rightmax, 510, "+LG")
    axis.SetLineColor(4)
    axis.SetTextColor(4)
    axis.Draw()

    legend.Draw()
    canvas.Update()
    #canvas.Print("comparison_channel%i.pdf" % (channel))
    #canvas.Print("comparison_channel%i.png" % (channel))
    canvas.Print("comparison.pdf")
    canvas.Print("comparison.png")
    raw_input("Press Enter to continue...")


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print "arguments: [sis root files] [sis root files]"
        sys.exit(1)

    process_file(sys.argv[1], sys.argv[2])

