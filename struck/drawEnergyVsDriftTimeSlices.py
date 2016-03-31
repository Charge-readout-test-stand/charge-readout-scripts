
import os
import sys
import glob
import time

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TH2D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gDirectory
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TMath
from ROOT import TTree
from ROOT import TEventList

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
#gStyle.SetPalette(53) # dark body radiator
#gStyle.SetPalette(56) # inverted dark body       
gStyle.SetPalette(51) # deep sea
gStyle.SetPalette(1) # deep sea
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

import struck_analysis_parameters

def process_file(filename):

    # options:
    draw_cmd = "energy1_pz:(rise_time_stop95-trigger_time+0.020)"
    single_strip_cut = struck_analysis_parameters.get_single_strip_cut(10.0)
    selection = []
    selection.append(single_strip_cut)
    selection.append("channel<8")

    print "---> processing", filename
    basename = os.path.splitext(os.path.basename(filename))[0]
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    try:
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
    except AttributeError:
        print "could not get entries from tree"

    print "draw_cmd:", draw_cmd
    selection = "&&".join(selection)
    print "selection:",selection
    print "\n"

    hist = TH2D("hist","",275,0,11,100,300,1300)
    hist.SetXTitle("drift time [#mus]")
    hist.SetYTitle("Energy [keV]")
    hist.GetYaxis().SetTitleOffset(1.3)

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    canvas.SetLogz(1)
    n_entries = tree.Draw(
        "%s >> %s" % (draw_cmd, hist.GetName()), 
        single_strip_cut,
        "colz"
    )
    print "%i entries drawn" % n_entries

    canvas.Update()
    canvas.Print("driftTimeVsEnergy.pdf")
    raw_input("enter... ")


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        sys.exit(1)

    process_file(sys.argv[1])


