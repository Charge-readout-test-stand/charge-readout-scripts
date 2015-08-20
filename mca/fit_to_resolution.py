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


def get_full_hist(files):   
    
    full_hist = ROOT.TH1D("full_hist", "full_hist", nbins, 0, ch_hi)

    hist_list = []

    test_time = []
    for f in files:
        hist_hold, lvtime = convertMCA.getMCAhist(f)
        hist_list.append(hist_hold)
        full_hist.Add(hist_hold)
        test_time.append(lvtime)
 
    test_time = np.array(test_time)
    print "Total data taken for ", np.sum(test_time)/(60*60), " hours"

    c1 = ROOT.TCanvas("c1")

    full_hist.SetLineColor(ROOT.kBlue)
    full_hist.SetFillColor(ROOT.kBlue)
    full_hist.SetFillStyle(3004)

    full_hist.Rebin(8)

    full_hist.GetXaxis().SetTitle("Energy[keV]")
    full_hist.SetTitle("Bi207 Spectrum at 1kV/cm Drift Field")

    #By eye calibrated so that 570keV peak appears roughly where it is supposed to
    calibration = 0.75

    print "Using Eye Ball Calibration of ", calibration

    full_hist.GetXaxis().SetLimits(0,ch_hi*calibration)
    print "Scaled ADC now the energy range is ", full_hist.GetXaxis().GetXmin(), full_hist.GetXaxis().GetXmax()
    print "After Rebinning by 8 and calibrating the Bin Width is...",  full_hist.GetBinWidth(0)
    
    bin_wid = int(full_hist.GetBinWidth(0))
    full_hist.GetYaxis().SetTitle("Counts/"+str(bin_wid)+"keV")

    c1.SetGrid(1,1)
    full_hist.SetMaximum(8e3)
    full_hist.GetXaxis().SetRangeUser(200,1500)
    full_hist.Draw()
    c1.SetLogy(0)
    c1.Update()
    c1.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/Data_Bi207_Linear.png")

    raw_input()

    return full_hist


def perform_fit(files):
    full_hist = get_full_hist(files)

    c2 = ROOT.TCanvas("c2")
    c2.SetLogy(0)
    c2.SetGrid(1,1)

    leg = ROOT.TLegend(0.6, 0.7, 0.95, 0.90)

    full_hist.Draw()

    testfit = ROOT.TF1("testfit", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2) + [3]*TMath::Exp(-[4]*x)", 300,700)
    testfit.SetParameters(6000,540,40,1e6,0.012)
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
    leg.AddEntry(bestfit_gaus, "Gaus Peak Fit (sigma = " + str(int(testfit.GetParameter(2)))+ "keV)")
    leg.AddEntry(bestfit_exp,  "Exp Background Fit")

    testfit.SetLineColor(ROOT.kOrange)
    testfit.Draw("same")
    bestfit_gaus.Draw("same")
    bestfit_exp.Draw("same")
    
    leg.SetFillColor(0)
    leg.Draw()

    c2.Update()
    c2.Print("/afs/slac.stanford.edu/u/xo/mjj46/Test_Stand/LXe_4th/Group_Meeting/plots/resolution_fit_7hour.png")
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

    perform_fit(files)



















