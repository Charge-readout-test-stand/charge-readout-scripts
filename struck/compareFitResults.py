
import os
import sys
import json
import math
import datetime


from ROOT import gROOT
# run in batch mode:
gROOT.SetBatch(True)
from ROOT import TFile
from ROOT import TTree
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TH1D
from ROOT import TF1
from ROOT import TGraphErrors
from ROOT import gSystem

import struck_analysis_parameters


def add_point_to_graph(results, graph):
    #key = graph.GetHistogram().GetYaxis().GetTitle()
    key = graph.GetTitle()
    i = graph.GetN()
    value = float(results[key])
    graph.SetPoint(i, i+1, value)
    print key
    try:
        error = float(results["%s_err" % key])
    except KeyError:
        print "%s_err not found" % key
        error = 0.0
    graph.SetPointError(i, 0.0, error)
    print "\t %s %i: %s +/- %s" % (
        key,
        i,
        value, 
        error
    )

def get_graph(key, color=TColor.kBlue):
    graph = TGraphErrors()
    graph.SetTitle(key)
    graph.GetHistogram().SetYTitle(key)
    graph.SetMarkerColor(color)
    graph.SetMarkerStyle(8)
    graph.SetMarkerSize(0.8)
    graph.SetLineColor(color)
    graph.SetLineWidth(2)
    return graph


def main(filenames):

    # set up some graphs to fill:
    graphs = []
    graphs.append(get_graph("centroid", TColor.kBlue))
    graphs.append(get_graph("sigma", TColor.kBlue))
    graphs.append(get_graph("sigma_over_E", TColor.kBlue))
    graphs.append(get_graph("red_chi2", TColor.kBlue))
    graphs.append(get_graph("ndf", TColor.kBlue))
    graphs.append(get_graph("peak_counts", TColor.kBlue))
    graphs.append(get_graph("fit_start_energy", TColor.kBlue))
    graphs.append(get_graph("fit_stop_energy", TColor.kBlue))
    graphs.append(get_graph("fit_status", TColor.kBlue))
    graphs.append(get_graph("integral_counts", TColor.kBlue))

    # remove bad files from list
    print "%i files" % len(filenames)
    bad_files = []
    for i,filename in enumerate(filenames):

        json_file = file(filename,'r')
        results = json.load(json_file)["all"] 

        print "--> processing", i, filename
        # check line_energy
        line_energy = float(results["line_energy"])
        if i == 0:
            line_energy_ref = line_energy
        elif line_energy_ref != line_energy:
            print "\t skipping -- line_energy: %.1f != %.1f" % (
                line_energy,
                line_energy_ref,
            )
            bad_files.append(filename)

    for bad_file in bad_files:
        filenames.remove(bad_file)

    # fill graphs 
    print "%i files" % len(filenames)
    for i,filename in enumerate(filenames):

        print "--> processing", i, filename
        json_file = file(filename,'r')
        results = json.load(json_file)["all"] 
        #print json.dumps(results, sort_keys=True, indent=4)

        for graph in graphs:
            add_point_to_graph(results, graph)

        #return # debugging

    # now that the graphs are full, draw them to get their hists
    for graph in graphs:
        graph.Draw("ap goff")

    # apply descriptive bin labels:
    for i, filename in enumerate(filenames):
        json_file = file(filename,'r')
        results = json.load(json_file)["all"] 
        line_energy = float(results["line_energy"])
        selection = results["selection"]
        draw_cmd = results["draw_cmd"]
        print "--->", filename
        print "\t", draw_cmd
        print "\t", selection
        
        try:
            label = results["cuts_label"]
        except:
            label = struck_analysis_parameters.get_cuts_label(draw_cmd, selection)
        print "\t", label

        for graph in graphs:
            hist = graph.GetHistogram()
            hist.GetXaxis().SetBinLabel(hist.FindBin(i+1), label)
            #print graph.GetHistogram().GetNbinsX()

    # draw the hists:
    canvas = TCanvas("canvas","")
    canvas.SetBottomMargin(0.2)
    canvas.SetLeftMargin(0.15)
    canvas.SetGrid(1,1)
    for graph in graphs:
        key = graph.GetTitle()
        graph.SetTitle("")
        hist = graph.GetHistogram()
        hist.SetYTitle(key)
        hist.GetYaxis().SetTitleOffset(1.3)
        #hist.SetNdivisions(-510, "X")
        #hist.SetNdivisions(-510, "Y")
        #hist.GetXaxis().SetNdivisions(16, 5, 16, False)
        graph.Draw("ap")
        #canvas.SetGrid(1,1)
        canvas.Update()
        canvas.Print("comparison_%i_%s.pdf" % (line_energy, key) )

        if not gROOT.IsBatch():
            val = raw_input("any key to continue (q to quit) ")
            if val == 'q':
                return


if __name__ == "__main__":

    
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        sys.exit(1)

    filenames = sys.argv[1:]
    print "%i files" % len(filenames)
    filenames.sort()
    main(filenames)

