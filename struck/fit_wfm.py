"""
Fit one charge signal wfm
"""

import os
import sys
import math
import time
from array import array

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TGraph
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle
from ROOT import gSystem


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

#gROOT.LoadFile("myfunc.C")
gROOT.ProcessLine('.L myfunc.C')
from ROOT import MyFunction

gSystem.Load("$EXOLIB/lib/libEXOROOT")
from ROOT import CLHEP
from ROOT import EXODoubleWaveform
from ROOT import EXOBaselineRemover

# definition of calibration constants, decay times, channels
import struck_analysis_parameters


def f(x, y, z): 
    # f, from Ralph's definition
    return math.atan(x*y/(z*math.sqrt(x*x + y*y + z*z)))


def one_pad(x,y,z):
    # response from one square pad, where x,y,x is distance to pad's center
    diagonal = 3.0 # mm
    side_length = diagonal/math.sqrt(2)
    x1 = x - side_length/2.0
    x2 = x + side_length/2.0
    y1 = y - side_length/2.0
    y2 = y + side_length/2.0
    return ( f(x2,y2,z) - f(x1,y2,z) - f(x2,y1,z) + f(x1,y1,z) ) / (2*math.pi)


def one_pad_rotated(x,y,z):
    # rotated
    # response from one square pad, where x,y,x is distance to pad's center
    diagonal = 3.0 # mm
    side_length = diagonal/math.sqrt(2)

    # calculate new variables in rotated coord system of anode pad:
    x_n = (x - y)/math.sqrt(2)
    y_n = (x + y)/math.sqrt(2)

    x1 = x_n - side_length/2.0
    x2 = x_n + side_length/2.0
    y1 = y_n - side_length/2.0
    y2 = y_n + side_length/2.0
    return ( f(x2,y2,z) - f(x1,y2,z) - f(x2,y1,z) + f(x1,y1,z) ) / (2*math.pi)



def draw():

    drift_velocity = 1.72 # mm / microsecond
    diagonal = 3.0 # mm
    side_length = diagonal/math.sqrt(2)
  
    # starting position:
    z = 2.0
    x = 0.0
    y = 0.0
    t = 0.0

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    graph = TGraph()
    graph.SetLineWidth(1)
    graph.SetMarkerStyle(8)
    graph.SetMarkerSize(0.5)
    graph2 = TGraph()
    graph2.SetLineColor(TColor.kRed)

    dz = 0.05 # mm
    z0 = z
    while z > 0:

        q = one_pad(x, y, z)
        q2 = one_pad_rotated(x, y, z)
        print "z=%.2f | t=%.2f | q=%.2f | q2=%.2f" % (z, t, q, q2)
        n_points = graph.GetN()
        graph.SetPoint(n_points, t, q)
        graph2.SetPoint(n_points, t, q2)

        z -= dz # decrement z
        t += dz / drift_velocity # increment t
    
    graph.Draw("apl")
    graph2.Draw("l")


def do_fit():

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz

    # one test:
    file_name = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier2/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root"
    tfile = TFile(file_name)
    tree = tfile.Get("tree")
    for i_entry in xrange(tree.GetEntries()):

        tree.GetEntry(i_entry)
        #if struck_analysis_parameters.charge_channels_to_use[tree.channel]:
        #    print channel
        calibration = struck_analysis_parameters.calibration_values[tree.channel[3]]
        calibration/=2.5
        #print calibration

        # only ch 3 for now:
        wfm = tree.wfm3
        energy = (tree.wfm_max[3] - wfm[0])*calibration
        print i_entry, energy
        if energy < 200: continue

        # setup the fit function
        test = TF1("test",MyFunction, 5, 22, 4)
        test.SetParName(0, "x")
        test.SetParName(1, "y")
        test.SetParName(2, "z0")
        test.SetParName(3, "q")
        test.SetParameter(0, 0) # x
        test.SetParameter(1, 0) # y
        test.SetParameter(2, 20.0) # z0
        test.SetParameter(3, energy) # q
        test.Draw() 
        hist = test.GetHistogram()
        hist.SetXTitle("time [#mus]");
        hist.SetYTitle("charge [arb]");



        exo_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
        exo_wfm*=calibration
        exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)


        # remove the baseline
        baseline_remover = EXOBaselineRemover()
        baseline_remover.SetBaselineSamples(100)
        baseline_remover.Transform(exo_wfm)
        rms = baseline_remover.GetBaselineRMS()
        print "rms", rms

        wfm_hist = exo_wfm.GimmeHist()
        for i_bin in xrange(wfm_hist.GetNbinsX()):
            wfm_hist.SetBinError(i_bin,20.0) # approx. rms
        wfm_hist.SetLineColor(TColor.kRed)
        wfm_hist.SetLineWidth(2)
        wfm_hist.Draw()
        test.Draw("same")

        canvas.Update()
        #raw_input("enter to continue")

        print "doing fit..."
        fit_start = time.clock()
        fit_result = wfm_hist.Fit(test, "SR")
        fit_stop = time.clock()
        wfm_hist.Draw()
        print "chi2", fit_result.Chi2()
        print "prob", fit_result.Prob()
        print "n dof", fit_result.Ndf()
        print "status", fit_result.Status()
        print "%.1f seconds" % (fit_stop - fit_start)

        canvas.Update()
        raw_input("enter to continue")


if __name__ == "__main__":
    #draw()
    do_fit()


