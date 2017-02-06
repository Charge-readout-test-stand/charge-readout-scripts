"""
Script to generate template PMT wfm
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

# file on ubuntu DAQ
filename = "/home/teststand/2016_09_19_overnight/tier1/tier1_SIS3316Raw_20160919230343_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root"
if len(sys.argv) > 1:
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

pmt_channel = struck_analysis_parameters.pmt_channel
calibration = struck_analysis_parameters.calibration_values[pmt_channel]

basename = os.path.splitext(os.path.basename(filename))[0]
plot_name = "pmt_ref_wfm_%s" % basename
canvas.Print("%s.pdf[" % plot_name) # open multi-page PDF


n_baseline_samples = int(struck_analysis_parameters.n_baseline_samples)

baseline_remover = ROOT.EXOBaselineRemover()
baseline_remover.SetBaselineSamples(n_baseline_samples)


# retrieve NGM config info:
ngm_config = tfile.Get("NGMSystemConfiguration")
card = ngm_config.GetSlotParameters().GetParValueO("card",0)
sampling_frequency_Hz = struck_analysis_parameters.get_clock_frequency_Hz_ngm(card.clock_source_choice)
pretriggerdelay = card.pretriggerdelay_block[0] 
gate_window_length_block = card.gate_window_length_block[0]
print "pretriggerdelay:", pretriggerdelay
print "trigger_time:", pretriggerdelay/sampling_frequency_Hz*1e6

max_time_hist = ROOT.TH1D("max_time_hist","",gate_window_length_block,0,gate_window_length_block)

for i_entry in xrange(n_entries):
    #if n_sum >= 5000: break # debugging, 5000 events takes ~5 minutes

    tree.GetEntry(i_entry)

    # check whether this is the PMT channel
    slot = tree.HitTree.GetSlot()
    channel = tree.HitTree.GetChannel()
    if channel != pmt_channel % 16: continue
    if slot != pmt_channel/16: continue

    graph = tree.HitTree.GetGraph()
    wfm = ROOT.EXODoubleWaveform(graph.GetY(),graph.GetN())
    wfm.SetSamplingFreq(sampling_frequency_Hz/1e9)
    baseline_remover.Transform(wfm)
    baseline_rms = baseline_remover.GetBaselineRMS()
    max_val = wfm.GetMaxValue()
    energy = max_val*calibration
    if max_val/baseline_rms < 10: continue # too much noise!
    #if energy < 10: continue # too much noise!
    wfm/=max_val # normalize to 1
    wfm_hist = wfm.GimmeHist("wfm_hist")
    n_bins = wfm_hist.GetNbinsX()
    bin_width = wfm_hist.GetBinWidth(1)
    max_bin = wfm_hist.GetMaximumBin()
    max_time_hist.Fill(max_bin)
    is_skipped = 0
    if max_bin < pretriggerdelay+25 or max_bin > pretriggerdelay+35: # skip pulser triggers
        print "--> skipping this wfm, max_bin=", max_bin
        continue
        is_skipped = 1
    wfm_hist.SetAxisRange(0,wfm_hist.GetBinCenter(n_baseline_samples)) # skip random concidences
    new_max = wfm_hist.GetMaximum()
    if new_max > 0.1: 
        print "---> skipping for high value in first 200 bins"
        continue
        is_skipped = 1
    wfm_hist.SetAxisRange(wfm_hist.GetBinCenter(400),wfm_hist.GetBinCenter(n_bins) + bin_width) # skip randon coincidences
    new_max = wfm_hist.GetMaximum()
    if new_max > 0.2:  # use 20% as threshold in region that includes ringing
        print "---> skipping for high value in last  bins"
        continue
        is_skipped = 1
    wfm_hist.SetAxisRange(wfm_hist.GetBinCenter(500),wfm_hist.GetBinCenter(n_bins) + bin_width) # skip randon coincidences
    new_max = wfm_hist.GetMaximum()
    if new_max > 0.1: # use 10% at late times
        print "---> skipping for high value in last  bins"
        continue
        is_skipped = 1
    wfm_hist.SetAxisRange(0, wfm_hist.GetNbinsX())

    wfm_squared = ROOT.EXODoubleWaveform(wfm)
    wfm_squared *= wfm
    # add this wfm to the sum:
    try:
        sum_wfm += wfm
        sum_squared_wfm += wfm_squared
    except NameError:
        print "making new sum wfms..."
        sum_wfm = EXODoubleWaveform(wfm)
        sum_squared_wfm = EXODoubleWaveform(wfm_squared)
    n_sum += 1

    sum_hist = sum_wfm.GimmeHist("sum_hist")
    sum_hist.SetTitle("")
    sum_hist.Scale(1.0/n_sum) # normalize to 1

    # format sum hist for drawing
    sum_hist.SetLineWidth(2)
    sum_hist.SetLineColor(ROOT.kRed)
    sum_hist.SetMarkerColor(ROOT.kBlack)
    sum_hist.SetMarkerStyle(8)
    sum_hist.SetMarkerSize(0.4)

    # format wfm hist for drawing
    wfm_hist.SetLineWidth(2)
    wfm_hist.SetLineColor(ROOT.kBlue)

    # construct a difference hist:
    diff_hist = wfm_hist.Clone("diff_hist")
    diff_hist.Add(sum_hist, -1.0)
    err_hist = wfm_hist.Clone("err_hist")

    # calculate errors
    sum_squared_hist = sum_squared_wfm.GimmeHist("sum_squared_hist")
    sum_squared_hist.Scale(1.0/n_sum)
    for i in xrange(sum_hist.GetNbinsX()):
        i_bin = i+1
        sum_val = sum_hist.GetBinContent(i_bin)
        sum_sq_val = sum_squared_hist.GetBinContent(i_bin)
        error = math.sqrt(sum_sq_val - sum_val*sum_val)
        sum_hist.SetBinError(i_bin, error)
        err_hist.SetBinContent(i_bin, 0.0)
        err_hist.SetBinError(i_bin, error)
        diff_hist.SetBinError(i_bin, 0.0)

    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.AddEntry(sum_hist, "sum after %i wfms" % n_sum)
    legend.AddEntry(wfm_hist, "event %i, %i keV = %i ADC units" % (i_entry/32, max_val*calibration, max_val))

    # draw this wfm and the new sum wfm, with errors
    pad = canvas.cd(1)
    pad.SetGrid()
    sum_hist.Draw()
    wfm_hist.Draw("hist same")
    legend.Draw()
    #wfm_squared.GimmeHist("wfm_sq_hist").Draw("same")

    # draw difference between this wfm and the new sum wfm
    pad = canvas.cd(2)
    pad.SetGrid()
    diff_hist.SetTitle("difference")
    #diff_hist.Draw("hist")
    diff_hist.SetMarkerColor(ROOT.kBlack)
    diff_hist.SetMarkerStyle(8)
    diff_hist.SetMarkerSize(0.8)
    diff_hist.Draw("p")
    err_hist.Draw("same")
    diff_hist.Draw("p same")

    print "---> entry %i, max= %i, %i wfms in sum" % (i_entry, energy, n_sum)
    canvas.Update()
    if n_sum <= 50: # 50 wfms = ~ 6MB file
        canvas.Print("%s.pdf" % plot_name) # add to multi-page PDF

    if not ROOT.gROOT.IsBatch():
        if not is_skipped: continue
        val = raw_input("enter to continue (q to quit, b = batch s = break from loop): ")
        if val == 'q':
            sys.exit()
        if val == 'b':
            ROOT.gROOT.SetBatch(True)
        if val == 's':
            break

    # end loop over events

print "%i events in sum" % n_sum
canvas.Print("%s.pdf]" % plot_name) # close multi-page PDF

# write out the sum hist into a python script
diff_hist = sum_hist.Clone("diff_hist")
diff_hist.Add(sum_hist, -1.0)
sum_squared_hist = sum_squared_wfm.GimmeHist("sum_squared_hist")
sum_squared_hist.Scale(1.0/n_sum)
text_file_name = "pmt_reference_signal_%i.py" % n_sum
text_file = file(text_file_name,"w")
text_file.write("# this script was auto-generated on %s\n" % datetime.datetime.now())
text_file.write("# %i events from %s \n\n" % (n_sum, filename))
text_file.write("import ROOT \n")
n_bins = sum_hist.GetNbinsX()
text_file.write("hist = ROOT.TH1D('pmt_ref_hist','',%i, %f, %f) \n" % (
    n_bins,
    sum_hist.GetBinLowEdge(1),
    sum_hist.GetBinLowEdge(n_bins) + sum_hist.GetBinWidth(1)
))
for i in xrange(sum_hist.GetNbinsX()):
    i_bin = i+1
    sum_val = sum_hist.GetBinContent(i_bin)
    sum_sq_val = sum_squared_hist.GetBinContent(i_bin)
    error = math.sqrt(sum_sq_val - sum_val*sum_val)
    sum_hist.SetBinError(i_bin, error)
    diff_hist.SetBinError(i_bin, error)
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
print "results written to", text_file_name

# Print the sum hist
canvas.cd(1)
sum_hist.SetTitle("sum hist after %i wfms" % n_sum)
sum_hist.Draw()
canvas.cd(2)
diff_hist.SetTitle("errors on sum hist")
diff_hist.Draw()
canvas.Update()
canvas.Print("%s_%i.pdf" % (plot_name, n_sum)) 

# draw max times
canvas = ROOT.TCanvas("canvas2","")
canvas.SetGrid()
max_time_hist.SetLineColor(ROOT.kBlue)
max_time_hist.SetLineWidth(2)
mean = max_time_hist.GetMean()
rms = max_time_hist.GetRMS()
title = "Max time hist: %i entries, mean: %.1f, RMS: %.1f" % (max_time_hist.GetEntries(), mean, rms)
max_time_hist.SetTitle(title)
line = ROOT.TLine(pretriggerdelay, 0, pretriggerdelay, max_time_hist.GetMaximum()*1.1)
line.SetLineWidth(2)
line.SetLineStyle(2)
max_time_hist.SetMaximum(max_time_hist.GetMaximum()*1.1)
max_time_hist.Draw()
max_time_hist.SetXTitle("PMT max time [sample]")
line.Draw()
canvas.Update()
canvas.Print("%s_max_times_lin.pdf" % plot_name) 
canvas.SetLogy(1)
canvas.Update()
canvas.Print("%s_max_times_log.pdf" % plot_name) 
max_time_hist.SetAxisRange(pretriggerdelay-10, pretriggerdelay+70)
canvas.Update()
canvas.Print("%s_max_times_zoom.pdf" % plot_name) 

