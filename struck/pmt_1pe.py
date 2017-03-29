"""
Script to fit single photo-electron peak in PMT spectrum, from Ako 18 Feb 2017
"""


import sys
import os
import ROOT
import numpy as np
import matplotlib as plot
from optparse import OptionParser
from difflib import Differ
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kWarning;")
ROOT.gStyle.SetOptFit(111);
fac = ROOT.TMath.Factorial
parser = OptionParser()

#When calling this script the (path/)filename should be passed as option
parser.add_option("-f", "--file",action="store", type="string", dest="filename")
(options, args) = parser.parse_args()

path, file = os.path.split(options.filename)
basename = os.path.splitext(file)[0]

print "...This file will be used:	", ("%s.root" % basename)
#Get histogram from ROOT file
c1 = ROOT.TCanvas("c1","",2500,2200)
file = ROOT.TFile("%s.root" % basename, "read")
hist = file.Get("hist")
hist.Rebin()
hist.SetMinimum(1)
hist.Draw()

#Set fitting range from maximum of pedestal to last bin with more than 10 counts
left_end = hist.GetXaxis().GetBinCenter(hist.GetMaximumBin())
right_end = hist.GetXaxis().GetBinCenter(hist.FindLastBinAbove(10,1))


#Define background function consisting of a gaussian for the pedestal and an exponential for background processes
background = "(((1-[6])/([4]*sqrt(2*3.14)))*exp(-.5*(((x-[3]))/(sqrt(2)*[4]))^2)+[6]*(x>[3])*[5]*exp(-[7]*(x-[3])))*exp(-[0])"

#Define #nr_pe Poisson convoluted Gaussians
gaussian = ""
nr_pe = 3
for ii in range(1,nr_pe):
	gaussian += ("(([0]^%s*exp(-[0]))/%s)*(1/([2]*sqrt(2*%s*3.14)))*exp(-.5*((x-[1]*%s-[3])/(sqrt(2*%s)*[2]))^2)+" % (str(ii),str(fac(ii)),str(ii),str(ii),str(ii)))

gaussian = gaussian[:-1]

#Combine both components of the PMT response function to one function
function = "[5]*(" + background + "+" + gaussian +")"


f = ROOT.TF1("f",function,left_end,right_end)
f.SetLineColor(ROOT.kRed);
f.SetNpx(10000);

#Define parameter ranges and start values
f.SetParameter(0,.03);
f.SetParLimits(0,0,1);
f.SetParameter(1,150);
f.SetParLimits(1,100,250);
f.SetParameter(2,20);
f.SetParLimits(2,10,100);
f.SetParameter(3,hist.GetXaxis().GetBinCenter(hist.GetMaximumBin()));
f.SetParLimits(3,hist.GetXaxis().GetBinCenter(hist.GetMaximumBin())*.5,hist.GetXaxis().GetBinCenter(hist.GetMaximumBin())*1.5);
f.SetParameter(4,5);
f.SetParLimits(4,0,10);
f.SetParameter(5,1000);
f.SetParameter(6,0.001);
f.SetParLimits(6,0,1);
f.SetParameter(7,5);
#f.SetParLimits(7,.000001,100000);

#Fit the response function #nr_fit times to the histogram
nr_fit = 10
for ii in range(nr_fit):
	if(ii==nr_fit-1):
		hist.Fit("f","QMERL","");
	else:
		hist.Fit("f","MERL","");
		print "Fit Nr. ", ii, "\r"

#Extract the fitted paratemeter values to plot the individual components of the PMT response function
f1 = []
for ii in range(1,nr_pe):
	f1.append(ROOT.TF1("f1",("(([0]^%s*exp(-[0]))/%s)*([3]/([2]*sqrt(2*%s*3.14)))*exp(-.5*(((x-[1]*%s-[4]))/(sqrt(2*%s)*[2]))^2)" % (str(ii),str(fac(ii)),str(ii),str(ii),str(ii))),left_end, 10000))
	f1[ii-1].SetNpx(10000)
	f1[ii-1].SetLineStyle(3)
	f1[ii-1].SetParameters(f.GetParameter(0),f.GetParameter(1),f.GetParameter(2),f.GetParameter(5),f.GetParameter(3))
	f1[ii-1].SetLineColor(ROOT.kBlue+ii)
	f1[ii-1].Draw("same")

#Plot background contribution
f2 = ROOT.TF1("f2","[3]*(((1-[4])/([2]*sqrt(2*3.14)))*exp(-.5*(((x-[1]))/(sqrt(2)*[2]))^2)+[4]*(x>[1])*[3]*exp(-[5]*(x-[1])))*exp(-[0])", left_end, 10000);
f2.SetNpx(10000);
f2.SetParameters(f.GetParameter(0),f.GetParameter(3),f.GetParameter(4),f.GetParameter(5),f.GetParameter(6),f.GetParameter(7));
f2.SetLineColor(ROOT.kMagenta);
f2.SetLineStyle(3);
f2.Draw("SAME");

#Save plot as pdf
c1.SetLogy(1)
c1.SaveAs("pmt_1pe.pdf")






