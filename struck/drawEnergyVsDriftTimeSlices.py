
import os
import sys
import glob
import json

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH2D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TTree
from ROOT import TGraphErrors

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
#gStyle.SetPalette(53) # dark body radiator
#gStyle.SetPalette(56) # inverted dark body       
gStyle.SetPalette(51) # deep sea
#gStyle.SetPalette(1) # rainbow
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

import struck_analysis_parameters

def process_file(filename, fit_results_filename):

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

    # grab info from json fit results:
    print "--> processing fit results", fit_results_filename
    json_file = file(fit_results_filename,'r')
    fit_results = json.load(json_file) 
    #print json.dumps(fit_results, sort_keys=True, indent=4)
    graph = TGraphErrors()
    graph.SetLineWidth(2)
    for drift_time, values in fit_results.items():
        drift_time = float(drift_time)
        centroid = float(values["centroid"])
        sigma = float(values["sigma"])
        dt = float(values["dt"])
        print "drift_time: %.1f:" % drift_time
        print "\t centroid", centroid
        print "\t sigma", sigma
        print "\t dt", dt
        i_point = graph.GetN()
        graph.SetPoint(i_point,drift_time+dt/2.0, centroid)
        graph.SetPointError(i_point,dt/2.0,sigma)

    # 2D hist for time vs. energy
    hist = TH2D("hist","",275,0,11,100,300,1300)
    hist.SetXTitle("drift time [#mus]")
    hist.SetYTitle("Energy [keV]")
    hist.GetYaxis().SetTitleOffset(1.3)

    # draw stuff
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    canvas.SetLogz(1)
    n_entries = tree.Draw(
        "%s >> %s" % (draw_cmd, hist.GetName()), 
        single_strip_cut,
        "colz"
    )
    print "%i entries drawn" % n_entries
    graph.Draw("p")
    canvas.Update()
    canvas.Print("driftTimeVsEnergy.pdf")
    raw_input("enter... ")



if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "using default files"
        process_file(
            "overnight7thLXe.root",
            #"fit_results_z_slices_overnight7thLXe_6.txt"
            "fit_results_z_slices_overnight7thLXe_10.txt"
        )

    elif len(sys.argv) < 3:
        process_file(sys.argv[1], sys.argv[2])
    else:
        print "arguments: [tier3 root file]"


