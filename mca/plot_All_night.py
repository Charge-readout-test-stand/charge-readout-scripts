import ROOT
import numpy as np
import matplotlib.pyplot as plt

import convertMCA

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


files = ["LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_12_02am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_1_01am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_2_00am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_3_03am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_3_52am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_4_46am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_5_31am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_6_12am.mca",
        "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207_7_630am.mca"]


livetime = [3142.366000,3289.616000, 3294.919000, 3546.430000, 2715.598000, 3022.203000, 2545.148000, 2273.879000, 1483.159000]

total_seconds_data = 0.0

for time in livetime:
    total_seconds_data += time

print total_seconds_data

MC_time = 600

norm_factor = total_seconds_data/MC_time

nbins = 8192
ch_hi = 8192

full_hist = ROOT.TH1D("full_hist", "full_hist", nbins, 0, ch_hi)

hist_list = []

for f in files:
    hist_hold = convertMCA.getMCAhist("../MCA_overnight/" + f)
    hist_list.append(hist_hold)
    full_hist.Add(hist_hold)


#MC_file = ROOT.TFile("MC_smeared_test.root")
MC_file = ROOT.TFile("MC_smeared_notConst.root")
#MC_file = ROOT.TFile("MC_smeared.root")
MC_smear = MC_file.Get("hist")


c1 = ROOT.TCanvas("c1")
c1.SetLogy()

full_hist.SetLineColor(ROOT.kBlue)
full_hist.SetFillColor(ROOT.kBlue)
full_hist.SetFillStyle(3004)

full_hist.Rebin(8)
print "Rebin so now there are",  full_hist.GetNbinsX(), "bins in data"

#full_hist.GetXaxis().SetTitle("ADC Channel")
full_hist.GetXaxis().SetTitle("Energy[keV]")
full_hist.GetYaxis().SetTitle("Counts/6keV")
full_hist.SetTitle("Bi207 Spectrum at 1kV/cm Drift Field Data vs MC")

MC_smear.SetLineColor(ROOT.kRed)
MC_smear.SetFillColor(ROOT.kRed)
MC_smear.SetFillStyle(3004)
#MC_smear.Scale(norm_factor)

#Just make the peak at 560keV the same height??
MC_smear.Scale(14.0)

leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)
leg.AddEntry(full_hist, "Data")
leg.AddEntry(MC_smear,  "MC Smearing Energy Dependent")


full_hist.GetXaxis().SetLimits(0,ch_hi*.75)
print "Scaled ADC now the energy range is ", full_hist.GetXaxis().GetXmax(), full_hist.GetXaxis().GetXmin()

print "MC bins ", MC_smear.GetNbinsX()
print "MC range", MC_smear.GetXaxis().GetXmax(), MC_smear.GetXaxis().GetXmin()


#full_hist.GetXaxis().SetRangeUser(0,8000)
#full_hist.GetXaxis().SetRangeUser(500,600)

print full_hist.FindBin(3000), full_hist.FindBin(6000)
print full_hist.Integral(full_hist.FindBin(3000), full_hist.FindBin(6000))

full_hist.Draw()
MC_smear.Draw("same")

#leg.SetTextSize(0.03)
leg.SetFillColor(0)
leg.Draw()



c1.Update()

c1.Print("../plots/MC_vs_Data_Bi207_TotalSpec.png")


full_hist.GetXaxis().SetRangeUser(0,3000)
c1.Update()
c1.Print("../plots/MC_vs_Data_Bi207_3MeV.png")



raw_input()



c2 = ROOT.TCanvas("c2")
c2.SetLogy()
hist_list[7].Scale(livetime[0]/livetime[6])

leg2 = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)

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

hist_list[0].GetXaxis().SetRangeUser(0,4000)
hist_list[0].SetTitle("Bi207 Overnight Runs (1st vs Last)")
hist_list[0].GetXaxis().SetTitle("ADC Units")
hist_list[0].GetYaxis().SetTitle("Counts/8 ADC Units")


hist_list[0].Draw()
hist_list[7].Draw("same")

leg2.SetFillColor(0)
leg2.Draw()


c2.Update()

c2.Print("../plots/MC_vs_Data_Bi207_first_vs_last_night.png")

raw_input()


