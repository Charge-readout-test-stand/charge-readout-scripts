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

    hist1 = TH1D("spectrum1", "Spectrum", 250, 0., 2000.)
    hist2 = TH1D("spectrum2", "Spectrum", 250, 0., 2000.)

    canvas = TCanvas("canvas","", 1700, 900)

    # open file1 and grab the tree
    root_file = TFile(filename1,"READ")
    tree = root_file.Get("tree")

    channel = input("Which channel: ")

    for i_entry in xrange(tree.GetEntries()):
        tree.GetEntry(i_entry)
        if tree.channel == channel:
            hist1.Fill(tree.energy1_pz)

    # open file2 and grab the tree
    root_file = TFile(filename2,"READ")
    tree = root_file.Get("tree")

    for i_entry in xrange(tree.GetEntries()):
        tree.GetEntry(i_entry)
        if tree.channel == channel:
            hist2.Fill(tree.energy1_pz)

    pad = canvas.cd(1)
    pad.SetGrid(1,1)
    pad.SetLogy()
    legend = TLegend(0.6, 0.75, 0.8, 0.85)
    
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
    scale = math.pow(10,pad.GetUymax())/rightmax
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
    raw_input("Press Enter to continue...")
    



if __name__ == "__main__":

    if len(sys.argv) != 3:
        print "arguments: [sis root files] [sis root files]"
        sys.exit(1)

    process_file(sys.argv[1], sys.argv[2])

