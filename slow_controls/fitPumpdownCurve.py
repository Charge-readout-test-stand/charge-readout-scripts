
import sys
import math
import ROOT


root_file_name = sys.argv[1]
root_file = ROOT.TFile(root_file_name)
tree = root_file.Get("tree")

n_entries = tree.GetEntries()

for i in xrange(n_entries):
    tree.GetEntry(i)
    first_time = tree.timeStamp/3600
    first_pressure = tree.pCCG
    print "i", i
    if first_pressure > 0: break
print "first_time:", first_time-first_time, "first_pressure:", first_pressure

canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid()
n_drawn = tree.Draw("pCCG:timeStamp/3600-%s" % first_time,"pCCG>0")
canvas.Update()
#raw_input("enter to continue ")

tree.GetEntry(n_drawn-1)
last_time = tree.timeStamp/3600
last_pressure = tree.pCCG
print "last_time:", (last_time-first_time)/3600, "last_pressure:", last_pressure

# get x and y from TTree::Draw command above:
y = tree.GetV1()
x = tree.GetV2()

# make a graph from x and y
graph = ROOT.TGraph(n_drawn, x, y)
graph.Draw("apl")

# estimate tau:
tau = -(last_time-first_time)/math.log(last_pressure/first_pressure)
if tau > 1.0: tau = 0.68
print "tau:", tau

# construct a fit function:
if "test_20161125_185003" in root_file_name:
    fcn = ROOT.TF1("fcn","[0]*exp(-x/[1])+[2]",24.0,60.0)
    first_pressure = 24.0
else:
    #fcn = ROOT.TF1("fcn","[0]*exp(-x/[1])+[2]",0.5,last_time-first_time+10)
    fcn = ROOT.TF1("fcn","[0]*exp(-x/[1])+[2]",2.0,16.0)
fcn.SetLineColor(ROOT.kRed)
fcn.SetParameter(0, first_pressure)
fcn.SetParameter(1, tau)
fcn.SetParameter(2, 0.0)

fcn.SetParName(0, "First Pressure [1e-6 torr]")
fcn.SetParName(1, "Tau [hour]")
fcn.SetParName(2, "Final Pressure [1e-6 torr]")

# do the fit
graph.Fit(fcn, "R")

fcn.Draw("l same")
canvas.Update()
raw_input("enter to continue ")

fcn.Draw("l")
tree.Draw("pCCG:timeStamp/3600-%s" % first_time,"","same")
fcn.Draw("l same")
canvas.Update()
raw_input("enter to continue ")



