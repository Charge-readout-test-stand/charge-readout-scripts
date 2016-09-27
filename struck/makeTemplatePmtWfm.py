"""
Divide this into 2 files: 1 to compare wfms to the reference and calc chi^2, one to make the reference
Save the reference wfm as some kind of text/json file
"""


import os
import sys
import math
import ROOT
import datetime
ROOT.gROOT.SetBatch(True)

from ROOT import EXOBaselineRemover
from ROOT import EXODoubleWaveform # fails if EXOBaselineRemover not imported first?

from struck import struck_analysis_parameters
filename = sys.argv[1]

print "--> processing", filename

tfile = ROOT.TFile(filename)
tree = tfile.Get("HitTree")
n_entries = tree.GetEntries()

canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid()
canvas.Divide(1,2)
canvas.cd(1)

n_sum = 0.0

for i_entry in xrange(n_entries):
    if n_sum >= 5*5000: break # debugging, 5000 events takes 1 minute

    tree.GetEntry(i_entry)

    slot = tree.HitTree.GetSlot()
    channel = tree.HitTree.GetChannel()
    if channel != 15: continue
    if slot != 1: continue

    graph = tree.HitTree.GetGraph()
    graph.SetLineWidth(2)
    baseline = 0.0
    n_samples_to_average = 10
    for i in xrange(n_samples_to_average):
        baseline += graph.GetY()[i]
    baseline /= n_samples_to_average
    max_val = graph.GetY()[227]
    #print np.amax(graph.GetY())
    energy = max_val - baseline
    if energy < 400: continue # too much noise!


    fcn_string = "(y - %s)*%s" % (baseline, 1.0/energy)
    #print "fcn_string:", fcn_string
    fcn = ROOT.TF2("fcn",fcn_string)
    graph.Apply(fcn)

    wfm = ROOT.EXODoubleWaveform(graph.GetY(),graph.GetN())
    baseline_remover = ROOT.EXOBaselineRemover()
    baseline_remover.SetBaselineSamples(200)
    baseline_remover.Transform(wfm)
    max_val = wfm.GetMaxValue()
    wfm/=max_val
    wfm_squared = ROOT.EXODoubleWaveform(wfm)
    wfm_squared *= wfm

    try:
        sum_wfm += wfm
        sum_squared_wfm += wfm_squared
    except NameError:
        print "making new sum wfms..."
        sum_wfm = EXODoubleWaveform(wfm)
        sum_squared_wfm = EXODoubleWaveform(wfm_squared)
    n_sum += 1

    sum_hist = sum_wfm.GimmeHist("sum_hist")
    sum_hist.Scale(1.0/n_sum)
    sum_hist.SetLineWidth(6)
    sum_hist.SetLineColor(ROOT.kRed)

    wfm_hist = wfm.GimmeHist("wfm_hist")
    wfm_hist.SetLineWidth(2)
    wfm_hist.SetLineColor(ROOT.kBlue)

    # keep a normalized version of the sum hist
    pad1 = canvas.cd(1)
    pad1.SetGrid()
    sum_hist.Draw()
    wfm_hist.Draw("same")

    pad2 = canvas.cd(2)
    pad2.SetGrid()
    diff_hist = wfm_hist.Clone("diff_hist")
    diff_hist.Add(sum_hist, -1.0)
    diff_hist.Draw()

    print "---> entry %i, max= %i, %i wfms in sum" % (i_entry, energy, n_sum)
    canvas.Update()

    if not ROOT.gROOT.IsBatch():
        val = raw_input("enter to continue (q to quit, b = batch): ")
        if val == 'q':
            sys.exit()
        if val == 'b':
            ROOT.gROOT.SetBatch(True)
    # end loop over events


# write out the hist into a python script
sum_squared_hist = sum_squared_wfm.GimmeHist("sum_squared_hist")
sum_squared_hist.Scale(1.0/n_sum)
text_file = file("pmt_reference_signal.py","w")
text_file.write("# this script was auto-generated on %s\n" % datetime.datetime.now())
text_file.write("# %i events from %s \n\n" % (n_sum, filename))
text_file.write("import ROOT \n")
text_file.write("hist = ROOT.TH1D('pmt_ref_hist','',800, -0.5, 799.5) \n")
for i in xrange(sum_hist.GetNbinsX()):
    i_bin = i+1
    sum_val = sum_hist.GetBinContent(i_bin)
    sum_sq_val = sum_squared_hist.GetBinContent(i_bin)
    error = math.sqrt(sum_sq_val - sum_val*sum_val)
    sum_hist.SetBinError(i_bin, error)
    text_file.write("hist.SetBinContent(%i,%6e) \n" % (i_bin, sum_val))
    text_file.write("hist.SetBinError(%i,%6e) \n" % (i_bin, error))

text_file.write("""
if __name__ == '__main__':
    canvas = ROOT.TCanvas('canvas','')
    canvas.SetGrid(1,1)
    hist.Draw('')
    hist2 = hist.Clone('hist2')
    hist2.SetLineColor(ROOT.kRed)
    hist2.SetLineWidth(2)
    hist2.Draw('hist same')
    raw_input('any key to continue')

""")
text_file.close()
sum_hist.SetLineWidth(2)

out_file = ROOT.TFile("sumPMTWfm.root","recreate")
sum_hist.Write("sum_hist")
out_file.Close()

