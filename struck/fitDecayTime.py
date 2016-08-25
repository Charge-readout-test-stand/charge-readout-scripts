#!/usr/bin/env python

import os
import sys
import time
import math
import datetime
import numpy as np
from optparse import OptionParser
import ROOT

from ROOT import TMath
from ROOT import TF1
from ROOT import gROOT
from ROOT import TFile
from ROOT import TChain
from ROOT import TTree
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TH1D
from ROOT import gSystem
from ROOT import TRandom3
from ROOT import kBlue
from ROOT import kRed
from ROOT import gStyle

if os.getenv("EXOLIB") is not None:
    try:
        gSystem.Load("$EXOLIB/lib/libEXOROOT")
    except:
        pass

try:
    from ROOT import CLHEP
    microsecond = CLHEP.microsecond
    second = CLHEP.second
except ImportError:
    # workaround for our Ubuntu DAQ, which doesn't have CLHEP -- CLHEP unit of time is ns:
    microsecond = 1.0e3
    second = 1.0e9
from ROOT import EXOBaselineRemover
from ROOT import EXODoubleWaveform
from ROOT import EXORisetimeCalculation
from ROOT import EXOSmoother
from ROOT import EXOPoleZeroCorrection
from ROOT import TObjString

from array import array

# definition of calibration constants, decay times, channels
import struck_analysis_parameters

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)


#----------------------------------------------------------------------------------------
#-----------------------------Constants to use-------------------------------------------
debug = True
debug = False
gROOT.SetBatch(debug)

#plot_name = "DecayTimeHist.pdf"

sampling_period = (1/struck_analysis_parameters.sampling_freq_Hz)*second #ns

#Get sample for fit (20us to 32us (32 is the end))
fitstart = int(20.0/(sampling_period/microsecond)) #sample
fitstop = int(32.0/(sampling_period/microsecond))  #sample

print fitstart, fitstop

reporting_period = 1000

drift_length = struck_analysis_parameters.drift_length #mm
n_baseline_samples = struck_analysis_parameters.n_baseline_samples
end_baseline_samples = 600
peaking_time = 50
gap_time = 250

threshold = 200

channels = struck_analysis_parameters.channels
n_chargechannels = struck_analysis_parameters.n_chargechannels
pmt_channel = struck_analysis_parameters.pmt_channel

exp_decay = TF1("exp_decay","[0]*exp(-x/[1])",fitstart, fitstop)

dstart = 0
dend = 2000
landau = TF1("landau","[0]*TMath::Landau(x,[1],[2],0)", dstart, dend)

tguess = 200 /(sampling_period/microsecond)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

# set up a canvas
canvas = TCanvas("canvas","",900,700)
canvas.SetGrid(1,1)

#ROOT.SetMemoryPolicy( ROOT.kMemoryStrict )

def diff(value, fit, rms):
    diff = (value-fit)/rms # approx RMS noise
    return diff

def WasSignal(ch, max_val, baseline, rms):
    #Determine if there was a signal on the channel
    #Check if above threshold.  Max is average of last 200 samples
    #so should filter induction signals.
    
    #If Waveform is a TGraph
    #max_val = TMath.MaxElement(wfgraph.GetN(),wfgraph.GetY())
    
    isSig = False

    #if (max_val - baseline) > threshold:
    if (max_val - baseline) > 10*rms:
        isSig = True
    
    #Only for Charge Channels
    if ch == pmt_channel: 
        isSig = False

    return isSig

def KillBaseline(wfgraph, baseline):
    for i in xrange(wfgraph.GetN()):
        wfgraph.GetY()[i] = wfgraph.GetY()[i] - baseline

def DoFit(wfgraph, max_val):
    exp_decay.SetParameters(max_val, tguess)
    fit_result = wfgraph.Fit("exp_decay","QWBRS")
    
    amp = exp_decay.GetParameter(0)
    tau = (exp_decay.GetParameter(1)*sampling_period/microsecond)
    chi2 = exp_decay.GetChisquare()/exp_decay.GetNDF()
    
    if debug:
        print "Error in decay:", tau, "+/-", exp_decay.GetParError(1)*sampling_period/microsecond

    return amp, tau, chi2

def process_files(filenames, check_channel):
 
    tree = TChain("HitTree")
    for tfile in filenames:
      tree.Add(tfile)
    
    n_entries = tree.GetEntries()
    print "Got chain with %i Entries" % n_entries

    fithist_list = []
    for ch in channels:
        fithist = TH1D("tau%i" % ch, "Ch %i Decay Time" % ch, 100, dstart, dend)
        fithist.SetDirectory(0)
        fithist.SetLineColor(ROOT.kBlue)
        fithist.SetLineWidth(2)
        fithist.SetXTitle("#tau [#mus]")
        fithist.SetYTitle("Counts / %.1f #mus" % fithist.GetBinWidth(1))
        fithist_list.append(fithist)

    for i_entry in xrange(n_entries):
        tree.GetEntry(i_entry)
        htree = tree.HitTree

        channel = int(htree.GetSlot()*16 + htree.GetChannel()) #Channel in Struck
        

        if i_entry%100000==0:
            print "percent done %f", (i_entry/float(n_entries))*100
            #print "Size of hlist: %f, htree: %f, func: %f, canvas: %f" % (sys.getsizeof(fithist_list),
            #                                                              sys.getsizeof(htree),
            #                                                              sys.getsizeof(exp_decay),
            #                                                              sys.getsizeof(canvas))

        if int(channel) != int(check_channel): continue
        
        #Get TGraph and a numpy array for the math
        wfgraph = htree.GetGraph()
        wfarray = np.frombuffer(htree.GetWaveformArray(), np.int32, htree.GetNSamples())
       
        max_val  = np.mean(wfarray[fitstart:fitstop])
        baseline = np.mean(wfarray[:n_baseline_samples])
        rms = np.std(wfarray[:n_baseline_samples] - baseline)

        KillBaseline(wfgraph, baseline)

        if not WasSignal(channel, max_val, baseline, rms): continue      

        #Fit the Waveform
        amp, tau, chi2 = DoFit(wfgraph, max_val)
        chi2 = chi2/rms**2
        
        if chi2 > 1.5: continue
        
        fithist_list[channel].Fill(tau)

        if debug:
            title = "ch = %i, Amp = %f, tau = %f, chi2 = %f " % (channel, amp, tau, chi2)
            print title
            wfgraph.SetTitle("Channel %i Max is %f base is %f" % (channel, max_val, baseline) )
            wfgraph.Draw()
            canvas.Update()
            raw_input()
            canvas.Clear()
        
        wfgraph.IsA().Destructor(wfgraph)

    plot_name = "~/2016_08_15_8th_LXe_overnight/DecayTimes/Testing/DecayTimeHist_ch%i.pdf" % int(check_channel)
    
    canvas.Print("%s[" % plot_name)
    
    for fiti, fithist in enumerate(fithist_list):
        if int(fiti) != int(check_channel): continue
        landau.SetParameter(1, fithist.GetBinCenter(fithist.GetMaximumBin()))
        landau.SetParameter(2, 100) 
        landau.SetParameter(0, fithist.GetMaximum()) 
        fit_result = fithist.Fit("landau", "QWBRS")
        print "Fit = ", landau.GetParameter(1), "+/-", landau.GetParError(1), "Entries = ", fithist.GetEntries()
        fithist.SetTitle(fithist.GetTitle()+ " tau = %f, error = %f, ents = %f" % (landau.GetParameter(1), landau.GetParError(1), fithist.GetEntries()))
        fithist.Draw()
        canvas.Update()
        #raw_input("Enter to continue.")
        canvas.Print("%s" % plot_name)

    canvas.Print("%s]" % plot_name) # close multi-page canvas


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [channel, tier1 root files] using default for now"
        #sys.exit(1)
        filenames = ["/home/teststand/2016_08_15_8th_LXe_overnight/tier1/tier1_SIS3316Raw_20160816023917_8thLXe_126mvDT_cell_full_cath_1700V_100cg_overnight__1-ngm.root"]
        #filenames = ["/home/teststand/2016_08_15_8th_LXe_overnight/tier1/tier1_SIS3316Raw_20160816025*root"]
        ch = 21
        process_files(filenames, ch)
    else:
        ch = sys.argv[1]
        filenames = sys.argv[2:]
        process_files(filenames, ch)



