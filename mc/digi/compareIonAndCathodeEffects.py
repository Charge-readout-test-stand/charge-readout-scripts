
# for RalphWF.py:
import RalphWF

from ROOT import gROOT
gROOT.SetBatch(True)
import ROOT


def make_graph(
    e_lifetime=None, # microseconds
):
    """
    fill a TGraph 
    """

    cathodeToAnodeDistance = RalphWF.cathodeToAnodeDistance
    # options
    x = 1.5 # mm
    y = 0.0 # mm
    q = 1.0 # arbitrary
    #dz = 0.25 # mm -- for nice plots -- takes ~1.5 minutes
    #dz = 1.0 # mm -- quick & dirty, takes ~ 1 minute at 33mm drift
    #dz = 4.0 # mm
    z = 0 # distance from cathode
    wfm_length = 800
    if cathodeToAnodeDistance > 900:
        z = 880 # mm, for nEXO
        wfm_length = 8000
    dz = (cathodeToAnodeDistance - z)/100.0 # nice for most drift lengths
    #dz = 2.0

    print "--> making graph: %i, %i" % (RalphWF.posion, RalphWF.cathsupress)

    #Collection signal on channel X16, WF is numpy array
    # args: x, y, z, q, channel
    integral_efficiency = 0.0
    integral_distance = 0.0
    graph = ROOT.TGraph()
    # for every z step, find the final value of the waveform
    while z <= cathodeToAnodeDistance+dz*0.5:
        WF = RalphWF.make_WF(x, y, z, q, 15, 
                cathodeToAnodeDistance=cathodeToAnodeDistance,
                dZ=dz, wfm_length=wfm_length)
        val = WF[-1] # last value of waveform
        integral_distance += dz
        integral_efficiency += val*dz
        print "\t %i, z=%.3f, val=%.5f" % (graph.GetN(), cathodeToAnodeDistance-z, val)
        graph.SetPoint(graph.GetN(), cathodeToAnodeDistance-z, val)
        z += dz
    graph.SetLineWidth(2)
    #graph.SetFillStyle(0)
    print "integral_distance:", integral_distance
    print "integral_efficiency", integral_efficiency
    print "integral_efficiency / integral_distance:", integral_efficiency/integral_distance
    return graph


def main():
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetGrid(1,1)
    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)
    legend2 = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend2.SetFillColor(0)
    legend2.SetNColumns(2)
    outfile = ROOT.TFile("ionAndCathodeEffect.root","recreate")

    print "no effects"
    RalphWF.posion = False
    RalphWF.cathsupress = False
    graph = make_graph()
    graph.Draw("al")
    hist = graph.GetHistogram()
    xmax = hist.GetXaxis().GetXmax()
    hist.GetXaxis().SetLimits(0.0, xmax)
    if RalphWF.cathodeToAnodeDistance > 900: hist.GetXaxis().SetLimits(0.0, 120) # nEXO
    hist.SetXTitle("Interaction location (distance from anode) [mm]")
    hist.SetYTitle("Fraction of ionization charge observed")
    hist.SetMinimum(0.0)
    hist.SetMaximum(1.1)
    #hist.SetAxisRange(5, 20)
    graph.SetLineColor(ROOT.kBlack)
    legend.AddEntry(graph, "No screening or cathode effects", "l")

    print "ion only"
    RalphWF.posion = True
    RalphWF.cathsupress = False
    graph2 = make_graph()
    graph2.SetLineColor(ROOT.kBlue)
    graph2.SetLineWidth(2)
    graph2.Draw("l")
    legend.AddEntry(graph2, "Ion screening", "l")

 
    # without the ion, this doesn't do anything to the final value!
    #print "cathode only"
    #RalphWF.posion = False
    #RalphWF.cathsupress = True
    #graph3 = make_graph()
    #graph3.SetLineColor(ROOT.kGreen+1)
    #graph3.Draw("l")
    #legend.AddEntry(graph3, "cathode effect only", "l")
 
    print "ion + cathode"
    RalphWF.posion = True
    RalphWF.cathsupress = True
    graph4 = make_graph()
    graph4.SetLineColor(ROOT.kRed)
    graph4.Draw("l")
    legend.AddEntry(graph4, "Ion screening, cathode effect", "l")


    cathodeToAnodeDistance = RalphWF.cathodeToAnodeDistance
    line = ROOT.TLine(cathodeToAnodeDistance, hist.GetMinimum(), 
        cathodeToAnodeDistance, hist.GetMaximum())
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    line.Draw()

    legend.Draw()
    canvas.Update()
    canvas.Print("ionAndCathodeEffect_%imm.pdf" % cathodeToAnodeDistance)
    # log plot doesn't look much different
    #canvas.SetLogy(1)
    #hist.SetMaximum(1.1)
    #hist.SetMinimum(1e-2)
    #canvas.Print("ionAndCathodeEffect_%imm_log.pdf" % cathodeToAnodeDistance)
    #canvas.SetLogy(0)
    #hist.SetMaximum(1.1)
    #hist.SetMinimum(0)

    if False: # electron lifetime

        print "e- lifetime"
        RalphWF.posion = False
        RalphWF.cathsupress = False
        RalphWF.e_lifetime = 70.0 # microseconds
        graph5 = make_graph()
        graph5.SetLineColor(ROOT.kViolet+1)
        graph5.Draw("l")

        # captured charge
        if False:
            print "e- lifetime + captured charge"
            RalphWF.posion = False
            RalphWF.cathsupress = False
            RalphWF.consider_capturedQ = True
            graph6 = make_graph()
            graph6.SetLineColor(ROOT.kMagenta)
            graph6.Draw("l")
            legend2.AddEntry(graph6, "#tau_{e-}=%i#mus w captured Q" % RalphWF.e_lifetime, "l")

        print "all"
        RalphWF.posion = True
        RalphWF.cathsupress = True
        RalphWF.consider_capturedQ = False
        graph7 = make_graph()
        graph7.SetLineColor(ROOT.kGreen+2)
        graph7.Draw("l")

        legend2.AddEntry(graph, "No screening or cathode effects", "l")
        legend2.AddEntry(graph5, "#tau_{e-}= %i#mus" % RalphWF.e_lifetime, "l")
        legend2.AddEntry(graph2, "Ion screening", "l")
        legend2.AddEntry(graph7, "Ion screening, cathode effect, #tau_{e-}=% i#mus" % RalphWF.e_lifetime, "l")
        legend2.AddEntry(graph4, "Ion screening, cathode effect", "l")

        legend2.Draw()
        canvas.Update()
        canvas.Print("ionAndCathodeEffectWithTau_%ius_%imm.pdf" % (RalphWF.e_lifetime, cathodeToAnodeDistance))

    if not gROOT.IsBatch():
        val = raw_input("press enter to continue") # pause

    # draw the weighting potential
    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)

    # calc Weighting potential from a waveform -- should be same? 
    graph = ROOT.TGraph()
    graph.SetLineColor(ROOT.kBlue)
    graph.SetLineWidth(2)
    graph6 = ROOT.TGraph()
    graph6.SetLineColor(ROOT.kGreen+2)
    graph6.SetLineWidth(2)
    dz = cathodeToAnodeDistance/100.0
    WF = RalphWF.make_WF(1.5, 0.0, 0.0, 1.0, 15, cathodeToAnodeDistance, dz, wfm_length=800)

    RalphWF.diagonal = 6.0 # 6-mm wire pitch
    WF6 = RalphWF.make_WF(1.5, 0.0, 0.0, 1.0, 15, cathodeToAnodeDistance, dz, wfm_length=800)
    for i_point in xrange(len(WF)): 
        z = i_point*dz # distance from anode
        y = WF[i_point] 
        graph.SetPoint(i_point, cathodeToAnodeDistance - z, y) 
        y = WF6[i_point] 
        graph6.SetPoint(i_point, cathodeToAnodeDistance - z, y) 
        if z > cathodeToAnodeDistance: break
    graph.Draw("al")
    hist = graph.GetHistogram()
    xmax = hist.GetXaxis().GetXmax()
    hist.GetXaxis().SetLimits(0.0, xmax)
    hist.SetXTitle("Distance from anode [mm]")
    hist.SetYTitle("Weighting potential")
    hist.SetMinimum(0.0)
    hist.SetMaximum(1.1)
    legend.AddEntry(graph, "Tile design, 3-mm strip pitch", "l")
    if RalphWF.cathodeToAnodeDistance > 900: # nEXO
        hist.GetXaxis().SetLimits(0.0, 120) # zoom in near anode for nEXO setup
        graph6.Draw("l")
        legend.AddEntry(graph6, "Tile design, 6-mm strip pitch", "l")

    if False:
        # calc weighting potential from graph4
        wp_graph = ROOT.TGraph()
        wp_graph.SetLineColor(ROOT.kGreen)
        wp_graph.SetLineWidth(1)
        for i_point in xrange(graph4.GetN()):
            x_val = graph4.GetX()[i_point]
            y_val = graph4.GetY()[i_point]
            y_val = 1.0 - y_val
            wp_graph.SetPoint(i_point, x_val, y_val)
        wp_graph.Draw("l")
        legend.AddEntry(wp_graph, "3mm wire pitch, 2nd method", "l")

    graph2 = ROOT.TGraph()
    graph2.SetLineColor(ROOT.kRed)
    graph2.SetLineWidth(2)
    graph2.SetPoint(0, 0.0, 1.0)
    graph2.SetPoint(1, 6.0, 0.0)
    graph2.SetPoint(2, cathodeToAnodeDistance, 0.0)
    graph2.Draw("l")
    legend.AddEntry(graph2, "Frisch grid 6 mm from anode", "l")
 
    #canvas.SetTopMargin(0.05)
    legend.Draw()
    line.Draw()
    canvas.Update()
    canvas.Print("WeightingPotential_%imm.pdf" % cathodeToAnodeDistance)
    #canvas.SetLogy(1)
    #canvas.Update()
    #canvas.Print("WeightingPotential_%imm_log.pdf" % cathodeToAnodeDistance)

    outfile.Close()


if __name__ == "__main__":
    main()
