import ROOT
import numpy as np
import matplotlib.pyplot as plt

import convertMCA

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)

nbins = 8192 #Bins in MCA
ch_hi = 8192 #High bin in MCA

def gaus_peak(x,a, b, c):
    return a*np.exp(-(x-b)**2/(2*c))

def background(x,a, b, c):
    return a + b*x + c*x**2

class FitFunc:
    def __call__(self,x,par):
        #print x[0], x[1], x[2], x[3]
        return background(x[0],par[0], par[1], par[2]) + gaus_peak(x[0],par[3], par[4], par[5])

def calibrate(hist, calib):
    print "Using Fit Calibration of: ", calib
    full_hist.GetXaxis().SetLimits(0,ch_hi*calib)
    full_hist.GetXaxis().SetTitle("Energy[keV]")
    full_hist.GetYaxis().SetTitle("Counts/"+str(int(full_hist.GetBinWidth(0)))+" keV")    
    print "Scaled ADC now the energy range is ", full_hist.GetXaxis().GetXmin(), full_hist.GetXaxis().GetXmax()
    

def get_full_hist(files):   
    
    full_hist = ROOT.TH1D("full_hist", "full_hist", nbins, 0, ch_hi)

    hist_list = []

    test_time = []
    for f in files:
        hist_hold, lvtime = convertMCA.getMCAhist(f)
        hist_list.append(hist_hold)
        full_hist.Add(hist_hold)
        test_time.append(lvtime)
 
    print "Bin content =", full_hist.GetBinContent(300), full_hist.GetBinContent(300)**0.5
    print "Is there Bin Error", full_hist.GetBinError(300)

    test_time = np.array(test_time)
    print "Total data taken for ", np.sum(test_time)/(60*60), " hours"

    c1 = ROOT.TCanvas("c1")

    full_hist.SetLineColor(ROOT.kBlue)
    full_hist.SetFillColor(ROOT.kBlue)
    full_hist.SetFillStyle(3004)

    full_hist.Rebin(8)

    full_hist.GetXaxis().SetTitle("ADC Units")
    full_hist.SetTitle("Bi207 Spectrum at 1kV/cm Drift Field")

    print "After Rebinning by 8 and calibrating the Bin Width is...",  full_hist.GetBinWidth(0)
    
    bin_wid = int(full_hist.GetBinWidth(0))
    full_hist.GetYaxis().SetTitle("Counts/"+str(bin_wid)+"ADC Units")

    c1.SetGrid(1,1)
    full_hist.SetMaximum(2e4)
    full_hist.GetXaxis().SetRangeUser(200,1500)
    full_hist.Draw()
    c1.SetLogy(0)
    c1.Update()
    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/Data_Bi207_Linear.png")
    print "Plot of Uncalibrated but Rebinned Data"
    raw_input("Enter to Continue")

    return full_hist


def perform_calibration_fit(full_hist):
    c2 = ROOT.TCanvas("c2")
    c2.SetLogy(0)
    c2.SetGrid(1,1)

    leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)

    full_hist.Draw()

    testfit = ROOT.TF1("testfit", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2) + [3]*TMath::Exp(-[4]*x)", 500,1000)
    testfit.SetParameters(2000,750,40,3e4,3e-3)
    testfit.SetNpx(500)

    full_hist.Fit("testfit","ILR")
    
    bestfit_gaus = ROOT.TF1("bestfitg", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)",0,3000)
    bestfit_gaus.SetParameters(testfit.GetParameter(0), testfit.GetParameter(1), testfit.GetParameter(2))
    bestfit_gaus.SetLineColor(ROOT.kRed)
 
    bestfit_exp = ROOT.TF1("bestfite","[0]*TMath::Exp(-[1]*x)",0,3000)
    bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4))
    bestfit_exp.SetLineColor(ROOT.kBlack)

    leg.AddEntry(full_hist, "Data")
    leg.AddEntry(testfit, "Total Fit")
    leg.AddEntry(bestfit_gaus, "Gaus Peak Fit (sigma = " + str(int(testfit.GetParameter(2)))+ "ADC Unit)")
    leg.AddEntry(bestfit_exp,  "Exp Background Fit")

    testfit.SetLineColor(ROOT.kOrange)
    testfit.Draw("same")
    bestfit_gaus.Draw("same")
    bestfit_exp.Draw("same")
    
    leg.SetFillColor(0)
    leg.Draw()

    c2.Update()
    c2.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/calib_fit_7hour.png")
    raw_input()

    return testfit.GetParameter(1)




def perform_resolution_fit_exp(full_hist, fitElow, fitEhigh):
    c3 = ROOT.TCanvas("c2")
    c3.SetLogy(0)
    c3.SetGrid(1,1)

    leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)

    full_hist.Draw()

    testfit = ROOT.TF1("testfit", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2) + [3]*TMath::Exp(-[4]*x)", fitElow,fitEhigh)
    testfit.SetParameters(2000,570,40,3e4,3e-3)
    testfit.SetNpx(500)
    
    print testfit.GetChisquare()
    full_hist.Fit("testfit","ILR")
    print "EXP Background"
    print "Fit region ", fitElow, " < E < ", fitEhigh
    print "chisquare = ", testfit.GetChisquare(), "ndf = ", testfit.GetNDF()
    print "chisquare/ndf = ", testfit.GetChisquare()/testfit.GetNDF()
    print "prob  =", testfit.GetProb()

    bestfit_gaus = ROOT.TF1("bestfitg", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)",0,3000)
    bestfit_gaus.SetParameters(testfit.GetParameter(0), testfit.GetParameter(1), testfit.GetParameter(2))
    bestfit_gaus.SetLineColor(ROOT.kRed)

    bestfit_exp = ROOT.TF1("bestfite","[0]*TMath::Exp(-[1]*x)",0,3000)
    bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4))
    bestfit_exp.SetLineColor(ROOT.kBlack)

    leg.AddEntry(full_hist, "Data")
    leg.AddEntry(testfit, "Total Fit")
    leg.AddEntry(bestfit_gaus, "Gaus Peak Fit (sigma = " + str(int(testfit.GetParameter(2)))+ "keV)")
    leg.AddEntry(bestfit_exp,  "Exp Background Fit")

    testfit.SetLineColor(ROOT.kOrange)
    testfit.Draw("same")
    bestfit_gaus.Draw("same")
    bestfit_exp.Draw("same")
 
    leg.SetFillColor(0)
    leg.Draw()

    c3.Update()
    c3.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/resolution_fit_7hour.png")
    raw_input()
    return testfit.GetParameter(2)

def perform_resolution_fit_parabola(full_hist, fitElow, fitEhigh):
    c3 = ROOT.TCanvas("c2")
    c3.SetLogy(0)
    c3.SetGrid(1,1)

    leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)

    full_hist.Draw()

    testfit = ROOT.TF1("testfit", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2) + [3] + [4]*x + [5]*x*x", fitElow, fitEhigh)
    testfit.SetParameters(3000,570,40,3e4,-84, 6e-2)
    testfit.SetNpx(500)
    
    print testfit.GetChisquare()
    full_hist.Fit("testfit","ILR")
    print "Parabolic Background"
    print "Fit region ", fitElow, " < E < ", fitEhigh
    print "chisquare = ", testfit.GetChisquare(), "ndf = ", testfit.GetNDF()
    print "chisquare/ndf = ", testfit.GetChisquare()/testfit.GetNDF()
    print "prob = ", testfit.GetProb()

    bestfit_gaus = ROOT.TF1("bestfitg", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)",0,3000)
    bestfit_gaus.SetParameters(testfit.GetParameter(0), testfit.GetParameter(1), testfit.GetParameter(2))
    bestfit_gaus.SetLineColor(ROOT.kRed)

    bestfit_parabola = ROOT.TF1("bestfitp","[0] + [1]*x + [2]*x*x",0,3000)
    bestfit_parabola.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4), testfit.GetParameter(5))
    bestfit_parabola.SetLineColor(ROOT.kBlack)

    leg.AddEntry(full_hist, "Data")
    leg.AddEntry(testfit, "Total Fit")
    leg.AddEntry(bestfit_gaus, "Gaus Peak Fit (sigma = " + str(int(testfit.GetParameter(2)))+ "keV)")
    leg.AddEntry(bestfit_parabola,  "Exp Background Fit")

    testfit.SetLineColor(ROOT.kOrange)
    testfit.Draw("same")
    bestfit_gaus.Draw("same")
    bestfit_parabola.Draw("same")

    #leg.SetFillColor(0)
    #leg.Draw()

    c3.Update()
    c3.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/resolution_fit_7hour_parabola.png")
    raw_input()
    return testfit.GetParameter(2)


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
    
    calib_peak = 570.0 #keV
    full_hist = get_full_hist(files)
    peak_pos = perform_calibration_fit(full_hist)
    calibrate(full_hist, calib_peak/peak_pos)
    sig = perform_resolution_fit_parabola(full_hist, 400, 700)    
    print "Sig = ",  sig
    print "Resolution is: ", (sig/calib_peak)*100
    print

    sig = perform_resolution_fit_exp(full_hist, 400, 700)
    print "Sig = ",  sig
    print "Resolution is: ", (sig/calib_peak)*100
    print

    sig = perform_resolution_fit_parabola(full_hist, 400, 800)
    print "Sig = ",  sig
    print "Resolution is: ", (sig/calib_peak)*100
    print

    sig = perform_resolution_fit_exp(full_hist, 400, 800)
    print "Sig = ",  sig
    print "Resolution is: ", (sig/calib_peak)*100
    print

    sig = perform_resolution_fit_parabola(full_hist, 500, 650)
    print "Sig = ",  sig
    print "Resolution is: ", (sig/calib_peak)*100
    print

    sig = perform_resolution_fit_exp(full_hist, 500, 650)
    print "Sig = ",  sig
    print "Resolution is: ", (sig/calib_peak)*100
    print













