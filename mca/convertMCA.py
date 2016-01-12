#!/bin/env python

from ROOT import gROOT
gROOT.SetBatch(True)
import ROOT
import numpy as np
import sys
import os.path
from array import array

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


def getMCAhist(file_name):
    #data = np.loadtxt(file_name, skiprows=12)
    data = np.genfromtxt(file_name,skip_header=12, skip_footer=44)
    
    #bin 1 is first and bin nbins is last
    hist = ROOT.TH1D("hist", file_name, len(data), 0, len(data))

    livetime_line = ""
    file_check = open(file_name)
    for i, line in enumerate(file_check):
        if i==7:
            livetime_line = line 
            break
    file_check.close()

    livetime = 0.0
    for lv in livetime_line.split():
        try:
            livetime = float(lv)
            break
        except:
            continue

    #print livetime

    i = 1
    for d in data:
        hist.SetBinContent(i,d)
        i+=1

    return hist, livetime




if __name__ == "__main__":


    """
    If this script is called from the command line, save a root file
    """
    
    # grab filenames from arguments:
    filenames = sys.argv[1:]

    # if no arguments are provided, print some usage info
    if len(filenames) < 1:
        print "arguments: [mca files]"
        sys.exit(1)

    # loop over all provided MCA files, call  getMCAhist(), and save root output:
    for filename in filenames:

        basename = os.path.basename(filename) # remove path
        print "--> processing", basename
        basename = os.path.splitext(basename)[0] # remove file extension

        outfile = ROOT.TFile("%s.root" % basename, "recreate")
        livetime = array('d', [0]) # double
        tree = ROOT.TTree("tree","livetime data tree")
        tree.Branch('livetime', livetime, 'livetime/D')

        hist, livetime[0] = getMCAhist(filename)

        print "\t livetime: %.2f seconds" % livetime[0]

        print "\t %i entries in hist" % hist.GetEntries()
        hist.SetLineColor(ROOT.TColor.kBlue+1)
        hist.SetFillColor(ROOT.TColor.kBlue+1)
        hist.SetFillStyle(3004)
        hist.Write()

        tree.Fill()
        tree.Write()

        outfile.Close()





