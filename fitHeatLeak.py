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


def process_file(filename):

    # this value was pasted from the LN consumption tab of "LXe test stand notes"
    # https://docs.google.com/spreadsheet/ccc?key=0AqZsfZ_WMNNNdEJ3N2hiY3RIRHlpOFcwbExvaG9fR0E#gid=4
    thermal_mass = 110892.74 # [J/K] this is the sum over all components

    print "--> processing file:", filename

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

    run_duration = last_timestamp - first_timestamp
    print "run duration: %.2f seconds" % run_duration

    # find the last instance of cooling with LN:
    # FIXME


    # make TGraph from TTree
    graph = TGraph()
    for i in xrange(n_entries):
        tree.GetEntry(i)

        # add data point to the graph
        graph.SetPoint(
            i, 
            tree.timeStamp - first_timestamp,
            tree.tCellTop
        )

    canvas = TCanvas("canvas","")

    # draw graph of temp vs. time
    graph.SetLineColor(TColor.kGreen+1)
    graph.Draw("apl")

    # draw LN valve status vs time 
    tree.SetLineColor(TColor.kBlue)
    tree.Draw("pLN*tCellTop:timeStamp-%s" % first_timestamp,"","pl same")

    # draw heater status vs time 
    tree.SetLineColor(TColor.kRed+1)
    tree.Draw("heat*tCellTop:timeStamp-%s" % first_timestamp,"","pl same")

    canvas.Update()
    #raw_input("--> press enter to continue")

    est_fit_start = 17e3

    # define a fit function
    fit_fcn = TF1(
        "fit_fcn",
        "[0] + ([1]-[0])*exp(-x/[2])", 
        est_fit_start,
        run_duration
    )
    fit_fcn.SetLineColor(TColor.kRed)

    # estimate some initial parameters
    fit_fcn.SetParameter(0, 290)
    fit_fcn.SetParameter(1, 170)
    fit_fcn.SetParameter(2, 3600.0*100)
    print "initial fit_fcn value at fit start:", fit_fcn.Eval(est_fit_start)
    print "itniial fit_fcn value at fit end:", fit_fcn.Eval(run_duration)

    fit_fcn.Draw("same")

    canvas.Update()
    raw_input("--> press enter to continue")


    # perform the fit
    graph.Fit(fit_fcn, "R")

    # draw the result
    graph.Draw("apl")
    fit_fcn.Draw("same")


    # take derivative of the temperature:
    temp_derivative = TF1(
        "temp_derivative",
        "-([1]-[0])/[2]*exp(-x/[2])",
        est_fit_start,
        run_duration
    )

    # initialize temp_derivative with fit values
    for i_par in xrange(fit_fcn.GetNpar()):

        val = fit_fcn.GetParameter(i_par)
        print "par %i: %.2f" % (i_par, val)
        temp_derivative.SetParameter(i_par, val)

    temp_derivative.Draw()
    canvas.Update()
    raw_input("--> press enter to continue")
    canvas.Print("fit.pdf")

    print "dT/dt at cooling stop: %s [K/s] | %.2f [K/hour]" % (
        temp_derivative.Eval(est_fit_start),
        temp_derivative.Eval(est_fit_start)*3600.0,
    )
    print "dT/dt at run stop: %s [K/s] | %.2f [K/hour]" % (
        temp_derivative.Eval(run_duration),
        temp_derivative.Eval(run_duration)*3600.0,
    )

    print "heat leak at cooling stop [W]:", temp_derivative.Eval(est_fit_start)*thermal_mass
    print "heat leak at run stop [W]:", temp_derivative.Eval(run_duration)*thermal_mass
    print fit_fcn.Derivative(est_fit_start)*thermal_mass
    print fit_fcn.Derivative(run_duration)*thermal_mass


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [test stand root files]"
        sys.exit(1)

    filename = sys.argv[1]

    process_file(filename)



