
# for RalphWF.py:
#import numpy as np
#import matplotlib.pyplot as plt
import RalphWF

# for AGS root macro:
from ROOT import gROOT
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TGraph
from ROOT import TLegend
from ROOT import TLine
from ROOT import TColor


def make_graph():

    # options
    x = 1.5 # mm
    y = 0.0 # mm
    z = 0.0 # distance from cathode
    q = 1.0 # arbitrary
    dz = 0.1 # mm -- for nice plots
    #dz = 2.0 # mm -- quick & dirty

    print "--> making graph: %i, %i" % (RalphWF.posion, RalphWF.cathsupress)

    #Collection signal on channel X16, WF is numpy array
    # args: x, y, z, q, channel
    integral_efficiency = 0.0
    integral_distance = 0.0
    graph = TGraph()
    cathodeToAnodeDistance = RalphWF.cathodeToAnodeDistance
    while z < cathodeToAnodeDistance:
        WF = RalphWF.make_WF(x, y, z, q, 15)
        val = WF[-1]
        integral_distance += dz
        integral_efficiency += val*dz
        print "\t %i, z=%.1f, val=%.3f" % (graph.GetN(), z, val)
        graph.SetPoint(graph.GetN(), cathodeToAnodeDistance-z, val)
        z += dz
    graph.SetLineWidth(2)
    print "integral_distance:", integral_distance
    print "integral_efficiency", integral_efficiency
    print "integral_efficiency / integral_distance:", integral_efficiency/integral_distance
    return graph


def main():
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)

    print "no effects"
    RalphWF.posion = False
    RalphWF.cathsupress = False
    graph = make_graph()
    graph.Draw("al")
    hist = graph.GetHistogram()
    hist.SetXTitle("Distance from anode [mm]")
    hist.SetYTitle("Fraction of ionization charge observed")
    hist.SetMinimum(0.0)
    hist.SetMaximum(1.1)
    #hist.SetAxisRange(5, 20)
    graph.SetLineColor(TColor.kBlack)
    legend.AddEntry(graph, "No screening or cathode effects", "l")

    print "ion only"
    RalphWF.posion = True
    RalphWF.cathsupress = False
    graph2 = make_graph()
    graph2.SetLineColor(TColor.kBlue)
    graph2.Draw("l")
    legend.AddEntry(graph2, "Ion screening only", "l")
 
    # without the ion, this doesn't do anything to the final value!
    #print "cathode only"
    #RalphWF.posion = False
    #RalphWF.cathsupress = True
    #graph3 = make_graph()
    #graph3.SetLineColor(TColor.kGreen+1)
    #graph3.Draw("l")
    #legend.AddEntry(graph3, "cathode effect only", "l")
 
    print "ion + cathode"
    RalphWF.posion = True
    RalphWF.cathsupress = True
    graph4 = make_graph()
    graph4.SetLineColor(TColor.kRed)
    graph4.Draw("l")
    legend.AddEntry(graph4, "Ion screening + cathode effect", "l")
    

    cathodeToAnodeDistance = RalphWF.cathodeToAnodeDistance
    line = TLine(cathodeToAnodeDistance, hist.GetMinimum(), 
        cathodeToAnodeDistance, hist.GetMaximum())
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    line.Draw()

    legend.Draw()
    canvas.Update()
    canvas.Print("ionAndCathodeEffect.pdf")
    canvas.Print("ionAndCathodeEffect.png")

    val = raw_input("press enter to continue") # pause

if __name__ == "__main__":
    main()
