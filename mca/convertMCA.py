import ROOT
import numpy as np
import matplotlib.pyplot as plt

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


def getMCAhist(file_name):
    #data = np.loadtxt(file_name, skiprows=12)
    data = np.genfromtxt(file_name,skip_header=12, skip_footer=44)
    
    #bin 1 is first and bin nbins is last
    hist = ROOT.TH1D(file_name, file_name, len(data), 0, len(data))

    i = 1
    for d in data:
        hist.SetBinContent(i,d)
        i+=1

    return hist


