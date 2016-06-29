"""
this isn't a fit yet; just drawing different curves and comparing.
"""

import os
import sys
import json
import math

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TTree
from ROOT import TGraphErrors
from ROOT import TGraph
from ROOT import TF1
from ROOT import TH1D

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(51) # deep sea
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

import struck_analysis_parameters
#gROOT.ProcessLine('.L ralphWF.C+')
gROOT.ProcessLine('.L ../mc/digi/ralphWF.C+')
from ROOT import FinalAmplitude

def make_graph(
    original_graph, # original graph to clone
    y_max, # y scaling
    tau=None # electron lifetime, microseconds
):
    """
    make a new graph from the TGraph calculated from ion and cathode effects
    """
    drift_velocity = struck_analysis_parameters.drift_velocity
    print "drift_velocity", drift_velocity
    drift_length = struck_analysis_parameters.drift_length
    print "drift_length", drift_length
    new_graph = TGraph()
    new_graph.SetLineWidth(2)
    if tau:
        exp_factor = math.exp(-drift_length/drift_velocity/tau)
        y_max = y_max/exp_factor
        print "exp_factor", exp_factor
    print "y_max", y_max
    for i_point in xrange(original_graph.GetN()):
        x = original_graph.GetX()[i_point]
        y = original_graph.GetY()[i_point]
        y *= y_max
        if tau:
            y*=math.exp(-x/drift_velocity/tau)
        #print x, y
        new_graph.SetPoint(i_point, x, y)
    return new_graph


def do_fit(graph):

    test = TF1("test", FinalAmplitude, 1.0, 18.16, 4)
    test.SetLineColor(TColor.kRed)

    # set some variable names:
    test.SetParName(0, "x for PCD 0")
    test.SetParName(1, "y for PCD 0")
    test.SetParName(2, "tau")
    test.SetParName(3, "energy")

    test.FixParameter(0,1.5)
    test.FixParameter(1,0.0)

    # initial guesses:
    test.SetParameter(2, 100.0) # tau
    test.SetParError(2, 20.0) 
    test.SetParameter(3, 570.0) # E
    test.SetParError(3, 20.0) 

        
    canvas = TCanvas("canvas1","")
    canvas.SetGrid(1,1)
    #canvas = TCanvas("canvas1","", 800, 1100)
    #canvas.Divide(1,2)
    #pad1 = canvas.cd(1)
    hist = test.GetHistogram()
    hist.SetXTitle("Drift distance [mm]");
    hist.SetYTitle("Energy [keV]");
    hist.SetTitle("")

    test.Draw() 
    graph.Draw('p')
    hist = graph.GetHistogram()
    hist1 = TH1D("graph_hist","",20,0.5,20.5)
    for i_point in xrange(graph.GetN()):
        x = graph.GetX()[i_point]
        y = graph.GetY()[i_point]
        error_y = graph.GetEY()[i_point]
        i_bin = hist1.FindBin(x)
        hist1.SetBinContent(i_bin, y)
        hist1.SetBinError(i_bin, error_y)
        print i_point, x, hist1.GetBinLowEdge(i_bin), y, error_y
    print hist1.GetNbinsX()
    print hist1.GetBinWidth(1)
    canvas.Update()
    if False and not gROOT.IsBatch(): 
        print "before fit"
        val = raw_input("enter to continue (q to quit) ")
        if val == 'q': sys.exit()

    fit_options = "SNR"
    # fit options:
    # S -- save output to fit_result
    # N -- don't store the fit function graphics with the histogram
    # R -- use fit fcn's range
    # M -- more; look for new minimum 
    #fit_result = graph.Fit(test, fit_options)
    fit_result = hist1.Fit(test, "SNRI")


    print "tau from fit: %.2e +/- %.2e" % (
        test.GetParameter(2),
        test.GetParError(2),
    )
    test.Draw() 
    hist = test.GetHistogram()
    hist.SetXTitle("Drift distance [mm]");
    hist.SetYTitle("Energy [keV]");
    hist.SetTitle("")
    graph.Draw('p')
    canvas.Update()
    canvas.Print("tauFit.pdf")
    if not gROOT.IsBatch(): 
        print "after fit"
        val = raw_input("enter to continue (q to quit) ")
        if val == 'q': sys.exit()




def process_file(filename, fit_results_filename):
    drift_velocity = struck_analysis_parameters.drift_velocity

    # Graph TGraph
    print "---> processing", filename
    root_file = TFile(filename)
    effects_graph = root_file.Get("graphIonAndCathode")
    print "\t %i points in effects_graph" % effects_graph.GetN()

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
        if False:
            print "drift_time %i: %.1f:" % (i, drift_time)
            print "\t centroid", centroid
            print "\t centroid_err", centroid_err
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

    do_fit(graph)

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.AddEntry(graph, "data from 570-keV fits", "pl")
    legend.SetFillColor(0)

    # draw data points
    hist = graph.GetHistogram()
    hist.SetMinimum(450)
    hist.SetMaximum(640)
    hist.SetYTitle("Energy [keV]")
    hist.SetXTitle("Distance from anode [mm]")
    #graph.Draw("ap")

    # draw different electron lifetime curves
    y_max = graph.GetY()[graph.GetN()-1] # final energy
    y_max = 600
    new_graph = make_graph(effects_graph, y_max)
    new_graph.SetLineColor(TColor.kRed)
    new_graph.Draw("al")
    hist1 = new_graph.GetHistogram()
    hist1.SetMinimum(300)
    new_graph.Draw("l")
    legend.AddEntry(new_graph, "ion + cathode effect curve", "l")

    tau = 100.0 # microseconds
    new_graph2 = make_graph(effects_graph, y_max, tau=tau)
    new_graph2.SetLineColor(TColor.kOrange+1)
    new_graph2.Draw("l")
    legend.AddEntry(new_graph2, "ion + cathode effect curve, #tau=%i#mus" % tau, "l")

    tau = 200.0 # microseconds
    new_graph3 = make_graph(effects_graph, y_max, tau=tau)
    new_graph3.SetLineColor(TColor.kGreen+2)
    new_graph3.Draw("l")
    legend.AddEntry(new_graph3, "ion + cathode effect curve, #tau=%i#mus" % tau, "l")

    tau = 500.0 # microseconds
    new_graph4 = make_graph(effects_graph, y_max, tau=tau)
    new_graph4.SetLineColor(TColor.kViolet)
    new_graph4.Draw("l")
    legend.AddEntry(new_graph4, "ion + cathode effect curve, #tau=%i#mus" % tau, "l")

    tau = 1000.0 # microseconds
    new_graph5 = make_graph(effects_graph, y_max, tau=tau)
    new_graph5.SetLineColor(TColor.kBlue)
    new_graph5.Draw("l")
    legend.AddEntry(new_graph5, "ion + cathode effect curve, #tau=%ims" % (tau/1e3), "l")


    legend.Draw()
    #graph.Draw("p")
    canvas.Update()
    n_slices = len(fit_results.keys())
    print "%i slices" % n_slices
    plot_name = "e_lifetime_fits_%islices" % n_slices
    canvas.Print("%s.pdf" % plot_name)
    raw_input("enter... ")



if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "using default files"

        #fit_results_file = "fit_results_z_slices_overnight7thLXe_6.txt"
        #fit_results_file = "fit_results_z_slices_overnight7thLXe_10.txt"
        #fit_results_file = "fit_results_z_slices_overnight7thLXe_21.txt"
        fit_results_file = "fit_results_z_slices_overnight7thLXe_19.txt"

        process_file("ionAndCathodeEffect.root", fit_results_file)

    elif len(sys.argv) < 3:
        process_file(sys.argv[1], sys.argv[2])
    else:
        print "arguments: [tier3 root file]"


