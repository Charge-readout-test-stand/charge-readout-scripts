import ROOT
import sys
import os
import struck_analysis_parameters
import numpy as np


tier3_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/overnight152.root"

#tier3_file = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2016_03_07_7thLXe/tier3_external/tier3_overnight_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03-08_10-08-33.root"


num_charge_channels = 8
ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetTitleStyle(0)
ROOT.gStyle.SetTitleBorderSize(0)
c1 = ROOT.TCanvas()
c1.SetGrid(1,1)
c1.SetLogy()
color_list = [ROOT.kRed, ROOT.kGreen, ROOT.kBlue, ROOT.kBlack, ROOT.kTeal, ROOT.kOrange, ROOT.kPink, ROOT.kMagenta, ROOT.kCyan+1]
name_list = ["X16", "X17", "X18", "X19", "Y16", "Y17", "Y18", "Y19"]




def CompareChannels(fname):
    tfile = ROOT.TFile(fname)

    tree = tfile.Get("tree")
    numEvents = tree.GetEntries()
    
    bins = 1000
    cE_h = 0.0
    cE_l = 10000.0

    hist_list = []
    maxes = []
    legend = ROOT.TLegend(0.1, 0.86, 0.9, 0.99)
    legend.SetNColumns(3)
    for i in np.arange(num_charge_channels):
        draw_cmd = "energy1_pz>>h(%i, %f, %f)" % (bins, cE_h, cE_l)
        cut = "channel==%i" % i
        tree.Draw(draw_cmd, cut, "goff")
        hist = ROOT.gDirectory.Get("h")
        hist.SetDirectory(0)
        hist.SetLineColor(color_list[i])
        hist_list.append(hist)
        maxes.append(hist.GetMaximum())
    
    for i, hist in enumerate(hist_list):
        legend.AddEntry(hist, name_list[i])
        if i==0: 
            hist.SetTitle("")
            hist.GetXaxis().SetTitle("Energy[keV]")
            hist.Draw()
        else: hist.Draw("same")
    
    legend.Draw()
    c1.Update()
    c1.Print("channel_Energy_compare.pdf(")
    print "Drawing...."
    
    hist_list[0].GetXaxis().SetRangeUser(0,3000)
    c1.Update()
    c1.Print("channel_Energy_compare.pdf)")
    raw_input("Wait for Input")

    return
if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "Need File Name"
        print "WARNING BYPASSING ARG AND JUST LOOKING AT HARDCODED FILE"
        raw_input()
    else:
        tier3_file = sys.argv[1]
    
    CompareChannels(tier3_file)
    

