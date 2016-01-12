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

    # unit charge, considering induced signal at a point:
    #q = z/(2*math.pi*pow(rho*rho + z*z, 3/2))*area
    #if q > 1: q = 1 # handle blow up as z -> 

    # unit charge, considering induced signal in a circular pad:
    # using method of images from wikipedia -- doesn't account for cathode
    q = z*(-1/math.sqrt(rho*rho + z*z) + 1.0/math.sqrt(pow(r-rho,2)+z*z))
    return q


def draw_wfm(rho, z):
  
    dz = 0.0001 # mm, step in z
    #area = 3*3/2 # mm, one pad
    #area = 1.0
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
    ionQ = calculate_charge(rho,z)

    # the charge starts at z and drifts to the anode...
    while z > 0: 

        q = calculate_charge(rho,z) - ionQ 

        #print z, q
        graph.SetPoint(graph.GetN(), t, q)

        t += dz/velocity
        z -= dz

    # add a final point at 20 microseconds to make the wfm longer
    graph.SetPoint(graph.GetN(), 20, q)
    print q

    graph.Draw("al")
    hist = graph.GetHistogram()
    hist.SetXTitle("time [#mus]")
    hist.SetYTitle("charge")
    hist.Draw()
    graph.Draw()
    canvas.Update()
    raw_input("--> press enter")



if __name__ == "__main__":


    draw_wfm(rho=3.0, z=18.0)



