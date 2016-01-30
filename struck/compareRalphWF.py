
# for RalphWF.py:
#import numpy as np
#import matplotlib.pyplot as plt
from RalphWF import make_WF

# for AGS root macro:
from ROOT import gROOT
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TGraph
from ROOT import TLegend


if __name__ == "__main__":
    

    # options
    x = 1.5
    y = 0.0
    z = 0.0 # distance from cathode
    q = 1.0

    canvas = TCanvas("canvas","", 800, 1000)
    legend = TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetFillColor(0)
    legend.SetNColumns(2)
    canvas.Divide(1,2)

    pad1 = canvas.cd(1)
    pad1.SetGrid(1,1)

    #Collection signal on channel X16, WF is numpy array
    # args: x, y, z, q, channel
    WF = make_WF(x, y, z, q, 15)
    graph = TGraph()
    for i_point in xrange(len(WF)):
        t = i_point*0.040
        val = WF[i_point]
        graph.SetPoint(i_point, t, val)
    graph.Draw("alp")
    hist = graph.GetHistogram()
    hist.SetAxisRange(5, 20)
    graph.SetLineWidth(3)
    graph.SetLineColor(2)
    legend.AddEntry(graph, "RalphWF.py", "l")
    print graph.GetY()[len(WF)-1]
        

    gROOT.ProcessLine('.L ralphWF.C+')
    from ROOT import OnePCD
    test = TF1("test", OnePCD, 0.0, 32.0, 4)
    test.SetParameter(0, x) # x
    test.SetParameter(1, y) # y 
    test.SetParameter(2, 17.0-z) # z0 (measured from anode)
    test.SetParameter(3, q) # q 
    test.SetLineWidth(1)
    test.Draw("same")
    legend.AddEntry(test, "ralphWF.C", "l")
    print test.Eval(20.0)

    diffGraph = TGraph()
    for i_point in xrange(graph.GetN()-10):
        #x = graph.GetX()[i_point]

        # this gives better results; so probably there is 
        x = graph.GetX()[i_point+1]

        y = graph.GetY()[i_point]

        diff = y - test.Eval(x)

        diffGraph.SetPoint(i_point, x, diff)

    pad2 = canvas.cd(2)
    pad2.SetGrid(1,1)
    diffGraph.Draw("apl")
    hist = diffGraph.GetHistogram()
    hist.SetYTitle("RalphWF.py - ralphWF.C")
    hist.SetAxisRange(5, 20)
    diffGraph.Draw("apl")

    canvas.cd(1)
    legend.Draw()
    canvas.Update()
    canvas.Print("ralphWfComparison.pdf")

    val = raw_input("") # pause

    #pars = array('d',[0])  
    #variables = array('d',[0.0, 1.5, 17.0])  
    #print OnePCD(pars, variables)


    #plt.figure(2)
    #Induction signal X15
    #WF = make_WF(1.5, 0.0, 0.0, 1, 14)
    #plt.plot(WF)
    #plt.ylim([-0.1,1.1])
    
    
    #plt.figure(3)
    #Induction signal Y16
    #WF = make_WF(1.5, 0.0, 0.0, 1, 45)
    #plt.plot(WF)
    #plt.ylim([-0.1,1.1])

   

