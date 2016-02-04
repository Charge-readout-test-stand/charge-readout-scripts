"""
to do:
    * process all channels, not just Y23

29 Jan 2016 -- changed drift velocity from 17.2 to 17.1 mm / microsecond

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
import numpy as np

from ROOT import gROOT
gROOT.SetBatch(True) #comment out to run interactively
from ROOT import TH1D
from ROOT import TFile
from ROOT import TTree
from ROOT import TGraph
from ROOT import TF1
from ROOT import TCanvas
from ROOT import TColor
from ROOT import gStyle
from ROOT import gSystem
from ROOT import TLine
from ROOT import TPaveText
from ROOT import TRandom3

import wfmProcessing


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

# be sure to use the "+" -- it made fitting about 30x faster!
gROOT.ProcessLine('.L ralphWF.C+')
from ROOT import OnePCD
from ROOT import TwoPCDsOneZ
from ROOT import OneStripWithIonAndCathode

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


def get_drift_stop_time_from_z(z):
    # options
    trigger_time = 8.0 # microseconds
    drift_velocity = struck_analysis_parameters.drift_velocity
    t = trigger_time + z/drift_velocity
    return t



def do_fit(exo_wfm, canvas, i_entry, rms, channel, doTwoPCDs=False, isMC=False, MCz = None):

    print "-----------------------------------------------------"
    print "starting fit"
    print "-----------------------------------------------------"

    #-------------------------------------------------------------------------------
    # options:
    #-------------------------------------------------------------------------------

    # fit range:
    fit_min = 7.5
    fit_max = 22

    #-------------------------------------------------------------------------------

    print "rms: %.2f" %  rms
    if isMC:
        channel_name = struck_analysis_parameters.mc_channel_map[channel]
    else:
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
        energy_estimate += exo_wfm.At(waveform_length-i-1)
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
    colors = struck_analysis_parameters.get_colors()
    color = colors[channel % len(colors)]
    color = 2
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
    fit_start = time.clock() # keep track of fit start time
    while status > 0:
        print "FIT ATTEMPT", n_tries
        wfm_hist.SetTitle("%s, attempt %i" % (title, n_tries))
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
        drift_stop = get_drift_stop_time_from_z(test.GetParameter(2))
        print "drift_stop [microseconds]: %.2f" % drift_stop
        line = TLine(drift_stop, wfm_hist.GetMinimum(), drift_stop, wfm_hist.GetMaximum())
        line.SetLineStyle(2)
        line.SetLineWidth(2)
        line.SetLineColor(TColor.kBlue)
        line.Draw()

        # draw z from MC
        if isMC:
            MCt = get_drift_stop_time_from_z(MCz)
            print "MC z=%.1f, t=%.1f" % (MCz, MCt)
            line2 = TLine(MCt, wfm_hist.GetMinimum(), MCt, wfm_hist.GetMaximum())
            #line2.SetLineStyle(2)
            #line2.SetLineWidth(2)
            line2.SetLineColor(TColor.kGreen+2)
            line2.Draw()


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
    return (status, chi2/ndf, ndf, test.GetParameter(2), fit_duration)


def process_file(file_name):

    # options:
    drift_length = struck_analysis_parameters.drift_length

    print "---> processing", file_name
    canvas = TCanvas("canvas","", 800, 1100)
    canvas.Divide(1,2)

    pad1 = canvas.cd(1)
    pad1.SetGrid(1,1)
    pad2 = canvas.cd(2)
    pad2.SetGrid(1,1)

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz

    tfile = TFile(file_name)

    # figure out if this is MC
    isMC = False
    try:
        tree = tfile.Get("tree")
        n_entries = tree.GetEntries()
        pmt_channel = struck_analysis_parameters.pmt_channel
        n_channels = struck_analysis_parameters.n_channels
        charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    except AttributeError:
        tree = tfile.Get("evtTree")
        n_entries = tree.GetEntries()
        print "--> this file is MC"
        isMC = True
        pmt_channel = None #No PMT in MC
        n_channels = struck_analysis_parameters.MCn_channels
        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    except:
        print "==> Problem with file."
        sys.exit(1)
    print "%i entries in tree" % n_entries

    # open output file and tree
    out_filename = "fits_" + wfmProcessing.create_outfile_name(file_name)
    out_file = TFile(out_filename, "recreate")
    out_tree = TTree("tree", "fits to wfms")

    ichannel = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('channel', ichannel, 'channel[%i]/i' % n_channels)

    # fitter status (if bad, != 0)
    fit_status = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('fit_status', fit_status, 'fit_status[%i]/i' % n_channels)

    # fit chi^2
    chi2 = array('d', [0.0]*n_channels) # double
    out_tree.Branch('chi2', chi2, 'chi2[%i]/D' % n_channels)

    # fit duration
    fit_duration = array('d', [0.0]*n_channels) # double
    out_tree.Branch('fit_duration', fit_duration, 'fit_duration[%i]/D' % n_channels)

    # fitter number of degrees of freedom
    dof = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('dof', dof, 'dof[%i]/i' % n_channels)

    # drift time, from fit result
    fit_drift_time = array('d', [0.0]*n_channels) # double
    out_tree.Branch('fit_drift_time', fit_drift_time, 'fit_drift_time[%i]/D' % n_channels)

    # rise_time95
    rise_time95 = array('d', [0.0]*n_channels) # double
    out_tree.Branch('rise_time95', rise_time95, 'rise_time95[%i]/D' % n_channels)

    if isMC:
        # drift time, from MC
        drift_time_MC = array('d', [0.0]*n_channels) # double
        out_tree.Branch('drift_time_MC', drift_time_MC, 'drift_time_MC[%i]/D' % n_channels)

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
        
        if isMC:
            calibration = struck_analysis_parameters.Wvalue*1e-3
        else:
            calibration = struck_analysis_parameters.calibration_values[tree.channel[3]]

        calibration/=2.5 # correction for ADC input range FIXME for different files...
        #print calibration

        # only ch Y23 for now -- FIXME
        
        if isMC:
            channel = 52
            wfm = [wfmp for wfmp in tree.ChannelWaveform[channel]]
            wfm_max = np.amax(wfm)

        else:
            channel = 3
            wfm = tree.wfm3
            wfm_max = tree.wfm_max[channel]

        energy = (wfm_max - wfm[0])*calibration
        print "entry %i | energy: %.2f" % (i_entry, energy)
        if energy < 100: continue

        print "--> %i fits so far..." % n_fits

        n_fits += 1

        # convert wfm to EXODoubleWaveform
        waveform_length = len(wfm)

        # add noise to MC
        if isMC:
            sigma = 18.0/calibration
            print "adding %.1f ADC units ( %.1f keV) noise to MC" % (
                sigma,
                sigma*calibration,
            )
            generator = TRandom3(0)
            for i_point in xrange(len(wfm)):
                noise = generator.Gaus()*sigma
                wfm[i_point]+=noise

        # print some info about PCDs
        MCz = None
        if isMC:
            nPCDs = tree.NumPCDs
            print "energy", tree.Energy
            print tree.NumPCDs

            # form an energy-weighted z-coord for PCDs that hit this channel
            z_sum = 0.0
            e_sum = 0.0
            for iPCD in xrange(nPCDs):
                x = tree.PCDx[iPCD]
                y = tree.PCDy[iPCD]
                z = tree.PCDz[iPCD]
                e = tree.PCDq[iPCD]*calibration

                # translate MC coords to frame of ralphWF.C
                if channel >= 30: # this is a y channel
                    x_ch = -1.5
                    y_ch = (channel - 30)*3.0 - 43.5
                    print "y_ch", y_ch
                    x = x - x_ch
                    y = y - y_ch
                    print "new y", y
                    z = drift_length-z
                hit_e =  OneStripWithIonAndCathode(x, y, 0, z)*e
                print "energy hitting this channel: %.1f" % hit_e
                e_sum += hit_e
                z_sum += hit_e*z
                print "PCD %i: E=%.1f, x=%.2f, y=%.2f, z=%.2f" % (
                    iPCD, 
                    e, 
                    x,
                    y, 
                    z,
                )
                # end loop over PCDs

            # calculate drift stop time from MC:
            MCz = z_sum/e_sum
        print "energy-weighted z: %.2f" % z

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
        if isMC: 
            if rms == 0: 
                print "setting MC RMS to 1.0"
                rms = 1.0

        output = do_fit(exo_wfm=exo_wfm, canvas=canvas, i_entry=i_entry, rms=rms, channel=channel, doTwoPCDs=False, isMC=isMC, MCz=MCz)
        chi2_per_ndf = output[1]

        #if chi2_per_ndf > 2.0:
        if chi2_per_ndf > 2.0:
            print "===> repeating fit with 2 PCDs... "
            output = do_fit(exo_wfm=exo_wfm, canvas=canvas,
            i_entry=i_entry, rms=rms, channel=channel, doTwoPCDs=True,
            isMC=isMC, MCz = MCz)

            chi2_per_ndf = output[1]

        risetimes = wfmProcessing.get_risetimes(exo_wfm, waveform_length, sampling_freq_Hz)
        rise_time95[0] = risetimes[10]

        # fill tree entries
        fit_status[0] = output[0]
        chi2[0] = output[1]*output[2]
        dof[0] = output[2]
        fit_drift_time[0] = get_drift_stop_time_from_z(output[3])
        drift_time_MC[0] = get_drift_stop_time_from_z(MCz)
        fit_duration[0] = output[4]
        ichannel[0] = channel
        out_tree.Fill()

        # end loop over tree entries
        if out_tree.GetEntries() >= 300: 
            print "-------------------> debugging!!"
            break # debugging

    # finish multi-page pdf
    canvas.Print("output.pdf]")
    out_tree.Write()


if __name__ == "__main__":

    # one test:

    # at SLAC:
    file_name = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier2/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root"
    # alexis' virtual ubuntu:
    file_name = "/home/alexis/myBucket/testStand/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root"

    # MJJ MC file, 207-Bi:
    file_name = "~/testStandMC/digitization/Bi207_Full_Ralph/Digi/digi1_Bi207_Full_Ralph_dcoef0.root"

    # MC file, 1-MeV electron:
    file_name = "/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/electron_1MeV_Ralph/Digi/digi1_electron_1MeV_Ralph_dcoef0.root"

    process_file(file_name)


