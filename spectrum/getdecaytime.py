#!/usr/bin/env python

"""
This script does a fit on the waveform to determine the decay time

Takes 43 minutes for this run:
tier1_overnight_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03-08_08-14-17.root

Takes 6 hours, 9 minutes:
2016_03_07_7thLXe/tier1/tier1_overnight_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03-08_08*.root

See the script for settings of flat time and gap time (for maw)

The script will ask for a channel number and a threshold,
only waveforms in the specified channel and whose maw max is > threshold are included

For qualified waveforms, the script does a fit starting from 100 clockticks after
the maw max and uses exponential decay function:
    def expdecay(x, a, b):
        return a * np.exp(-x / b) + baseline
(the number of baseline samples is set in the script!)

The output of this script is a histogram of the fit parameter b (i.e. the decay time)
"""

import os
import sys
import math

import numpy as np
from array import array
from scipy.optimize import curve_fit

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TF1
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TLine
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TGraph
from ROOT import TTree
from ROOT import TChain
from struck import struck_analysis_parameters


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)

gSystem.Load("$EXOLIB/lib/libEXOUtilities")
from ROOT import EXOTrapezoidalFilter
from ROOT import CLHEP


def diff(value, fit, rms):
    diff = (value-fit)/rms # approx RMS noise
    return diff

def process_files(filenames):
    sampling_period = 40 * CLHEP.nanosecond


    # options:
    fitstart = int(19.0/(sampling_period/CLHEP.microsecond))
    fitstop = int(32.0/(sampling_period/CLHEP.microsecond))
    do_draw = 1 # draw each wfm fit

    reporting_period = 1000

    drift_length = struck_analysis_parameters.drift_length

    basename = os.path.commonprefix(filenames)
    basename = os.path.basename(basename)
    basename = os.path.splitext(basename)[0]


    # longer fits for noise runs
    if basename == "tier1_noise_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03-08_10-23-20":
        fitstart = int(1500.0/(sampling_period/CLHEP.microsecond))
        fitstop = int(2600.0/(sampling_period/CLHEP.microsecond))

    # set up a canvas
    canvas = TCanvas("canvas","",900,700)
    canvas.SetGrid(1,1)

    peaking_time = 50
    gap_time = 250
    trapFilter = EXOTrapezoidalFilter()
    trapFilter.SetRampTime(peaking_time * sampling_period)
    trapFilter.SetFlatTime(gap_time * sampling_period)
    trapFilter.SetDoNormalize()

    # open output file and tree
    out_filename = "fit_%s.root" % (basename)
    print out_filename
    out_file = TFile(out_filename, "recreate")

    results_file = file("results_%s.txt" % basename,"w")

    for channel in xrange(8):
        tree_name = "tree%i" % channel
        print "----> processing", tree_name

        tree = TChain(tree_name)
        for filename in filenames:
            print "---> processing", os.path.basename(filename)
            tree.Add(filename)

        canvas.Divide(2,1)
        try:
            n_entries = tree.GetEntries()
        except:
            print "\t couldn't open tree"
            sys.exit(1)
        print "%i entries" % n_entries
        if n_entries == 0: 
            continue
        tree.SetLineWidth(2)
        print "%i entries in tree%i" % (n_entries, channel)
        if n_entries == 0:
            print "zero entries in tree"

        out_tree = TTree("tree%i" % channel, "decay time fits")
        out_tree.SetLineColor(TColor.kBlue)
        out_tree.SetLineWidth(2)
        out_tree.SetMarkerColor(TColor.kRed)
        out_tree.SetMarkerStyle(8)
        out_tree.SetMarkerSize(0.5)


        tau = array('d', [0]) # double
        out_tree.Branch('tau', tau, 'tau/D')

        ndf = array('d', [fitstop-fitstart+1-2]) # double
        out_tree.Branch('ndf', ndf, 'ndf/D')

        chi2_saved = array('d', [0]) # double
        out_tree.Branch('chi2', chi2_saved, 'chi2/D')

        height = array('d', [0]) # double
        out_tree.Branch('height', height, 'height/D')

        #threshold = input("Enter threshold: ")
        threshold = 150
    
        fithist = TH1D("tau%i" % channel, "Ch %i Decay Time" % channel, 100, 0.0, 2000.0)
        fithist.SetLineColor(TColor.kBlue)
        fithist.SetLineWidth(2)
        fithist.SetXTitle("#tau [#mus]")
        fithist.SetYTitle("Counts / %.1f #mus" % fithist.GetBinWidth(1))

        for i_entry in xrange(tree.GetEntries()):
            tree.GetEntry(i_entry)
            if ord(tree.channel) != channel:
                print "channel doesn't match!"
                print "tree.channel:", ord(tree.channel)
                print "channel", channel
                sys.exit()

            if i_entry % reporting_period == 0:
                print "entry", i_entry

            #if i_entry > 200: break # debugging
            #if fithist.GetEntries() >= 50: break # debugging

            wfm = np.array(tree.wfm)

            sp = 10   # the step used when calculating the maw
            mawlen = (len(wfm) - 2*peaking_time - gap_time + 1) // sp  # length of the maw
            maw = np.zeros(mawlen)
            # mawplot = TGraph(mawlen)

            for j in xrange(mawlen):
                i = j * sp
                maw[j] = - np.mean(wfm[i:i+peaking_time]) + np.mean(wfm[i+peaking_time+gap_time:i+2*peaking_time+gap_time])
                # mawplot.SetPoint(j, j, maw[j])

            # average over first 100 baseline samples
            
            baseline = np.mean(wfm[:100])  # assuming that the wfm will eventually decay onto the baseline
            
            #print baseline, tree.wfm_max - baseline, threshold

            # subtract off the baseline:
            wfm[:] = [x - baseline for x in wfm]
            if np.amax(wfm)  < threshold:
                continue

            rms = [x**2 for x in wfm[:100]]
            rms = math.sqrt(sum(rms)/100.0)

            # print "maw_max = %d" % np.amax(maw)

            # canvas.Clear()
            # canvas.Divide(2,2)

            # pad = canvas.cd(1)
            # pad.SetGrid(1,1)

            # legend = TLegend(0.7, 0.92, 0.9, 0.99)
            # legend.AddEntry(tree, "channel %i" % tree.channel, "pl")
            # tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry, "l")
            # legend.Draw()

            # pad = canvas.cd(2)
            # pad.SetGrid(1,1)
            # mawplot.Draw("AL")


            def expdecay(x, a, b):
                return a * np.exp(-x / b) 

            ## start fit at 100 points after the maw max
            #fitstart = int(np.argmax(maw) * sp + peaking_time + gap_time + 100)
            
            fitlen = len(wfm[fitstart:fitstop])
            if fitlen < 10:  ## if remaining length is < 10 then print out warning message and skip
                print "fitting length < 10!"
                continue

            # wfm = 0.5 * np.exp(-np.arange(len(wfm)) / 1000.) + 1 + np.random.normal(0., 0.05, len(wfm)) # test waveform

            tdata = np.arange(fitlen)

            a_guess = wfm[fitstart]  # making guesses for the fit
            b_guess = 200 /(sampling_period/CLHEP.microsecond) # guess for decay time = 200 us
            try:
                popt, pcov = curve_fit(expdecay, tdata, wfm[fitstart:fitstop], p0 = [a_guess, b_guess])
            except RuntimeError:
                print "RuntimeError from fitter; skipping this event"
                continue
            chi2 = 0.0
            resid_graph = TGraph()
            resid_graph.SetMarkerStyle(8)
            resid_graph.SetMarkerSize(0.5)
            calibration = struck_analysis_parameters.calibration_values[channel]/2.5 
            try:
                dataset_RMS = struck_analysis_parameters.rms_keV[channel]
            except KeyError:
                dataset_RMS = 0.5 # digitization error
            for i in range(fitstart, fitstop):
                difference = diff(wfm[i], expdecay(i-fitstart, popt[0], popt[1]), dataset_RMS/calibration)
                chi2 += pow(difference, 2.0)
                resid_graph.SetPoint(resid_graph.GetN(),i*sampling_period/CLHEP.microsecond,difference)
            #print "decay time [microsecond]:", popt[1]*sampling_period/CLHEP.microsecond
            #print np.sqrt(np.diag(pcov))

            ## Show data with fit
            if do_draw and not gROOT.IsBatch():
                print "\t calibration", calibration
                print "\t dataset RMS [keV]", dataset_RMS 
                print "\t dataset RMS", dataset_RMS/calibration
                print "\t wfm RMS", rms
                print "\t fitstart", fitstart
                print "\t fitstop", fitstop
                print "\t entry", i_entry
                print "\t chi2", chi2
                print "\t height", popt[0]
                pad = canvas.cd(1)
                pad.SetGrid(1,1)
                fitplot = TGraph()
                fitplot.SetLineWidth(2)
                wfmplot = TGraph()
                for i in xrange(len(wfm)):
                    wfmplot.SetPoint(i, i*(sampling_period/CLHEP.microsecond), wfm[i])
                    if i >= fitstart and i <= fitstop:
                        i_point = fitplot.GetN()
                        val = expdecay(i_point, popt[0], popt[1])
                        #print i_point, i, val
                        fitplot.SetPoint(i_point, i*(sampling_period/CLHEP.microsecond), val)
                wfmplot.SetLineColor(1)
                wfmplot.Draw("al")
                hist = wfmplot.GetHistogram()
                hist.SetTitle("ch %i entry %i | #tau: %.1f  #mus| chi^{2}/ndf: %.1f/%i=%.1f" % (
                    channel,
                    i_entry, 
                    popt[1]*sampling_period/CLHEP.microsecond,
                    chi2,
                    ndf[0],
                    chi2/ndf[0],
                ))
                hist_max = hist.GetMaximum()
                hist_min = hist.GetMinimum()
                line = TLine(drift_length, hist_min, drift_length, hist_max)
                line.SetLineStyle(2)
                wfmplot.Draw("al")
                line.Draw()
                fitplot.SetLineColor(2)
                fitplot.Draw("L")

                pad = canvas.cd(2)
                pad.SetGrid(1,1)
                resid_graph.Draw("ap")

                canvas.Update()
                val = raw_input("q=quit | n=next channel | b=batch: ")
                if val == 'q':
                    sys.exit()
                if val == 'b':
                    gROOT.SetBatch(True)
                if val == 'n':
                    break

            
            tau[0] = popt[1]*sampling_period/CLHEP.microsecond
            height[0] = popt[0]
            chi2_saved[0] = chi2
            out_tree.Fill()

            if chi2/ndf[0] < 2.0:
                fithist.Fill(tau[0]) # fill the histogram

        fit_fcn = TF1("fcn","[2]*TMath::Landau(x,[0],[1],0)",0,5000)
        fit_fcn.SetParameter(0,fithist.GetBinCenter(fithist.GetMaximumBin())) # peak center
        fit_fcn.SetParameter(1,100) # width
        #fit_fcn.SetParameter(2, fithist.GetMaximum()*fithist.GetBinWidth(1))
        fit_fcn.SetParameter(2, fithist.GetMaximum())

        # draw before fit
        fithist.Draw()
        fit_fcn.Draw("same")
        canvas.Update()
        if not gROOT.IsBatch():
            print "%i entries in hist" % fithist.GetEntries()
            raw_input("Press Enter to continue...")

        print "performing fit..."
        result = fithist.Fit(fit_fcn,"IS")
        print "chi2:", result.Chi2()
        print "ndf:", result.Ndf()
        print "chi2/ndf:", result.Chi2()/result.Ndf()
        print "p-value:", result.Prob()

        canvas.Clear()
        fithist.SetTitle("ch %i #tau: %.1f #pm %.1f #mus, #chi^{2}/NDF: %.1f/%i = %.1f, P=%.1E, %.1E cts" % (
            channel,
            fit_fcn.GetParameter(0),
            fit_fcn.GetParError(0),
            result.Chi2(),
            result.Ndf(),
            result.Chi2()/result.Ndf(),
            result.Prob(),
            fithist.GetEntries(),
        ))
        fithist.Draw()
        canvas.Update()
        #canvas.Print("%s_fit_maw_p%i_g%i_channel%i.png" % (basename, peaking_time, gap_time, channel))
        canvas.Print("%s_fit_channel%i.pdf" % (basename, channel))

        fithist.Write()
        out_tree.Write()
        
        if not gROOT.IsBatch():
            raw_input("Press Enter to continue...")

        info = "decay_time_values[%i] = %.2f*microsecond # +/- %.2f" % (
            channel,
            fit_fcn.GetParameter(0),
            fit_fcn.GetParError(0),
        )
        print info
        results_file.write("%s \n" % info)

    results_file.close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    filenames = sys.argv[1:]
    process_files(filenames)



