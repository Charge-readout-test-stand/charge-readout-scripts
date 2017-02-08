"""
Compare results of differen fits. 
Arguments: json files
"""

import os
import sys
import json


import ROOT
ROOT.gROOT.SetBatch(True) # run in batch mode

import struck_analysis_parameters


def add_point_to_graph(results, graph):
    #key = graph.GetHistogram().GetYaxis().GetTitle()
    key = graph.GetTitle()
    i = graph.GetN()
    try:
        value = float(results[key])
    except KeyError:
        if key == "do_use_exp":
            value = 1.0
        elif key == "step_height":
            value = 0.0
        elif key == "do_use_step":
            try:
                results["step_height"]
                value=1.0
            except KeyError:
                value = 0.0
        else:
            print "no key", key
            
    graph.SetPoint(i, i+1, value)
    print "\t %s" % key
    try:
        error = float(results["%s_err" % key])
    except KeyError:
        print "\t\t %s_err not found" % key
        error = 0.0
    graph.SetPointError(i, 0.0, error)
    print "\t\t %s %i: %s +/- %s" % (
        key,
        i,
        value, 
        error
    )

def get_graph(key, color=ROOT.kBlue):
    graph = ROOT.TGraphErrors()
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
    graphs.append(get_graph("centroid", ROOT.kBlue))
    graphs.append(get_graph("sigma", ROOT.kBlue))
    graphs.append(get_graph("sigma_over_E", ROOT.kBlue))
    graphs.append(get_graph("red_chi2", ROOT.kBlue))
    graphs.append(get_graph("ndf", ROOT.kBlue))
    graphs.append(get_graph("peak_counts", ROOT.kBlue))
    graphs.append(get_graph("fit_start_energy", ROOT.kBlue))
    graphs.append(get_graph("fit_stop_energy", ROOT.kBlue))
    graphs.append(get_graph("fit_status", ROOT.kBlue))
    graphs.append(get_graph("integral_counts", ROOT.kBlue))
    graphs.append(get_graph("do_use_exp", ROOT.kBlue))
    graphs.append(get_graph("do_use_step", ROOT.kBlue))
    graphs.append(get_graph("ratio", ROOT.kBlue))

    # remove bad files from list
    print "%i files" % len(filenames)
    bad_files = []
    for i,filename in enumerate(filenames):

        json_file = file(filename,'r')
        results = json.load(json_file)["all"] 

        print "--> checking for bad file", i, filename
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
        print "---> %i of %i" % (i, len(filenames)), filename
        #print "\t", draw_cmd
        #print "\t", selection
        
        # two label schemes:
        if True:
            label = "%i to %i" % (
                float(results["fit_start_energy"]), 
                float(results["fit_stop_energy"]),
            )
            try:
                results["step_height"]
                label += " step"
            except:
                pass
            try:
                val = results["do_use_exp"]
                #print "exp val", val
                if val: label += " exp"
            except:
                label += " exp"
                
        else:
            try:
                label = results["cuts_label"]
            except:
                label = struck_analysis_cuts.get_cuts_label(draw_cmd, selection)
            print "\t", label

        for graph in graphs:
            hist = graph.GetHistogram()
            hist.GetXaxis().SetBinLabel(hist.FindBin(i+1), label)
            #print graph.GetHistogram().GetNbinsX()

        print "label:", label

    # draw the hists:
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetBottomMargin(0.3)
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

        if not ROOT.gROOT.IsBatch():
            val = raw_input("any key to continue (q to quit) ")
            if val == 'q':
                return


if __name__ == "__main__":

    
    if len(sys.argv) < 2:
        print "argument: [json files of fit results]"
        sys.exit(1)

    filenames = sys.argv[1:]
    print "%i files" % len(filenames)
    filenames.sort()
    main(filenames)

