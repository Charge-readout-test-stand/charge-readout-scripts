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


