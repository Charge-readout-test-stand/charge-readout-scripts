#!/usr/bin/env python

import os
import sys
import ROOT

"""
This script draws waveforms from nEXOdigi and prints info about them. 
"""

if os.getenv("EXOLIB"):
    try:
        print "loading libEXOROOT"
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
    except:
        print "loading libEXOROOT failed"
        sys.exit()

microsecond = 1.0e3
second = 1.0e9

from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother
from ROOT import EXOTrapezoidalFilter
from ROOT import EXOBaselineRemover
from ROOT import EXODoubleWaveform
from ROOT import TObjString
from ROOT import gROOT
from array import array
def main(filename):
  
    digi_file = ROOT.TFile(filename)
    tree = digi_file.Get("waveformTree")
    n_entries = tree.GetEntries()
    print "%i entries in tree" % n_entries

    canvas = ROOT.TCanvas("canvas", "")  
    canvas.SetGrid()

    tree.SetLineColor(ROOT.kBlue)
    tree.SetMarkerColor(ROOT.kBlue)
    tree.SetMarkerSize(0.8)
    tree.SetMarkerStyle(8)

    for i_entry in xrange(n_entries):

        tree.GetEntry(i_entry)

        print "entry %i | Evt %i | WFLen %i | WFTileId %i | WFLocalId %i | WFChannelCharge %i" % (
            i_entry, 
            tree.EventNumber,
            tree.WFLen,
            tree.WFTileId,
            tree.WFLocalId,
            tree.WFChannelCharge,
        )

        selection = "Entry$==%i" % i_entry
        tree.Draw("WFAmplitude:WFTime",selection,"pl")
        canvas.Update()
        val = raw_input("press enter (q to quit) ") 
        if val == 'q':
            sys.exit()
    
        waveform = array('d', tree.WFAmplitude)
        print len(waveform), tree.WFLen
        exo_wfm = EXODoubleWaveform(waveform, len(waveform))
        get_risetimes(exo_wfm=exo_wfm, wfm_length=len(waveform), sampling_freq_Hz=2e6, skip_short_risetimes=False, label="")
        hist=exo_wfm.GimmeHist()
        hist.SetMarkerSize(0.8)
        hist.SetMarkerStyle(8)
        hist.Draw("PL")
        
        canvas.Update()
        val = raw_input("press enter (q to quit) ") 
        if val == 'q':
            sys.exit()
        

def do_draw(
    exo_wfm,
    title="", 
    extra_wfm=None, 
    extra_wfm2=None,
    vlines=None, # vertical lines
    ):
                            
    if gROOT.IsBatch(): return
    canvas = TCanvas("canvas","do_draw canvas")
    canvas.SetGrid(1,1)
    canvas.cd()
    hist = exo_wfm.GimmeHist("hist")
    hist.SetTitle(title)
    hist.SetLineWidth(2)
    if vlines != None:
      pass
    hist.SetMarkerStyle(8)
    hist.SetMarkerSize(0.7)
    hist.Draw()
    hist_max = hist.GetMaximum()
    hist_min = hist.GetMinimum()
    hist.Draw("p same")
    if extra_wfm:
      hist2 = extra_wfm.GimmeHist("hist2")
      hist2.SetLineColor(kBlue)
      hist2.Draw("l same")
      if hist2.GetMaximum() > hist_max:
        hist_max = hist2.GetMaximum()
      if hist2.GetMinimum() < hist_min:
        hist_min = hist2.GetMinimum()

    if extra_wfm2:
      hist3 = extra_wfm2.GimmeHist("hist3")
      hist3.Draw("l same")
      if hist3.GetMaximum() > hist_max:
        hist_max = hist3.GetMaximum()
      if hist3.GetMinimum() < hist_min:
        hist_min = hist3.GetMinimum()
    hist_max = hist_max*1.1
    hist_min = hist_min - hist_max*0.1
    if vlines: 
      lines = []
      for vline in vlines:
          line = TLine(vline, hist_min_vline, hist_max)
          line.SetLineStyle(2)
          line.SetLineWidth(2)
          line.Draw()
          lines.append(line)
    hist.SetMaximum(hist_max)
    hist.SetMinimum(hist_min)
    canvas.Update()

def do_risetime_calc(rise_time_calculator, threshold_percent, wfm, max_val, period):
    rise_time_calculator.SetFinalThresholdPercentage(threshold_percent)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
      rise_time_calculator.Transform(wfm, wfm)
    return rise_time_calculator.GetFinalThresholdCrossing()*period/microsecond

def get_risetimes(exo_wfm, wfm_length, sampling_freq_Hz,skip_short_risetimes=True,label=""):
    exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)
    new_wfm = EXODoubleWaveform(exo_wfm)
    maw_wfm = EXODoubleWaveform(exo_wfm)

    period = exo_wfm.GetSamplingPeriod()

    # perform some smoothing -- be careful because this changes the rise time
    smoother = EXOSmoother()
    smoother.SetSmoothSize(5)
    smoother.Transform(exo_wfm, new_wfm) 

    smoothed_max = new_wfm.GetMaxValue()
    max_val = new_wfm.GetMaxValue() # smoothed max
    print "max_val", max_val

    rise_time_calculator = EXORisetimeCalculation()
    rise_time_calculator.SetPulsePeakHeight(max_val)
    
    if skip_short_risetimes:
      rise_time_stop10 = 0.0
    else: 
      rise_time_stop10 = do_risetime_calc(rise_time_calculator, 0.10, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop20 = 0.0
    else:
      rise_time_stop20 = do_risetime_calc(rise_time_calculator, 0.20, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop30 = 0.0
    else:
      rise_time_stop30 = do_risetime_calc(rise_time_calculator, 0.30, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop40 = 0.0
    else:
      rise_time_stop40 = do_risetime_calc(rise_time_calculator, 0.40, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop50 = 0.0
    else:
      rise_time_stop50 = do_risetime_calc(rise_time_calculator, 0.50, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop60 = 0.0
    else:
      rise_time_stop60 = do_risetime_calc(rise_time_calculator, 0.60, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop70 = 0.0
    else:
      rise_time_stop70 = do_risetime_calc(rise_time_calculator, 0.70, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop80 = 0.0
    else:
      rise_time_stop80 = do_risetime_calc(rise_time_calculator, 0.80, exo_wfm, max_val, period)

    rise_time_stop90 = do_risetime_calc(rise_time_calculator, 0.90, exo_wfm, max_val, period)
    rise_time_stop95 = do_risetime_calc(rise_time_calculator, 0.95, exo_wfm, max_val, period)

    rise_time_stop99 = do_risetime_calc(rise_time_calculator, 0.99, exo_wfm, max_val, period)

    if not gROOT.IsBatch(): #shows a few rise-times to check
      print "rise times:"
      print "\tmax_val:", max_val
      print "\trise_time_stop50:", rise_time_stop50
      print "\trise_time_stop90:", rise_time_stop90
      print "\trise_time_stop99:", rise_time_stop99
    
    if max_val > 100 and not "PMT" in label and False: do_draw(exo_wfm, "%s after rise-time calc" % label, new_wfm, maw_wfm, vlines=[
      rise_time_stop10,
      rise_time_stop20,
      rise_time_stop30,
      rise_time_stop40,
      rise_time_stop50,
      rise_time_stop60,
      rise_time_stop70,
      rise_time_stop80,
      rise_time_stop90,
      rise_time_stop95,
      rise_time_stop99,
    ])

    maw_wfm.IsA().Destructor(maw_wfm)
    new_wfm.IsA().Destructor(new_wfm)

    return [smoothed_max, rise_time_stop10, rise_time_stop20, rise_time_stop30, rise_time_stop40, rise_time_stop50, rise_time_stop60, rise_time_stop70, rise_time_stop80, rise_time_stop90, rise_time_stop95, rise_time_stop99]


if __name__ == "__main__":

    if len(sys.argv) < 1:
      print "exiting"
      sys.exit(1)

    for filename in sys.argv[1:]:
      main(filename)
