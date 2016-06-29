
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
import struck_analysis_cuts

def process_file(filenames, fit_results_filename):
    drift_velocity = struck_analysis_parameters.drift_velocity

    # options:
    do_draw_fit_results = True
    #draw_cmd = "energy1_pz:(rise_time_stop99-trigger_time+0.020)"
    #draw_cmd = "energy1_pz:(rise_time_stop99-trigger_time+0.020)*%s" % drift_velocity
    draw_cmd = "energy1_pz:(rise_time_stop95-trigger_time+0.020)*%s" % drift_velocity

    if fit_results_filename == None:
        do_draw_fit_results = False

    plot_name = "driftDistVsEnergy95"

    if do_draw_fit_results:
        # grab info from json fit results:
        print "--> processing fit results", fit_results_filename
        json_file = file(fit_results_filename,'r')
        fit_results = json.load(json_file) 
        #print json.dumps(fit_results, sort_keys=True, indent=4)
        graph = TGraphErrors()
        graph.SetLineWidth(2)
        keys = fit_results.keys()
        keys.sort()
        for i, drift_time in enumerate(keys):
            values = fit_results[drift_time]
            drift_time = float(drift_time)
            centroid = float(values["centroid"])
            centroid_err = float(values["centroid_err"])
            sigma = float(values["sigma"])
            fit_status = int(values["fit_status"])
            dt = float(values["dt"])
            dz = dt*drift_velocity
            z=drift_time*drift_velocity
            print "drift_time %i: %.1f:" % (i, drift_time)
            print "\t centroid", centroid
            print "\t sigma", sigma
            print "\t dt", dt
            print "\t dz", dz
            print "\t z", z
            print "\t fit_status", fit_status
            if fit_status != 0:
                print "BAD FIT!"
            #    continue
            i_point = graph.GetN()
            graph.SetPoint(i_point,z+dz/2.0, centroid)
            #graph.SetPointError(i_point,dz/2.0,sigma)
            graph.SetPointError(i_point,dz/2.0,centroid_err)

    # 2D hist for time vs. energy
    hist = TH2D("hist","",275,0,11*drift_velocity,100,300,1300)
    #hist.SetXTitle("drift time [#mus]")
    hist.SetXTitle("distance from anode [mm]")
    hist.SetYTitle("Energy [keV]")
    hist.GetYaxis().SetTitleOffset(1.3)


    basename = os.path.splitext(os.path.basename(filenames[0]))[0]
    print basename


    for i_file, filename in enumerate(filenames):
        print "---> processing", filename
        root_file = TFile(filename)
        tree = root_file.Get("tree")
        try:
            n_entries = tree.GetEntries()
            print "%i entries, file %i of %i" % (n_entries, i_file, len(filenames))
            isMC = struck_analysis_parameters.is_tree_MC(tree)
        except AttributeError:
            print "could not get entries from tree"
            continue

        # selections (these go in the loop so isMC can be set):
        single_strip_cut = struck_analysis_cuts.get_single_strip_cut(10.0, isMC)
        selection = []
        selection.append(single_strip_cut)
        selection.append(struck_analysis_cuts.get_channel_selection(isMC))
        #selection.append("Entry$<1e5") # debugging
        selection = "&&".join(selection)



        print "draw cmd:", "%s >>+ %s" % (draw_cmd, hist.GetName())
        print "selection:", selection

        # draw 2D hist
        hist.GetDirectory().cd()
        n_entries = tree.Draw(
            "%s >>+ %s" % (draw_cmd, hist.GetName()), 
            #single_strip_cut,
            selection,
            "goff"
        )
        print "\t %i entries drawn; %i entries in hist" % (n_entries, hist.GetEntries())


    print "isMC:", isMC
    print "draw_cmd:", draw_cmd
    print "selection:",selection
    print "hist entries", hist.GetEntries()
    print "\n"


    plot_name = basename + plot_name
    canvas = TCanvas("canvas","")
    hist.Draw("colz")
    canvas.SetGrid(1,1)
    canvas.SetLogz(1)
    canvas.Update()
    canvas.Print("%s.pdf" % plot_name)
    canvas.Print("%s.png" % plot_name)
    print "%i hist entries drawn" % n_entries
    if not gROOT.IsBatch():
        raw_input("pause")

    if do_draw_fit_results:
        # draw graph over hist
        graph.Draw("p")
        canvas.Update()
        n_slices = len(fit_results.keys())
        print "%i slices" % n_slices
        plot_name = "%s_%islices" % (plot_name, n_slices)
        canvas.Print("%s.pdf" % plot_name)
        canvas.Print("%s.png" % plot_name)
        if not gROOT.IsBatch():
            raw_input("enter... ")



if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "using default files"

        #fit_results_file = "fit_results_z_slices_overnight7thLXe_6.txt"
        #fit_results_file = "fit_results_z_slices_overnight7thLXe_10.txt"
        #fit_results_file = "fit_results_z_slices_overnight7thLXe_21.txt"
        fit_results_file = "fit_results_z_slices_overnight7thLXe_19.txt"

        data_file = "overnight7thLXe.root"
        #data_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/mc/Bi207_Full_Ralph_dcoeff50/tier3/all.root"


        process_file([data_file], fit_results_file)

    elif len(sys.argv) == 2:
        process_file([sys.argv[1]], None)
    elif len(sys.argv) == 3:
        process_file([sys.argv[1]], sys.argv[2])
    elif len(sys.argv) >= 3: # a hack to try to generalized to MC
        process_file(sys.argv[1:], None)
    else:
        print "arguments: [tier3 root file] [fit results]"


