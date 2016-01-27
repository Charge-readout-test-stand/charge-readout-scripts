"""
Fit one charge signal wfm
"""

import os
import sys
import math

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


    test = TF1("test",MyFunction, 6, 20, 4)
    test.SetParameter(0, 0) # x
    test.SetParameter(1, 0) # y
    test.SetParameter(2, 17.0) # z0
    test.SetParameter(3, 1.0) # q
    test.Draw() 
    hist = test.GetHistogram()
    hist.SetXTitle("time [#mus]");
    hist.SetYTitle("charge [arb]");

    canvas.Update()
    canvas.Print("test.png")
    raw_input("wait...")

    # one test, in a location on alexis' computer":
    tfile = TFile("~/bucket/slac/test-stand/2015_12_07_6th_LXe/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root")
    tree = tfile.Get("tree")
    tree.GetEntry(59)
    wfm = tree.wfm3
    wfm_length = len(wfm)

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz
    exo_wfm = EXODoubleWaveform(array('d',wfm), wfm_length[i])
    exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
    wfm_hist = exo_wfm.GimmeHist()
    wfm_hist.Draw()


    canvas.Update()
    raw_input("wait...")


if __name__ == "__main__":
    draw()


