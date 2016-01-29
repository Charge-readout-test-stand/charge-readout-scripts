"""
Fit one charge signal wfm with Ralph's analytical function. 

The fit function is tricky... when the charge drifts to the anode, the function
changes discontinuously to 0 or 1. 

As x and y change to move the charge onto or off of a pad, the function also
changes to 0 or 1 at late times. 

The fit is sensitive to initial conditions. The collected charge and wfm max are
used to decide whether to fit with a collection signal or induction signal. 

The dashed vertical line shows the signal stop time. 

"""

import os
import sys
import math
import time
from array import array

from ROOT import gROOT
gROOT.SetBatch(True) #comment out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TGraph
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TColor
from ROOT import gStyle
from ROOT import gSystem
from ROOT import TLine
from ROOT import TPaveText


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

# be sure to use the "+" -- it made fitting about 30x faster!
gROOT.ProcessLine('.L ralphWF.C+')
from ROOT import OnePCD
from ROOT import TwoPCDsOneZ

gSystem.Load("$EXOLIB/lib/libEXOROOT")
from ROOT import CLHEP
from ROOT import EXODoubleWaveform
from ROOT import EXOBaselineRemover

# definition of calibration constants, decay times, channels
import struck_analysis_parameters

def print_fit_info(fit_result, fit_duration):

    chi2 = fit_result.Chi2()
    prob = fit_result.Prob()
    ndf = fit_result.Ndf()
    status = fit_result.Status()
    print "fit results:"
    print "\tchi2: %.2f" % chi2
    print "\tn dof", ndf
    print "\tchi2 / dof: %.2f" % (chi2/ndf) 
    print "\tprob", prob
    print "\tstatus", status
    print "\t%.1f seconds" % fit_duration




def do_fit(exo_wfm, canvas, i_entry, rms, channel, doTwoPCDs=False):

    print "-----------------------------------------------------"
    print "starting fit"
    print "-----------------------------------------------------"

    #-------------------------------------------------------------------------------
    # options:
    #-------------------------------------------------------------------------------

    # fit range:
    fit_min = 7.5
    fit_max = 22
    drift_velocity = 1.7

    #-------------------------------------------------------------------------------

    print "rms: %.2f" %  rms
    channel_name = struck_analysis_parameters.channel_map[channel]

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
    test.SetParError(0, 0.2) 
    # Y ERROR AFFECTS FIT RESULT!
    #test.SetParError(1, 1.5) # too big

    test.SetParError(1, 0.2) # too small
    test.SetParError(1, 0.5) # too small?
    test.SetParError(1, 0.75) # too small?
    test.SetParError(1, 1.0) # too small?
    test.SetParError(1, 1.2) # too small?
    print "y error:", test.GetParError(1)

    test.SetParameter(2, 18.5) # z0
    test.SetParError(2, 1.0) # too small
    test.SetParError(3, rms) # too small


    # this works best for pure induction signals...
    wfm_max = exo_wfm.GetMaxValue()
    print "wfm max: %.1f (%.1f sigma)" % (wfm_max, wfm_max/rms)

    # estimate the collected energy; this works best for collection or collection + induction
    nSamples = 100
    waveform_length = exo_wfm.size()
    energy_estimate = 0.0
    for i in xrange(nSamples):  
        energy_estimate += exo_wfm[waveform_length-i]
    energy_estimate /= nSamples
    print "energy_estimate: %.1f (%.1f sigma)" % (energy_estimate, energy_estimate/rms)
    amplitude_estimate = energy_estimate


    x_estimate = 1.5
    y_estimate = 0.0
    if not doTwoPCDs:
        if energy_estimate/rms < 3.0:
            if wfm_max/rms > 3.0:
                print "--> we are using one PCD and this looks like a pure induction signal"
                x_estimate = 0.0
                y_estimate = 0.1
                amplitude_estimate = wfm_max*2.5
        
    print "x_estimate:", x_estimate
    test.SetParameter(0, x_estimate) # x (x=1.5 is center of one pad); THIS AFFECTS FIT RESULT!
    print "y_estimate:", y_estimate
    test.SetParameter(1, y_estimate) # y
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
    for i_bin in xrange(wfm_hist.GetNbinsX()+1):
        wfm_hist.SetBinError(i_bin, rms) # approx. rms
    color = struck_analysis_parameters.get_colors()[channel]
    wfm_hist.SetLineColor(color)
    wfm_hist.SetLineWidth(2)
    title = "Entry %i %s before fit with %i PCDs" % (i_entry, channel_name, 1+doTwoPCDs)
    wfm_hist.SetAxisRange(fit_min-1, fit_max+1)
    wfm_hist.SetTitle(title)
    wfm_hist.SetYTitle("Energy [keV]")

    # draw before fit
    if True:
        print "--> before fit"
        wfm_hist.Draw("hist")
        test.Draw("same")

        canvas.Update()
        if not gROOT.IsBatch(): 
            val = raw_input("enter to continue (q to quit) ")
            if val == 'q': sys.exit()

    # set things up for drawing
    title = "Entry %i %s after fit with %i PCD(s)" % (i_entry, channel_name, 1 + doTwoPCDs)
    wfm_hist.SetAxisRange(fit_min-1, fit_max+1)

    # if status is bad, repeat the fit:
    n_tries = 0
    status = 1
    print "doing fit..."
    fit_options = "SNR"
    while status > 0:
        print "FIT ATTEMPT", n_tries
        wfm_hist.SetTitle("%s, attempt %i" % (title, n_tries))
        fit_start = time.clock() # keep track of fit start
        # fit options:
        # S -- save output to fit_result
        # N -- don't store the fit function graphics with the histogram
        # R -- use fit fcn's range
        # M -- more; look for new minimum 
        print "fit_options:", fit_options
        fit_result = wfm_hist.Fit(test, fit_options)
            
        n_tries += 1
        fit_stop = time.clock() # keep track of fit stop
        fit_duration = fit_stop - fit_start
        print_fit_info(fit_result, fit_duration)
        pad1 = canvas.cd(1)
        wfm_hist.Draw("hist")
        test.Draw("same")

        # calculate drift stop time and draw a line to represent
        drift_stop = 8.0 + test.GetParameter(2)/drift_velocity
        print "drift_stop [microseconds]: %.2f" % drift_stop
        line = TLine(drift_stop, wfm_hist.GetMinimum(), drift_stop, wfm_hist.GetMaximum())
        line.SetLineStyle(2)
        line.SetLineWidth(2)
        line.SetLineColor(TColor.kBlue)
        line.Draw()

        # fit results
        chi2 = fit_result.Chi2()
        prob = fit_result.Prob()
        ndf = fit_result.Ndf()
        status = fit_result.Status()

        # text block to draw results
        pave_text = TPaveText(0.12, 0.6, 0.5, 0.88, "NDC")
        pave_text.SetTextAlign(12) # left horizontal, vertical center
        pave_text.GetTextFont()
        pave_text.SetTextFont(42)
        pave_text.SetFillColor(10)
        #pave_text.SetFillStyle(0)
        pave_text.SetBorderSize(1)
        pave_text.AddText("#chi^{2}/DOF = %.1f/%i = %.2f" % (chi2, ndf, chi2/ndf))
        pave_text.AddText("P-val: %.2e | wfm RMS [keV]: %.2f" % (prob, rms))
        pave_text.AddText("Fit status: %i | elapsed fit time [s]: %.1f" % (status, fit_stop - fit_start))
        pave_text.AddText("PCD 0: q=%i, (%.1f #pm %.1f, %.1f #pm %.1f, %.1f #pm %.1f) mm" % (
            test.GetParameter(3),
            test.GetParameter(0),
            test.GetParError(0),
            test.GetParameter(1),
            test.GetParError(1),
            test.GetParameter(2),
            test.GetParError(2),
        ))

        if doTwoPCDs:
            pave_text.AddText("PCD 1: q=%i, (%.1f #pm %.1f, %.1f #pm %.1f, %.1f #pm %.1f) mm" % (
                test.GetParameter(6),
                test.GetParameter(4),
                test.GetParError(4),
                test.GetParameter(5),
                test.GetParError(5),
                test.GetParameter(2),
                test.GetParError(2),
            ))
        pave_text.Draw()


        # setup residuals hist
        residHist = wfm_hist.Clone("residHist")
        residHist.SetTitle("Entry %i" % i_entry)
        residHist.SetYTitle("residual[#sigma] = (wfm - fit) / %.2f" % rms)
        residHist.SetMarkerStyle(8)
        residHist.SetMarkerSize(0.7)
        wfm_hist.SetAxisRange(fit_min-1, fit_max+1)

        # calculate residual for each bin
        for i_bin in xrange(residHist.GetNbinsX()+1):
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

        if False:
            # repeat with M option
            if status == 0 and chi2/ndf > 2:
                print "trying again with M option"
                fit_options = "SNRM"
                status=1

        if n_tries > 20: break # limit number of attempts

        if status > 0:
            print "BAD FIT, repeating..."
        # end loop over fitting

    canvas.Update()
    canvas.Print("output.pdf")


    # wait for user input after drawing. don't do this in batch mode
    if not gROOT.IsBatch():

        val = raw_input("enter to continue (q to quit) ")
        if val == 'q':

            # this should probably be handled better...
            # finish the multi-page PDF
            canvas.Print("output.pdf]")
            sys.exit()

    print "-----------------------------------------------------"
    return (status, chi2/ndf)


def process_file(file_name):

    print "processing", file_name
    canvas = TCanvas("canvas","", 800, 1100)
    canvas.Divide(1,2)

    pad1 = canvas.cd(1)
    pad1.SetGrid(1,1)
    pad2 = canvas.cd(2)
    pad2.SetGrid(1,1)

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz

    tfile = TFile(file_name)
    tree = tfile.Get("tree")
    n_fits = 0

    canvas.Print("output.pdf[")

    for i_entry in xrange(tree.GetEntries()):

        
        # debugging; skip entries I'm not interested in or start from
        # interesting events
        #if i_entry < 42: continue # debugging; skip entries i've seen before...
        #if i_entry < 84: continue # signal with induction
        #if i_entry < 91: continue # pure induction signal
        #if i_entry < 144: continue # pure induction signal
        #if i_entry < 194: continue # pure induction signal

        tree.GetEntry(i_entry)
        #if struck_analysis_parameters.charge_channels_to_use[tree.channel]:
        #    print channel
        calibration = struck_analysis_parameters.calibration_values[tree.channel[3]]
        calibration/=2.5 # correction for ADC input range
        #print calibration

        # only ch 3 for now:
        channel = 3
        wfm = tree.wfm3
        energy = (tree.wfm_max[channel] - wfm[0])*calibration
        print "entry %i | energy: %.2f" % (i_entry, energy)
        if energy < 100: continue

        print "--> %i fits so far..." % n_fits

        # debugging... limit n_fits
        if n_fits >= 300:
            canvas.Print("output.pdf]")
            sys.exit()

        n_fits += 1

        # convert wfm to EXODoubleWaveform
        waveform_length = len(wfm)
        exo_wfm = EXODoubleWaveform(array('d',wfm), waveform_length)
        exo_wfm*=calibration # convert wfm from ADC units to keV
        exo_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
    
        # remove the baseline
        baseline_remover = EXOBaselineRemover()
        # Use many samples so we can get a good estimate of RMS. When doing real
        # processing, this estimate could come from all wfms in the file from
        # this channel. 
        baseline_remover.SetBaselineSamples(125)
        baseline_remover.Transform(exo_wfm)
        rms = baseline_remover.GetBaselineRMS()

        output = do_fit(exo_wfm=exo_wfm, canvas=canvas, i_entry=i_entry, rms=rms, channel=channel, doTwoPCDs=False)
        status = output[0]
        chi2_per_ndf = output[1]



        #if status != 0 or chi2_per_ndf > 2.0:
        if chi2_per_ndf > 2.0:
            print "===> repeating fit with 2 PCDs... "
            (status, chi2_per_ndf) = do_fit(exo_wfm=exo_wfm, canvas=canvas,
            i_entry=i_entry, rms=rms, channel=channel, doTwoPCDs=True)

        # end loop over tree entries

    # finish multi-page pdf
    canvas.Print("output.pdf]")


if __name__ == "__main__":

    # one test:

    # at SLAC:
    file_name = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier2/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root"
    # alexis' virtual ubuntu:
    file_name = "/home/alexis/myBucket/testStand/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root"

    process_file(file_name)


