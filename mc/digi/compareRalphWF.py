
# for RalphWF.py:
#import numpy as np
#import matplotlib.pyplot as plt
import sys
from array import array
from RalphWF import make_WF

# for AGS root macro:
from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TGraph
from ROOT import TLegend


if __name__ == "__main__":
    
    #channel = 16 # X16
    do_divide = False # for drawing difference; some issues with canvas updating

    # options
    x = 1.5
    y = 0.0
    z = 0.0 # distance from cathode
    q = 1.0

#x:  value0 0.00613201
#y:  value1 1.51218
#z:  value2 0.330198
#q: 3 chnam3 q value3 -23255.5

    # from Manisha's fit:
    x = 0.00613201
    y =  1.51218
    z =  0.330198
    #q =  -23255.5

    gROOT.ProcessLine('.L ralphWF.C+')
    from ROOT import OnePCD
    from ROOT import TransformCoord
    par = array('d', [0.0]*4)
    par[0] = x
    par[1] = y
    par[2] = z
    par[3] = q
    test = TF1("test", OnePCD, 0.0, 32.0, 4)

    #canvas = TCanvas("canvas","", 800, 1000)
    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    canvas.SetLeftMargin(0.15)
    canvas.Print("ralphWfComparison.pdf[")

    if do_divide:
        canvas.Divide(1,2)
        pad1 = canvas.cd(1)
        pad1.SetGrid(1,1)
        pad2 = canvas.cd(2)
        pad2.SetGrid(1,1)

    diffGraph = TGraph()
    graph = TGraph()

    for channel in xrange(60):

        legend = TLegend(0.15, 0.91, 0.9, 0.99)
        legend.SetFillColor(0)
        legend.SetNColumns(2)

        if do_divide:
            canvas.Divide(1,2)
            pad1 = canvas.cd(1)
            pad1.SetGrid(1,1)

        #Collection signal on channel X16, WF is numpy array
        # args: x, y, z, q, channel
        WF = make_WF(x, y, z, q, channel)
        for i_point in xrange(len(WF)):
            t = i_point*0.040
            val = WF[i_point]
            graph.SetPoint(i_point, t, val)
        print "len(WF)", len(WF)
        graph.Draw("alp")
        hist = graph.GetHistogram()
        hist.GetYaxis().SetTitleOffset(1.5)
        hist.SetXTitle("Time [#mus]")
        hist.SetYTitle("ch %i Q" % channel)
        y_max = hist.GetMaximum()
        y_min = hist.GetMinimum()
        print "\t hist y_max", y_max
        hist.SetAxisRange(5, 20)
        graph.SetLineWidth(2)
        graph.SetLineColor(2)
        legend.AddEntry(graph, "RalphWF.py", "l")
        print "\t final val from RalphWF.py:", graph.GetY()[len(WF)-1]

        P = array('d', [0.0]*4)
        TransformCoord(par, P, channel)
        print "\t par:", par[0], par[1], par[2], par[3]
        print "\t P:", P[0], P[1], P[2], P[3]

        test.SetParameter(0, P[0]) # x
        test.SetParameter(1, P[1]) # y 
        test.SetParameter(2, 18.16-P[2]) # z0 (measured from anode)
        test.SetParameter(3, P[3]) # q 
        test.SetLineWidth(3)
        test.SetLineStyle(7)
        test.Draw("same")
        print "\t test max", test.GetMaximum()
        print "\t test min", test.GetMinimum()
        if test.GetMaximum() > y_max: y_max = test.GetMaximum()
        hist.SetMaximum(y_max*1.2)
        legend.AddEntry(test, "ralphWF.C", "l")
        legend.Draw()
        print "\t test fcn(20 microseconds):", test.Eval(20.0)

        if do_divide:
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
            hist.GetYaxis().SetTitleOffset(1.3)
            hist.SetYTitle("RalphWF.py - ralphWF.C")
            hist.SetXTitle("Time [#mus]")
            hist.SetAxisRange(5, 20)
            diffGraph.Draw("apl")

        canvas.Update()
        canvas.Print("ralphWfComparison.pdf")

        if not gROOT.IsBatch():
            val = raw_input("channel %i | q=quit, p=print, enter to continue... " % channel) # pause
            if val == 'q': break
            if val == 'p': 
                canvas.Print("ralphWfComparison_ch%i.pdf" % channel)

    canvas.Print("ralphWfComparison.pdf]")

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

   

