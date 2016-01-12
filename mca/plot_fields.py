import ROOT
import numpy as np
import matplotlib.pyplot as plt

import convertMCA

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)


files = ["LXe_10V_point2perThreshold_cathConnected_300VnegBias.mca",
         "LXe_10V_point2perThreshold_cathConnected_652VnegBiasX27_207Bi.mca",
         "LXe_10V_point2perThreshold_cathConnected_1000VnegBiasX27_Bi207.mca",                      
         "LXe_10V_point2perThreshold_cathConnected_1700VnegBiasX27_Bi207.mca",                      
         "LXe_10V_point2perThreshold_cathConnected_2000VnegBiasX27_Bi207.mca",
         "LXe_10V_point2perThreshold_cathConnected_2500VnegBiasX27_Bi207.mca",
         "LXe_10V_point2perThreshold_cathConnected_3000VnegBiasX27_Bi207.mca"]

livetime = [588.270000, 1361.841000, 1203.631000, 589.276000, 611.904000,  615.984000, 559.539000]

live_scale = [1.0, livetime[0]/livetime[1], livetime[0]/livetime[2], livetime[0]/livetime[3], livetime[0]/livetime[4], livetime[0]/livetime[5], livetime[0]/livetime[6]]

name = ["300V", "652V", "1000V", "1700V", "2000V", "2500V", "3000V"]


nbins = 8192
ch_hi = 8192

hist_list = []

for f,s in zip(files, live_scale):
    hist_hold = convertMCA.getMCAhist("../MCA/" + f)
    hist_hold.Scale(s)
    hist_list.append(hist_hold)


MC_file = ROOT.TFile("MC_smeared_better.root")
MC_smear = MC_file.Get("hist")


c1 = ROOT.TCanvas("c1")
c1.SetLogy()

hist_list[0].SetLineColor(ROOT.kBlue)
hist_list[0].SetFillColor(ROOT.kBlue)
hist_list[0].SetFillStyle(3004)

hist_list[1].SetLineColor(ROOT.kGreen)
hist_list[1].SetFillColor(ROOT.kGreen)
hist_list[1].SetFillStyle(3004)

hist_list[2].SetLineColor(ROOT.kRed)
hist_list[2].SetFillColor(ROOT.kRed)
hist_list[2].SetFillStyle(3004)

hist_list[3].SetLineColor(ROOT.kPink)
hist_list[3].SetFillColor(ROOT.kPink)
hist_list[3].SetFillStyle(3004)

hist_list[4].SetLineColor(ROOT.kBlack)
hist_list[4].SetFillColor(ROOT.kBlack)
hist_list[4].SetFillStyle(3004)

hist_list[5].SetLineColor(ROOT.kYellow)
hist_list[5].SetFillColor(ROOT.kYellow)
hist_list[5].SetFillStyle(3004)

hist_list[6].SetLineColor(ROOT.kOrange)
hist_list[6].SetFillColor(ROOT.kOrange)
hist_list[6].SetFillStyle(3004)

rebin = 8
hist_list[0].Rebin(rebin)
hist_list[1].Rebin(rebin)
hist_list[2].Rebin(rebin)
hist_list[3].Rebin(rebin)
hist_list[4].Rebin(rebin)
hist_list[5].Rebin(rebin)
hist_list[6].Rebin(rebin)
#print "Rebin so now there are",  full_hist.GetNbinsX(), "bins in data"

#full_hist.GetXaxis().SetTitle("ADC Channel")
hist_list[0].GetXaxis().SetTitle("ADC Unit")
hist_list[0].GetYaxis().SetTitle("Counts/8 ADC Units")
hist_list[0].SetTitle("Bi207 Spectrum Changing Field Data vs MC")

#MC_smear.SetLineColor(ROOT.kRed)
#MC_smear.SetFillColor(ROOT.kRed)
#MC_smear.SetFillStyle(3004)
#MC_smear.Scale(norm_factor)

#Just make the peak at 560keV the same height??
#MC_smear.Scale(10.0)

leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)
leg.AddEntry(hist_list[0], name[0])
leg.AddEntry(hist_list[1], name[1])
leg.AddEntry(hist_list[2], name[2])
leg.AddEntry(hist_list[3], name[3])
leg.AddEntry(hist_list[4], name[4])
leg.AddEntry(hist_list[5], name[5])
leg.AddEntry(hist_list[6], name[6])

#leg.AddEntry(MC_smear,  "MC Smeared (28keV)")



#print "MC bins ", MC_smear.GetNbinsX()
#print "MC range", MC_smear.GetXaxis().GetXmax(), MC_smear.GetXaxis().GetXmin()


hist_list[0].GetXaxis().SetRangeUser(0,3000)
#full_hist.GetXaxis().SetRangeUser(500,600)


#hist_list[1].GetXaxis().SetLimits(0,ch_hi*1.4)
#hist_list[2].GetXaxis().SetLimits(0,ch_hi*.82)


#print hist_list[0].GetNbinsX(),  hist_list[0].GetXaxis().GetXmax(), hist_list[0].GetXaxis().GetXmin(), (hist_list[0].GetXaxis().GetXmax() -  hist_list[0].GetXaxis().GetXmin())/hist_list[0].GetNbinsX()

#print hist_list[1].GetNbinsX(),  hist_list[1].GetXaxis().GetXmax(), hist_list[1].GetXaxis().GetXmin(), (hist_list[1].GetXaxis().GetXmax() -  hist_list[1].GetXaxis().GetXmin())/hist_list[1].GetNbinsX()

#print hist_list[2].GetNbinsX(),  hist_list[2].GetXaxis().GetXmax(), hist_list[2].GetXaxis().GetXmin(), (hist_list[2].GetXaxis().GetXmax() -  hist_list[2].GetXaxis().GetXmin())/hist_list[2].GetNbinsX()

#X27_binwidth = (hist_list[0].GetXaxis().GetXmax() -  hist_list[0].GetXaxis().GetXmin())/hist_list[0].GetNbinsX()
#X28_binwidth = (hist_list[1].GetXaxis().GetXmax() -  hist_list[1].GetXaxis().GetXmin())/hist_list[1].GetNbinsX()
#X29_binwidth = (hist_list[2].GetXaxis().GetXmax() -  hist_list[2].GetXaxis().GetXmin())/hist_list[2].GetNbinsX()

#print X27_binwidth/X28_binwidth, X27_binwidth/X29_binwidth

#hist_list[1].Scale(X27_binwidth/X28_binwidth)
#hist_list[2].Scale(X27_binwidth/X29_binwidth)


hist_list[0].Draw()
hist_list[1].Draw("same")
hist_list[2].Draw("same")
hist_list[3].Draw("same")
hist_list[4].Draw("same")
hist_list[5].Draw("same")
hist_list[6].Draw("same")
#MC_smear.Draw("same")

#leg.SetTextSize(0.03)
leg.SetFillColor(0)
leg.Draw()

print hist_list[0].Integral(hist_list[0].FindBin(3000), hist_list[0].FindBin(8192))
print hist_list[1].Integral(hist_list[1].FindBin(3000), hist_list[1].FindBin(8192))
print hist_list[2].Integral(hist_list[2].FindBin(3000), hist_list[2].FindBin(8192))


c1.Update()

c1.Print("../plots/MC_vs_Data_Bi207_Efields.png")
raw_input()




