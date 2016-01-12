#!/usr/bin/env python

"""
This script estimates the heat leak into the HFE volume

Q = sum( C_p_i * m_i * T )
where:
Q = energy [J]
C_p = specific heat [J/kg-K]
m = mass [kg]
i labels each component (HFE, SS cell, Cu plate)
"""

import os
import sys

from ROOT import gROOT
#gROOT.SetBatch(True) #run in batch mode
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TGraph
from ROOT import TF1
from ROOT import TLegend


def process_file(filename):

    # this value was pasted from the LN consumption tab of "LXe test stand notes"
    # https://docs.google.com/spreadsheet/ccc?key=0AqZsfZ_WMNNNdEJ3N2hiY3RIRHlpOFcwbExvaG9fR0E#gid=4
    thermal_mass = 1.11E+05 # [J/K] this is the sum over all components

    seconds_per_hour = 3600.0

    print "--> processing file:", filename
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    print basename

    # open root file and get the TTree
    root_file = TFile(filename)
    tree = root_file.Get("tree") 
    n_entries = tree.GetEntries()
    print "%i entries in tree" % n_entries

    # find the first time stamp in the root file:
    tree.GetEntry(0)
    first_timestamp = tree.timeStamp
    print "first_timestamp:", first_timestamp

    # find the last time stamp in the root file:
    tree.GetEntry(n_entries-1)
    last_timestamp = tree.timeStamp
    print "last_timestamp:", last_timestamp

    run_duration = (last_timestamp - first_timestamp)/seconds_per_hour
    print "run duration: %.2f hours" % run_duration

    # find the last instance of cooling with LN:
    # FIXME


    # make TGraph from TTree
    graph = TGraph()
    for i in xrange(n_entries):
        tree.GetEntry(i)

        # add data point to the graph
        graph.SetPoint(
            i, 
            (tree.timeStamp - first_timestamp)/seconds_per_hour,
            tree.tCellBot
        )

    canvas = TCanvas("canvas","")

    # draw graph of temp vs. time
    #graph.SetLineColor(TColor.kGreen+1)
    #graph.SetLineWidth(2)
    graph.Draw("apl")

    # draw LN valve status vs time 
    tree.SetLineColor(TColor.kBlue)
    tree.Draw("pLN*tCellTop:(timeStamp-%s)/%s" % (first_timestamp, seconds_per_hour),"","pl same")

    # draw heater status vs time 
    tree.SetLineColor(TColor.kRed+1)
    tree.Draw("heat*tCellTop:(timeStamp-%s)/%s" % (first_timestamp, seconds_per_hour),"","pl same")

    canvas.Update()
    #raw_input("--> press enter to continue")

    fit_start = 17e3/3600
    fit_start = 21e3/3600
    fit_start = 0.0
    fit_stop = run_duration #- 25.0

    # define a fit function
    fit_fcn = TF1(
        "fit_fcn",
        #"[0] + ([1]-[0])*exp(-x/[2])", 
        "pol8(0)",
        fit_start,
        fit_stop
    )
    fit_fcn.SetLineColor(TColor.kRed)

    # estimate some initial parameters -- for exp fit_fcn
    #fit_fcn.SetParameter(0, 290)
    #fit_fcn.SetParameter(1, 170)
    #fit_fcn.SetParameter(2, 3600.0*100)
    #print "initial fit_fcn value at fit start:", fit_fcn.Eval(fit_start)
    #print "itniial fit_fcn value at fit end:", fit_fcn.Eval(fit_stop)

    #fit_fcn.Draw("same")
    #canvas.Update()
    #raw_input("--> press enter to continue")

    # perform the fit
    # options:
    # R = Use the Range specified in the function range
    # N = Do not store the graphics function, do not draw
    graph.Fit(fit_fcn, "R N")

    # label axes
    graph.Draw("apl")
    frame_hist = graph.GetHistogram()
    frame_hist.SetXTitle("Time [hours]")
    frame_hist.SetYTitle("Temperature [K]")

    # make a legend
    legend = TLegend(0.1, 0.93, 0.9, 0.97)
    legend.SetFillColor(0)
    legend.AddEntry(graph, "cell top temperature", "l")
    legend.AddEntry(fit_fcn, "fit curve", "l")
    legend.AddEntry(tree, "LN cooling", "l")
    legend.SetNColumns(3)


    # draw the result
    frame_hist.Draw()
    fit_fcn.Draw("same")
    graph.Draw("pl")
    legend.Draw()
    tree.SetLineColor(TColor.kBlue)
    tree.Draw("pLN*tCellTop:(timeStamp-%s)/%s" % (first_timestamp, seconds_per_hour),"","pl same")
    canvas.Print("warmupFit_%s.pdf" % basename)

    canvas.Update()
    raw_input("--> press enter to continue")

    energy_leak = TF1("energy_leak","fit_fcn*%s" % (thermal_mass/seconds_per_hour), fit_start, fit_stop)
    energy_leak.SetLineWidth(1)
    energy_leak.SetLineColor(TColor.kBlue+1)
    #energy_leak.Draw("")
    energy_leak.DrawDerivative()
    canvas.Update()
    raw_input("--> press enter to continue")
    canvas.Print("heatLeak_%s.pdf" % basename)

    print "dT/dt at fit start: %.2f [K/hour]" % (
        fit_fcn.Derivative(fit_start),
    )
    print "dT/dt at fit stop: %.2f [K/hour]" % (
        fit_fcn.Derivative(fit_stop),
    )

    print "heat leak at fit start [W]: %.3f" % (
        fit_fcn.Derivative(fit_start)*thermal_mass/seconds_per_hour
    )
    #print "heat leak at fit stop [W]:", fit_fcn.Derivative(fit_stop)*thermal_mass
    print fit_fcn.Derivative(10)*thermal_mass/seconds_per_hour


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [test stand root files]"
        sys.exit(1)

    filename = sys.argv[1]

    process_file(filename)



