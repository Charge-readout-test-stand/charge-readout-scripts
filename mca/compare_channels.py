import ROOT
import numpy as np
import matplotlib.pyplot as plt

import convertMCA

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


colors = [ROOT.kBlue, ROOT.kGreen+2, ROOT.kRed, ROOT.kBlack, ROOT.kMagenta, ROOT.kOrange]

nbins = 8192
ch_hi = 8192

rebin = 16

def make_plots(files, names, my_calibs):
    c1 = ROOT.TCanvas("c1")
    c1.SetLogy(1)

    leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)

    hist_list = []   
    livetime = []
    bin_widths = []

    for f,cal,c,n in zip(files, my_calibs, colors, names):
        hist_hold, lvtime = convertMCA.getMCAhist(f)
        livetime.append(lvtime)
        hist_hold.Scale(livetime[0]/lvtime)
        hist_hold.SetLineColor(c)
        hist_hold.SetLineWidth(2)
        hist_hold.Rebin(rebin)
        leg.AddEntry(hist_hold, n)
        hist_hold.GetXaxis().SetLimits(0,ch_hi*cal)
        bin_widths.append(hist_hold.GetBinWidth(0))
        print hist_hold.GetBinWidth(0), bin_widths[0]/hist_hold.GetBinWidth(0)
        hist_hold.Scale(bin_widths[0]/hist_hold.GetBinWidth(0))
        hist_list.append(hist_hold)
    

    hist_list[0].GetXaxis().SetTitle("Energy [keV]")
    hist_list[0].GetYaxis().SetTitle("Counts")
    hist_list[0].SetTitle("Bi207 Spectrum For 3 Channels (588 V/cm)")
    hist_list[0].SetMaximum(3e3)
    hist_list[0].GetXaxis().SetRangeUser(0,3000)
    #hist_list[0].GetXaxis().SetRangeUser(300,900)
    #hist_list[0].SetMaximum(1000)
    hist_list[0].Draw()

    for h in hist_list[1:]:
        h.Draw("same")

    leg.SetFillColor(0)
    leg.Draw()
    c1.SetGrid(1,1)

    c1.Update()

    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/Data_Bi207_Compare_Channels.png")
    raw_input()


if __name__ == "__main__":
    
    #if len(sys.argv) < 2:
    #    print "arguments: [sis root files]"
    #    sys.exit(1)
 

    files = ["/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA/LXe_10V_point2perThreshold_cathConnected_1000VnegBiasX27_Bi207.mca",
                "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA/LXe_10V_point2perThreshold_cathConnected_1000VnegBiasX28_Bi207.mca",
                "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA/LXe_10V_point2perThreshold_cathConnected_1000VnegBiasX29_Bi207.mca"]
    
    names = ["X27", "X28", "X29"]
    my_calibs = [0.861, 1.22, 0.66]
    
    make_plots(files, names, my_calibs)




