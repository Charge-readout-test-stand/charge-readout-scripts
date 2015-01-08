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
from ROOT import TF1


def process_file(filename):

    # this value was pasted from the LN consumption tab of "LXe test stand notes"
    # https://docs.google.com/spreadsheet/ccc?key=0AqZsfZ_WMNNNdEJ3N2hiY3RIRHlpOFcwbExvaG9fR0E#gid=4
    thermal_mass = 110892.74 # [J/K] this is the sum over all components

    print "--> processing file:", filename

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

    print "run duration: %.2f seconds" % (last_timestamp - first_timestamp)


    canvas = TCanvas("canvas","")

    # draw one temperature vs. time -- using hack TTree::Draw() method
    tree.Draw("tCellTop:timeStamp-%s" % first_timestamp,"","pl")
    tree.SetLineColor(TColor.kBlue)

    # draw LN valve status vs time 
    tree.Draw("pLN*tCellTop:timeStamp-%s" % first_timestamp,"","pl same")

    canvas.Update()
    #raw_input("--> press enter to continue")

    # define a fit function
    fit_fcn = TF1(
        "fit_fcn",
        "[0] + ([1]-[0])*exp(-x/[2])", 
        17000.0, # estimate
        last_timestamp - first_timestamp
    )
    fit_fcn.SetLineColor(TColor.kRed)
    fit_fcn.SetParameter(0, 290)
    fit_fcn.SetParameter(1, 170)
    fit_fcn.SetParameter(2, 3600.0*100)
    print fit_fcn.Eval(0)
    print fit_fcn.Eval(last_timestamp-first_timestamp)

    fit_fcn.Draw("same")

    canvas.Update()
    raw_input("--> press enter to continue")
    canvas.Print("fit.pdf")



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [test stand root files]"
        sys.exit(1)

    filename = sys.argv[1]

    process_file(filename)



