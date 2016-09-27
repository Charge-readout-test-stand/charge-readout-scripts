"""
Compare PMT signals to template signal to see chi^2 vals.
"""


import os
import sys
import math
import ROOT
import datetime
ROOT.gROOT.SetBatch(True)

import pmt_reference_signal

from ROOT import EXOBaselineRemover
from ROOT import EXODoubleWaveform # import fails if EXOBaselineRemover not imported first?

from struck import struck_analysis_parameters

# default file on ubuntu DAQ:
#filename = "~/2016_09_19_overnight/tier1/tier1_SIS3316Raw_20160919230343_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root"
filename = "~/2016_09_19_overnight/tier1/tier1_SIS3316Raw_20160919225739_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root"
if len(sys.argv) > 1: # use command-line argument otherwise
    filename = sys.argv[1]

print "--> processing", filename

tfile = ROOT.TFile(filename)
tree = tfile.Get("HitTree")
n_entries = tree.GetEntries()

canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid()
canvas.Divide(1,2)
canvas.cd(1)

pmt_hist = pmt_reference_signal.hist
n_big = 0

pmt_channel = struck_analysis_parameters.pmt_channel
# pmt electronics noise, in ADC units
calibration = struck_analysis_parameters.calibration_values[pmt_channel]
pmt_electronics_noise = struck_analysis_parameters.rms_keV[pmt_channel]/calibration
#print pmt_channel, struck_analysis_parameters.rms_keV[pmt_channel], struck_analysis_parameters.calibration_values[pmt_channel]

baseline_remover = ROOT.EXOBaselineRemover()
baseline_remover.SetBaselineSamples(200)

basename = os.path.splitext(os.path.basename(filename))[0]
plot_name = "pmt_%s" % basename

canvas.Print("%s.pdf[" % plot_name) # open multi-page PDF

for i_entry in xrange(n_entries):
    #if i_entry >= 32*100: break # 100 events
    if ROOT.gROOT.IsBatch() and n_big >= 100: break # 100 events = ~ 8MB file

    tree.GetEntry(i_entry)

    slot = tree.HitTree.GetSlot()
    channel = tree.HitTree.GetChannel()
    if channel != 15: continue
    if slot != 1: continue

    graph = tree.HitTree.GetGraph()
    wfm = ROOT.EXODoubleWaveform(graph.GetY(),graph.GetN())
    baseline_remover.Transform(wfm)
    wfm_hist = wfm.GimmeHist("wfm_hist")

    #wfm_hist.SetAxisRange(0,650)
    for i in xrange(wfm_hist.GetNbinsX()):
        wfm_hist.SetBinError(i+1, 0.0)
    max_val = wfm_hist.GetMaximum()
    pmt_max = pmt_hist.GetMaximum() 
    #print pmt_hist.GetBinError(300)/pmt_max # just checking...
    pmt_hist.Scale(max_val/pmt_max)

    pad = canvas.cd(1)
    pad.SetGrid()
    legend = ROOT.TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetNColumns(2)
    wfm_hist.SetLineColor(ROOT.kRed)
    wfm_hist.SetLineWidth(2)
    wfm_hist.SetTitle("")
    wfm_hist.SetXTitle("Time [samples]")
    wfm_hist.Draw("hist")
    pmt_hist.Draw("same")
    wfm_hist.Draw("hist same")
    legend.AddEntry(wfm_hist, "event %i, %i ADC units, %i keV" % (i_entry/32, max_val, max_val*calibration))
    legend.AddEntry(pmt_hist, "template signal")
    legend.Draw()

    pad = canvas.cd(2)
    pad.SetGrid()
    diff_hist = wfm_hist.Clone("diff_hist")
    diff_hist.Add(pmt_hist, -1.0)
    diff_hist.SetMarkerColor(ROOT.kBlack)
    diff_hist.SetMarkerStyle(8)
    diff_hist.SetMarkerSize(0.8)
    chi2 = 0.0
    #print "pmt_electronics_noise:", pmt_electronics_noise
    for i in xrange(pmt_hist.GetNbinsX()):
        val = diff_hist.GetBinContent(i+1)
        error = math.sqrt(
                    math.pow(pmt_hist.GetBinError(i+1), 2.0) + \
                    math.pow(pmt_electronics_noise, 2.0))
        diff_hist.SetBinError(i+1,error)
        diff_hist.SetBinContent(i+1, val)
        if error > 0:
            #diff_hist.SetBinContent(i+1, val/error)
            chi2 += val*val/(error*error)
    #print "my chi2:", chi2
    #diff_hist.SetAxisRange(0,650)
    diff_hist.SetTitle("difference hist: #chi^{2}/DOF = %.1f/%i = %.2f" % (chi2, i, chi2/i))
    diff_hist.Draw("x0")
    if chi2/i < 2.0: 
        continue
    n_big += 1

    print "---> event %i, max= %i, my chi2: %.3f" % (i_entry/32, max_val, chi2)
    canvas.Update()
    canvas.Print("%s.pdf" % plot_name) # add to multi-page PDF

    if not ROOT.gROOT.IsBatch():
        val = raw_input("enter to continue (q to quit, b = batch, s=break): ")
        if val == 'q':
            sys.exit()
        if val == 'b':
            ROOT.gROOT.SetBatch(True)
        if val == 's':
            break
    # end loop over events

print "%i above threshold" % n_big
canvas.Print("%s.pdf]" % plot_name) # close multi-page PDF

