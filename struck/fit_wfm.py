"""
Fit one charge signal wfm
"""

import os
import sys
import math
import time
from array import array

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TGraph
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle
from ROOT import gSystem
from ROOT import TLine


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

# be sure to use the "+" -- it made fitting about 30x faster!
gROOT.ProcessLine('.L myfunc.C+')
from ROOT import OnePCD
from ROOT import TwoPCDsOneZ

gSystem.Load("$EXOLIB/lib/libEXOROOT")
from ROOT import CLHEP
from ROOT import EXODoubleWaveform
from ROOT import EXOBaselineRemover

# definition of calibration constants, decay times, channels
import struck_analysis_parameters


def do_fit(exo_wfm, canvas, i_entry, rms, doTwoPCDs=False):

    print "-----------------------------------------------------"
    print "starting fit"
    print "-----------------------------------------------------"

    #-------------------------------------------------------------------------------
    # options:
    #-------------------------------------------------------------------------------

    # fit range:
    fit_min = 7
    fit_max = 19
    drift_velocity = 1.7

    #-------------------------------------------------------------------------------

    print "rms: %.2f" %  rms

    # setup the fit function
    if doTwoPCDs:
        test = TF1("test",TwoPCDsOneZ, fit_min, fit_max, 7)
    else:
        test = TF1("test",OnePCD, fit_min, fit_max, 4)

    # set some variable names:
    test.SetParName(0, "x for PCD 0")
    test.SetParName(1, "y for PCD 0")
    test.SetParName(2, "z for PCDs 0 and 1")
    test.SetParName(3, "q for PCD 0")

    # initial guesses:
    test.SetParameter(0, 0) # x
    test.SetParameter(1, 0) # y
    test.SetParameter(2, 18.5) # z0


    # this works best for pure induction signals...
    amplitude_estimate = exo_wfm.GetMaxValue()

    # this works best for collection + induction
    waveform_length = exo_wfm.size()
    amplitude_estimate = (exo_wfm[waveform_length-1] + exo_wfm[waveform_length-2]) / 2.0
    print "amplitude_estimate: %.2f" % amplitude_estimate
    test.SetParameter(3, amplitude_estimate) # q


    if doTwoPCDs:
        test.SetParName(4, "x for PCD 1")
        test.SetParName(5, "y for PCD 1")
        test.SetParName(6, "q for PCD 1")

        # assume the 2nd PCD contributes some induction signal
        test.SetParameter(4, 0) # x
        test.SetParameter(5, 0.1) # y
        test.SetParameter(6, amplitude_estimate*3.0) # q1
        
    pad1 = canvas.cd(1)
    test.Draw() 
    hist = test.GetHistogram()
    hist.SetXTitle("time [#mus]");
    hist.SetYTitle("charge [arb]");

    wfm_hist = exo_wfm.GimmeHist()

    # set bin errors:
    for i_bin in xrange(wfm_hist.GetNbinsX()):
        wfm_hist.SetBinError(i_bin, rms) # approx. rms
    wfm_hist.SetLineColor(TColor.kRed)
    wfm_hist.SetLineWidth(2)
    title = "Y23, entry %i before fit" % i_entry
    #wfm_hist.SetAxisRange(fit_min-1, fit_max+1)
    wfm_hist.SetTitle(title)
    wfm_hist.SetYTitle("Energy [keV]")
    wfm_hist.Draw("hist")
    test.Draw("same")

    canvas.Update()
    raw_input("enter to continue ")

    print "doing fit..."
    fit_start = time.clock() # keep track of fit start

    # fit options:
    # S -- save output to fit_result
    # N -- don't store the fit function graphics with the histogram
    # R -- use fit fcn's range
    # M -- more; look for new minimum 
    fit_result = wfm_hist.Fit(test, "SNR")

    fit_stop = time.clock() # keep track of fit stop
    title = "Y23, entry %i after fit with %i PCD(s)" % (i_entry, 1 + doTwoPCDs)
    wfm_hist.SetTitle(title)
    wfm_hist.SetAxisRange(fit_min-1, fit_max+1)
    pad1 = canvas.cd(1)
    wfm_hist.Draw("hist")
    test.Draw("same")
    drift_stop = 8.0 + test.GetParameter(2)/drift_velocity
    print "drift_stop [microseconds]: %.2f" % drift_stop
    line = TLine(drift_stop, wfm_hist.GetMinimum(), drift_stop, wfm_hist.GetMaximum())
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    line.SetLineColor(TColor.kBlue)
    line.Draw()
    chi2 = fit_result.Chi2()
    prob = fit_result.Prob()
    ndf = fit_result.Ndf()
    status = fit_result.Status()
    print "fit results:"
    print "\tchi2: %.2f" % chi2
    print "\tprob", prob
    print "\tn dof", ndf
    print "\tchi2 / dof: %.2f" % (chi2/ndf) 
    print "\tstatus", status
    print "\t%.1f seconds" % (fit_stop - fit_start)

    # residuals hist
    residHist = wfm_hist.Clone("residHist")
    residHist.SetTitle("Entry %i" % i_entry)
    residHist.SetYTitle("residual [#sigma]")
    residHist.SetMarkerStyle(8)
    residHist.SetMarkerSize(0.7)
    wfm_hist.SetAxisRange(fit_min-1, fit_max+1)

    # calculate residual for each bin
    for i_bin in xrange(residHist.GetNbinsX()):
        binCenter = residHist.GetBinCenter(i_bin)

        # only set non-zero entries for the fit region
        if binCenter < fit_min or binCenter > fit_max: 
            residHist.SetBinContent(i_bin,0)
            residHist.SetBinError(i_bin, 0)
            continue
        val = (wfm_hist.GetBinContent(i_bin) - test.Eval(binCenter)) / wfm_hist.GetBinError(i_bin)
        residHist.SetBinContent(i_bin, val)
        residHist.SetBinError(i_bin, 1) # 1 sigma
    pad2 = canvas.cd(2)
    residHist.Draw("hist p")

    canvas.Update()

    print "-----------------------------------------------------"
    return (status, chi2/ndf)




def process_file(file_name):

    canvas = TCanvas("canvas","", 600, 1400)
    canvas.Divide(1,2)

    pad1 = canvas.cd(1)
    pad1.SetGrid(1,1)
    pad2 = canvas.cd(2)
    pad2.SetGrid(1,1)

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz

    canvas.Print("output.pdf(")

    tfile = TFile(file_name)
    tree = tfile.Get("tree")
    for i_entry in xrange(tree.GetEntries()):

        
        # debugging; skip entries I'm not interested in
        if i_entry < 42: continue # debugging; skip entries i've seen before...
        if i_entry < 84: continue # signal with induction
        #if i_entry < 91: continue # pure induction signal

        tree.GetEntry(i_entry)
        #if struck_analysis_parameters.charge_channels_to_use[tree.channel]:
        #    print channel
        calibration = struck_analysis_parameters.calibration_values[tree.channel[3]]
        calibration/=2.5 # correction for ADC input range
        #print calibration

        # only ch 3 for now:
        wfm = tree.wfm3
        energy = (tree.wfm_max[3] - wfm[0])*calibration
        print "entry %i | energy: %.2f" % (i_entry, energy)
        if energy < 100: continue
        pad1 = canvas.cd(1)

        # convert wfm to EXODoubleWaveform
        waveform_length = len(wfm)
        exo_wfm = EXODoubleWaveform(array('d',wfm), waveform_length)
        exo_wfm*=calibration # convert wfm from ADC units to keV
        exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
    
        # remove the baseline
        baseline_remover = EXOBaselineRemover()
        baseline_remover.SetBaselineSamples(125)
        baseline_remover.Transform(exo_wfm)
        rms = baseline_remover.GetBaselineRMS()

        output = do_fit(exo_wfm=exo_wfm, canvas=canvas, i_entry=i_entry, rms=rms, doTwoPCDs=False)
        status = output[0]
        chi2_per_ndf = output[1]
        canvas.Print("output.pdf")

        val = raw_input("enter to continue ")
        if val == 'q':
            # this should probably be handled better...
            canvas.Print("output.pdf)")
            sys.exit()

        #if chi2_per_ndf > 2.0:
        if status != 0 or chi2_per_ndf > 2.0:
            print "===> repeating fit... "
            (status, chi2_per_ndf) = do_fit(exo_wfm=exo_wfm, canvas=canvas, i_entry=i_entry, rms=rms, doTwoPCDs=True)
            canvas.Print("output.pdf")

            val = raw_input("enter to continue ")
            if val == 'q':
                # this should probably be handled better...
                canvas.Print("output.pdf)")
                sys.exit()


        canvas.Print("output.pdf)")

if __name__ == "__main__":

    # one test:

    # at SLAC:
    file_name = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier2/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root"
    # alexis' virtual ubuntu:
    file_name = "/home/alexis/myBucket/testStand/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root"

    process_file(file_name)


