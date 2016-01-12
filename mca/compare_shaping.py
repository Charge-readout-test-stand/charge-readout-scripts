import ROOT
import numpy as np
import matplotlib.pyplot as plt

import convertMCA

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


name = ["0.5us", "1us", "2us", "3us", "6us", "10us"]

colors = [ROOT.kBlue, ROOT.kGreen+2, ROOT.kRed, ROOT.kBlack, ROOT.kMagenta, ROOT.kOrange]

nbins = 8192
ch_hi = 8192

rebin = 16

def make_plots(files, names, my_calibs):
    c1 = ROOT.TCanvas("c1")
    c1.SetLogy(0)

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
        hist_hold.SetFillColor(c)
        hist_hold.SetFillStyle(3006)
        hist_hold.Rebin(rebin)
        leg.AddEntry(hist_hold, n)
        hist_hold.GetXaxis().SetLimits(0,ch_hi*cal)
        bin_widths.append(hist_hold.GetBinWidth(0))
        print hist_hold.GetBinWidth(0), bin_widths[0]/hist_hold.GetBinWidth(0)
        hist_hold.Scale(bin_widths[0]/hist_hold.GetBinWidth(0))
        #print hist_hold.GetBinWidth(0), hist_hold.GetBinWidth(0)/bin_widths[0]
        #hist_hold.Scale(hist_hold.GetBinWidth(0)/bin_widths[0])
        hist_list.append(hist_hold)
    

    hist_list[0].GetXaxis().SetTitle("Energy[keV]")
    hist_list[0].GetYaxis().SetTitle("Counts/8 ADC Units")
    hist_list[0].SetTitle("Bi207 Spectrum Changing Shaping Time (1kV/cm)")
    hist_list[0].SetMaximum(500)
    hist_list[0].GetXaxis().SetRangeUser(300,1000)


    hist_list[0].Draw()

    for h in hist_list[1:]:
        h.Draw("same")

    leg.SetFillColor(0)
    leg.Draw()
    c1.SetGrid(1,1)

    c1.Update()

    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/Data_Bi207_Compare_Shaping.png")
    raw_input()


if __name__ == "__main__":
    
    #if len(sys.argv) < 2:
    #    print "arguments: [sis root files]"
    #    sys.exit(1)
    
   files = ["/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_AfterRalphFix_and_more_testing_0_5us.mca",
            "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_AfterRalphFix_and_more_testing_1us.mca",
            "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_AfterRalphFix_and_more_testing_2us.mca",
            "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_AfterRalphFix_and_more_testing.mca"]
            #"/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_AfterRalphFix_and_more_testing_3us.mca",
            #"/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_AfterRalphFix_and_more_testing_10us.mca"]

   #names = ["0.5us", "1us", "2us", "3us", "6us", "10us"] 
   #my_calibs = [1.0, 0.8769, 0.8028, 1.0, 0.7808, 1.0]
   names = ["0.5us", "1us", "2us", "6us"]
   my_calibs = [1.0, 0.8769, 0.8028, 0.7808]


   make_plots(files, names, my_calibs)




