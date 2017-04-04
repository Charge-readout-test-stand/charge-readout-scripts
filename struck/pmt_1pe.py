"""
Script to fit single photo-electron peak in PMT spectrum, from Ako 18 Feb 2017

seems sensitive to:
    left_end
    pedestal_mean
    TE background settings
"""


import sys
import os
import ROOT
import numpy as np
import matplotlib as plot
from optparse import OptionParser
from difflib import Differ

#ROOT.gROOT.SetBatch(True)
#ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kWarning;")
ROOT.gStyle.SetOptStat(1) # show box on plots
ROOT.gStyle.SetOptFit(1);
fac = ROOT.TMath.Factorial
parser = OptionParser()

#When calling this script the (path/)filename should be passed as option
#parser.add_option("-f", "--file",action="store", type="string", dest="filename")
#(options, args) = parser.parse_args()
#path, file = os.path.split(options.filename)
#filename = options.filename

filename = sys.argv[1]
basename = os.path.splitext(os.path.basename(filename))[0]

print "...This file will be used:	", ("%s.root" % basename)
#Get histogram from ROOT file
#c1 = ROOT.TCanvas("c1","",2500,2200)
c1 = ROOT.TCanvas("c1","")
c1.SetLogy(1)
#tfile = ROOT.TFile("%s.root" % basename, "read")
tfile = ROOT.TFile(filename)
hist = tfile.Get("hist")
#hist.Rebin() # default is 2x
print hist.GetMaximum()
hist.SetMaximum(-1111)
hist.GetYaxis().SetTitleOffset(1.2)
hist_max =  hist.GetMaximum()
hist.SetMaximum(hist_max*2.0)
hist.SetMinimum(1)
#hist.SetMinimum(0.1)
hist.Draw()
print "hist entries:",  hist.GetEntries()

pedestal_mean = hist.GetBinCenter(hist.GetMaximumBin())
if "sig_chain" in basename:
    pedestal_mean = 11.0
    if "2V" in basename and "500cg" in basename:
        pedestal_mean = 450
#pedestal_mean = 12.0 # AGS test
print "pedestal mean:", pedestal_mean
#left_end = pedestal_mean + 1.0*hist.GetBinWidth(1) # if the step function is used, left_end must be pedestal mean!
left_end = pedestal_mean # if the step function is used, left_end must be pedestal mean!
#left_end = 0.0
left_end = pedestal_mean - 1.0*hist.GetBinWidth(1)
if "2V" in basename and "500cg" in basename:
    left_end = pedestal_mean - 3.0*hist.GetBinWidth(1)
#Set fitting range from maximum of pedestal to last bin with more than 10 counts
right_end = hist.GetBinCenter(hist.FindLastBinAbove(10))


#Define background function consisting of a gaussian for the pedestal and an exponential for background processes

# this version is in pdf from ako?:
#background = "(((1-[6])/([4]*sqrt(2*3.14)))*exp(-.5*((x-[3])/(sqrt(2)*[4]))^2)+[6]*(x>[3])*[7]*[5]*exp(-[7]*(x-[3])))*exp(-[0])"

#background = "(((1-[6])/([4]*sqrt(2*3.14)))*exp(-.5*((x-[3])/(sqrt(2)*[4]))^2)+[6]*(x>[3])*[5]*exp(-[7]*(x-[3])))*exp(-[0])"

# incorporating gf3 efcc:
background = "((((1-[6])/([4]*sqrt(2*3.14)))*exp(-.5*((x-[3])/(sqrt(2)*[4]))^2)+[6]*0.5*[7]*TMath::Erfc(([3]-x)/(sqrt(2)*[4] + [4]*[7]/sqrt(2)))*exp(-[7]*(x-[3])))*exp(-[0]))*[8]"

#Define #nr_pe Poisson convoluted Gaussians
gaussian = ""
nr_pe = 5
for ii in range(1, nr_pe):
        print "adding gaussian: ", ii
	gaussian += ("(([0]^%s*exp(-[0]))/%s)*(1/([2]*sqrt(2*%s*3.14)))*exp(-.5*((x-[1]*%s-[3])/(sqrt(2*%s)*[2]))^2) +" % (ii,fac(ii),ii,ii,ii))

gaussian = gaussian[:-1]

#Combine both components of the PMT response function to one function
function = "[5]*(" + background + "+" + gaussian +")"
print "\n"


print "\nbackground:\n", background
print "\ngaussian:\n", " + \n".join(gaussian.split("+"))
print "\nfunction:\n", function

f = ROOT.TF1("f",function,left_end,right_end)
f.SetLineColor(ROOT.kRed);
f.SetNpx(10000);

#Define parameter ranges and start values
f.SetParName(0, "Mean number of PEs")
f.SetParameter(0,0.1);
if "no_sig" in basename:
    f.SetParameter(0,0.1)
    print "no_sig!"
f.SetParLimits(0,0,10.0);

f.SetParName(1, "1PE peak mean")
f.SetParameter(1,50) # + [3]
if "sig_chain" in basename:
    f.SetParameter(1,13) # + [3]
    print "sig_chain!"
    if "2V" in basename and "500cg" in basename:
        f.SetParameter(1,1500)
f.SetParLimits(1,0,right_end);

f.SetParName(3, "pedestal mean")
f.SetParName(2, "1PE peak sigma")
f.SetParameter(2,15);
f.SetParLimits(2,0,100);
if "sig_chain" in basename:
    f.SetParameter(2,4) 
    print "sig_chain!"
    if "2V" in basename and "500cg" in basename:
        f.SetParameter(2,400) 
        f.SetParLimits(2,0,1000);

f.SetParameter(3, pedestal_mean)
f.SetParLimits(3, pedestal_mean*0.5, pedestal_mean*5.0);

f.SetParName(4, "pedestal sigma")
f.SetParameter(4, 0.5);
f.SetParLimits(4,0,10);
if "sig_chain" in basename:
    f.SetParameter(4,1.3) 
    print "sig_chain!"
    if "2V" in basename and "500cg" in basename:
        f.SetParameter(4,20) 
        f.SetParLimits(4,0,100);

f.SetParName(5, "Normalization (of 1PE?)")
f.SetParameter(5, 1.0*hist.GetEntries()*hist.GetBinWidth(1));

f.SetParName(6, "P of TE emission")
f.SetParameter(6,0.06);
f.SetParLimits(6,0,1);
if "sig_chain" in basename:
    f.SetParameter(6, 0.02) 
    print "sig_chain!"
#f.FixParameter(6,0.0) # turn off TE emission part
#f.FixParameter(6,1.0) # 100% TE emission part

f.SetParName(7, "Coeff of exp dec. of TE bkg")
f.SetParameter(7, 0.03);
#f.SetParLimits(7,.000001,100000);

# I think the way we select events breaks the poisson dist. for events with no PE
f.SetParName(8, "pedestal norm")
f.SetParameter(8, 0.5);
#f.FixParameter(8,1.0) # use Poisson constraint

hist.SetAxisRange(0, right_end*1.2)
hist.Draw()
f.Draw("same")
f1 = []
for ii in range(1, nr_pe):
	f1.append(ROOT.TF1("f1",("(([0]^%s*exp(-[0]))/%s)*([3]/([2]*sqrt(2*%s*3.14)))*exp(-.5*(((x-[1]*%s-[4]))/(sqrt(2*%s)*[2]))^2)" % (str(ii),str(fac(ii)),str(ii),str(ii),str(ii))),left_end, 10000))
	f1[ii-1].SetNpx(10000)
	f1[ii-1].SetLineStyle(3)
	f1[ii-1].SetParameters(f.GetParameter(0),f.GetParameter(1),f.GetParameter(2),f.GetParameter(5),f.GetParameter(3))
	f1[ii-1].SetLineColor(ROOT.kBlue+ii)
	f1[ii-1].Draw("same")

#Plot background contribution
#f2 = ROOT.TF1("f2","[3]*(((1-[4])/([2]*sqrt(2*3.14)))*exp(-.5*(((x-[1]))/(sqrt(2)*[2]))^2)+[4]*(x>[1])*[3]*exp(-[5]*(x-[1])))*exp(-[0])", left_end, 10000);
f2 = ROOT.TF1("f2",
#"[3]*(((1-[4])/([2]*sqrt(2*3.14)))*exp(-.5*(((x-[1]))/(sqrt(2)*[2]))^2)+[4]*(x>[1])*[3]*exp(-[5]*(x-[1])))*exp(-[0])", 
"[6]*([3]*(((1-[4])/([2]*sqrt(2*3.14)))*exp(-.5*((x-[1])/(sqrt(2)*[2]))^2)+[4]*0.5*[5]*TMath::Erfc(([1]-x)/(sqrt(2)*[2] + [2]*[5]/sqrt(2)))*exp(-[5]*(x-[1])))*exp(-[0]))", 
left_end, #0.0, 
10000);
f2.SetNpx(10000);
f2.SetParameters(f.GetParameter(0),f.GetParameter(3),f.GetParameter(4),f.GetParameter(5),f.GetParameter(6),f.GetParameter(7), f.GetParameter(8));
f2.SetLineColor(ROOT.kMagenta);
f2.SetLineStyle(3);
f2.Draw("SAME");
f.Draw("same")
c1.Update()
c1.SaveAs("%s_pmt_1pe_before_fit.pdf" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue ")

#sys.exit()i # debugging

#Fit the response function #nr_fit times to the histogram
nr_fit = 20
for ii in range(nr_fit):
        print "-----------------------------------------------"
        print "Fit Nr. ", ii, "\r"

	#if(ii==nr_fit-1):
        #	hist.Fit("f","QMERL","");
	#else:
	#	hist.Fit("f","MERL","");
	#	print "Fit Nr. ", ii, "\r"


        #result = hist.Fit("f","RLSI","") # "I" has tolerance probs
        result = hist.Fit("f","RLS","")
        status = result.Status()
        print "status=", status

        #if False:
        if True:
            result = hist.Fit("f","MERLS","")
            status = result.Status()
            print "status=", status
        if status == 0: break


#Extract the fitted paratemeter values to plot the individual components of the PMT response function
hist.Draw()
for ii in range(1, nr_pe):
	f1[ii-1].SetNpx(10000)
	f1[ii-1].SetLineStyle(3)
	f1[ii-1].SetParameters(f.GetParameter(0),f.GetParameter(1),f.GetParameter(2),f.GetParameter(5),f.GetParameter(3))
	f1[ii-1].SetLineColor(ROOT.kBlue+ii)
	f1[ii-1].Draw("same")

#Plot background contribution
f2.SetNpx(10000);
f2.SetParameters(f.GetParameter(0),f.GetParameter(3),f.GetParameter(4),f.GetParameter(5),f.GetParameter(6),f.GetParameter(7), f.GetParameter(8));
f2.SetLineColor(ROOT.kMagenta);
f2.SetLineStyle(3);
f2.Draw("SAME");

#Save plot as pdf
c1.Update()
c1.SaveAs("%s_pmt_1pe.pdf" % basename)
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue ")






