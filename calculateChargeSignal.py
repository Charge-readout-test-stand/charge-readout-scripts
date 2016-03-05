#!/usr/bin/env python

"""
Calculate charge induced on a strip

to do:
* right now, anode pads are cicular
* this doesn't account for the cathode being nearby
"""

import os
import sys
import math

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TGraph
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TLine
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle


def calculate_charge(rho,z):

    r = 1.5 # mm, radius of pad
    area = 1.0
    cathode_distance = 17.0 # mm

    #print rho, z
    # unit charge, considering induced signal at a point:
    q = z/(2*math.pi*pow(rho*rho + z*z, 3/2))*area
    if q > 1: q = 1 # handle blow up as z -> 0 

    # account for effect of cathode:
    #q*=(1-z/cathode_distance)

    # unit charge, considering induced signal in a circular pad:
    # using method of images from wikipedia -- doesn't account for cathode
    #q = z*(1/math.sqrt(rho*rho + z*z) - 1.0/math.sqrt(pow(r+rho,2)+z*z))
    return q


def draw_wfm(rho, z):
  
    dz = 0.01 # mm, step in z
    velocity = 2.0 # mm/us
    pad_pitch = 3.0
    #n_pads = 30
    t = 0 # microseconds, time

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    graph = TGraph()
    graph.SetLineWidth(2)
    graph.SetLineColor(TColor.kBlue)


    # the ion doesn't drift, so it contributes a constant
    z0 = z
    ionQ = calculate_charge(rho,z)
    print "rho",rho
    print "z",z
    print "ionQ",ionQ

    # the charge starts at z and drifts to the anode...
    while z >= 0: 

        q = calculate_charge(rho,z) - ionQ 

        #print z, q
        graph.SetPoint(graph.GetN(), t, q)

        t += dz/velocity
        z -= dz

    # add a final point at 20 microseconds to make the wfm longer
    graph.SetPoint(graph.GetN(), 20, q)
    print "q", q

    graph.Draw("al")
    hist = graph.GetHistogram()
    hist.SetTitle("initial location: #rho_{0}=%.1f mm, z_{0}=%.1f mm" % (rho, z0))
    hist.SetXTitle("time [#mus]")
    hist.SetYTitle("charge")
    hist.Draw()
    graph.Draw()
    canvas.Update()
    canvas.Print("signal_z%imm_rho%imm.pdf" % (z0*10.0, rho*10.0))
    raw_input("--> press enter")



if __name__ == "__main__":

    draw_wfm(rho=5.0, z=17.0)



