import ROOT
import numpy as np
import matplotlib.pyplot as plt

import convertMCA

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


nbins = 8192
ch_hi = 8192

def make_plots(files, my_calib):
    MC_time = 600 #seconds (10 minutes)
    
    full_hist = ROOT.TH1D("full_hist", "full_hist", nbins, 0, ch_hi)
    hist_list = []

    livetime = []
    for f in files:
        hist_hold, lvtime = convertMCA.getMCAhist(f)
        livetime.append(lvtime)
        hist_list.append(hist_hold)
        full_hist.Add(hist_hold)

    print "Total Elapsed Time", np.sum(livetime)/(60*60)

    MC_file = ROOT.TFile("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MC_Data/MC_smeared_notConst.root")
    MC_smear = MC_file.Get("hist")
    MC_smear.SetLineColor(ROOT.kRed)
    MC_smear.SetFillColor(ROOT.kRed)
    MC_smear.SetFillStyle(3004)
    MC_smear.Scale(14.0) #Arbitraty picked to make 570keV peaks match


    c1 = ROOT.TCanvas("c1")
    c1.SetLogy()

    full_hist.SetLineColor(ROOT.kBlue)
    full_hist.SetFillColor(ROOT.kBlue)
    full_hist.SetFillStyle(3004)
    full_hist.Rebin(8)
    full_hist.GetXaxis().SetTitle("Energy[keV]")
    full_hist.GetYaxis().SetTitle("Counts/6keV")
    full_hist.SetTitle("Bi207 Spectrum at 1kV/cm Drift Field")
    full_hist.GetXaxis().SetLimits(0,ch_hi*my_calib)
    full_hist.SetMaximum(8e3)
    full_hist.GetXaxis().SetRangeUser(200,1500)

    leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)
    leg.AddEntry(full_hist, "Data")
    leg.AddEntry(MC_smear,  "MC Smearing Energy Dependent")
    
    print "Scaled ADC now the energy range is ", full_hist.GetXaxis().GetXmin(), full_hist.GetXaxis().GetXmax(), full_hist.GetBinWidth(0)
    print "MC range", MC_smear.GetXaxis().GetXmin(), MC_smear.GetXaxis().GetXmax(), MC_smear.GetBinWidth(0)

    c1.SetGrid(1,1)
    full_hist.Draw()
    c1.SetLogy(0)
    c1.Update()
    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/Data_Bi207_Linear.png")

    raw_input()

    full_hist.SetMaximum(1e5)
    full_hist.GetXaxis().SetRangeUser(0,8000)

    print full_hist.FindBin(3000), full_hist.FindBin(6000)
    print full_hist.Integral(full_hist.FindBin(3000), full_hist.FindBin(6000))

    c1.SetLogy(1)
    c1.Update()
    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/Data_Bi207_TotalSpec.png")

    MC_smear.Draw("same")
    leg.SetFillColor(0)
    leg.Draw()

    full_hist.SetTitle("Bi207 Spectrum at 1kV/cm Drift Field Data vs MC")

    c1.Update()
    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/MC_vs_Data_Bi207_TotalSpec.png")


    full_hist.GetXaxis().SetRangeUser(0,3000)
    c1.Update()
    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/MC_vs_Data_Bi207_3MeV.png")

    raw_input()
 
    c2 = ROOT.TCanvas("c2")
    c2.SetLogy(1)
    c2.SetGrid(1,1)
    hist_list[7].Scale(livetime[0]/livetime[6])

    leg2 = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)

    hist_list[0].GetXaxis().SetLimits(0,ch_hi*my_calib)
    hist_list[7].GetXaxis().SetLimits(0,ch_hi*my_calib)

    hist_list[0].Rebin(8)
    hist_list[7].Rebin(8)

    hist_list[0].SetLineColor(ROOT.kRed)
    hist_list[0].SetFillColor(ROOT.kRed)
    hist_list[0].SetFillStyle(3004)

    hist_list[7].SetLineColor(ROOT.kBlue)
    hist_list[7].SetFillColor(ROOT.kBlue)
    hist_list[7].SetFillStyle(3004)

    leg2.AddEntry(hist_list[0], "First")
    leg2.AddEntry(hist_list[7],  "Last")

    hist_list[0].SetMaximum(4e4)
    hist_list[0].GetXaxis().SetRangeUser(0,4000)
    hist_list[0].SetTitle("Bi207 Overnight Runs (First vs Last)")
    hist_list[0].GetXaxis().SetTitle("Energy [keV]")
    hist_list[0].GetYaxis().SetTitle("Counts/6 keV")


    hist_list[0].Draw()
    hist_list[7].Draw("same")

    leg2.SetFillColor(0)
    leg2.Draw()


    c2.Update()
    c2.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/MC_vs_Data_Bi207_first_vs_last_night.png")

    raw_input()






if __name__ == "__main__":

    #if len(sys.argv) < 2:
    #    print "arguments: [sis root files]"
    #    sys.exit(1)

    files = ["/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_12_02am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_1_01am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_2_00am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_3_03am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_3_52am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_4_46am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_5_31am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_6_12am.mca",
             "/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/MCA_overnight/LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_7_630am.mca"]

    my_calib = 0.75

    make_plots(files, my_calib)










