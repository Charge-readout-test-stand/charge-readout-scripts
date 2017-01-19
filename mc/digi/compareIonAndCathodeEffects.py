
# for RalphWF.py:
import RalphWF

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TGraph
from ROOT import TLegend
from ROOT import TLine
from ROOT import TColor
from ROOT import TFile


def make_graph(
    e_lifetime=None, # microseconds
):

    cathodeToAnodeDistance = RalphWF.cathodeToAnodeDistance
    # options
    x = 1.5 # mm
    y = 0.0 # mm
    z = 0.23 # distance from cathode
    q = 1.0 # arbitrary
    dz = 0.25 # mm -- for nice plots -- takes ~1.5 minutes
    #dz = 1.0 # mm -- quick & dirty
    #z = cathodeToAnodeDistance # mm
    z = 0

    print "--> making graph: %i, %i" % (RalphWF.posion, RalphWF.cathsupress)

    #Collection signal on channel X16, WF is numpy array
    # args: x, y, z, q, channel
    integral_efficiency = 0.0
    integral_distance = 0.0
    graph = TGraph()
    dz = (cathodeToAnodeDistance - z)/100.0
    #dz = 0.5
    while z < cathodeToAnodeDistance:
        WF = RalphWF.make_WF(x, y, z, q, 15)
        val = WF[-1]
        integral_distance += dz
        integral_efficiency += val*dz
        print "\t %i, z=%.1f, val=%.5f" % (graph.GetN(), z, val)
        graph.SetPoint(graph.GetN(), cathodeToAnodeDistance-z, val)
        z += dz
    graph.SetLineWidth(2)
    graph.Draw("goff")
    hist = graph.GetHistogram()
    hist.SetXTitle("Interaction location (distance from anode) [mm]")
    hist.SetYTitle("Fraction of ionization charge observed")
    graph.SetMarkerStyle(8)
    graph.SetMarkerSize(0.5)
    graph.SetFillColor(0)
    graph.SetFillStyle(0)
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
    outfile = TFile("ionAndCathodeEffect.root","recreate")

    print "no effects"
    RalphWF.posion = False
    RalphWF.cathsupress = False
    graph = make_graph()
    graph.Draw("al")
    hist = graph.GetHistogram()
    hist.SetXTitle("Interaction location (distance from anode) [mm]")
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
    graph2.SetLineWidth(4)
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
    #canvas.Print("ionAndCathodeEffect.png")

    """
    print "e- lifetime"
    RalphWF.posion = False
    RalphWF.cathsupress = False
    RalphWF.e_lifetime = 50.0 # microseconds
    graph5 = make_graph()
    graph5.SetLineColor(TColor.kViolet+1)
    graph5.Draw("l")
    legend.AddEntry(graph5, "#tau_{e-}=%i#mus" % RalphWF.e_lifetime, "l")

    if False:
        print "e- lifetime + captured charge"
        RalphWF.posion = False
        RalphWF.cathsupress = False
        RalphWF.consider_capturedQ = True
        graph6 = make_graph()
        graph6.SetLineColor(TColor.kMagenta)
        graph6.Draw("l")
        legend.AddEntry(graph6, "#tau_{e-}=%i#mus w captured Q" % RalphWF.e_lifetime, "l")

    print "all"
    RalphWF.posion = True
    RalphWF.cathsupress = True
    RalphWF.consider_capturedQ = False
    graph7 = make_graph()
    graph7.SetLineColor(TColor.kGreen+2)
    graph7.Draw("l")
    legend.AddEntry(graph7, "ion + cathode + #tau_{e-}=%i#mus" % RalphWF.e_lifetime, "l")

    legend.Draw()
    canvas.Update()
    canvas.Print("ionAndCathodeEffectWithTau.pdf")
    canvas.Print("ionAndCathodeEffectWithTau.png")
    """

    if not gROOT.IsBatch():
        val = raw_input("press enter to continue") # pause

    #graph4.Write("graphIonAndCathode")
    #graph5.Write("graphIonAndCathode%iusTau" % RalphWF.e_lifetime)
    outfile.Close()

if __name__ == "__main__":
    main()
