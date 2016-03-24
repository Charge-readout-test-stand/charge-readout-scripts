#!/bin/env python

"""
Script to calibrate energies based on location of 570-keV peak. 
Currently doing binned fit, using exponential background model

This script was adapted from mca/fit_to_resolution.py 

to do:
* draw residuals
* goodness of fit
* try different background models
* unbinned fit / test different binning
"""


import os
import sys
import json
import math
import datetime


from ROOT import gROOT
# run in batch mode:
gROOT.SetBatch(True)
from ROOT import TFile
from ROOT import TTree
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import TH1D
from ROOT import TF1
from ROOT import TGraph
from ROOT import gSystem

import struck_analysis_parameters


def fit_channel(tree, channel, basename, do_1064_fit=False):

    #-------------------------------------------------------------------------------
    # options
    #-------------------------------------------------------------------------------

    energy_var = "energy1_pz"

    do_debug = False
    do_use_step = False
    do_individual_channels = False

    # defaults for 570-keV
    min_bin = 200
    max_bin = 1000
    bin_width = 5
    line_energy = 570
    sigma_guess = 40
    fit_half_width = 170
    #fit_half_width = 250

    # gaus + exponential
    fit_formula = "gausn(0) + [3]*TMath::Exp(-[4]*x) + [5]"

    if do_1064_fit: # 1064-keV peak fit
        min_bin = 500
        max_bin = 2000
        line_energy = 1150
        sigma_guess = 60
        bin_width = 10
        fit_half_width = 300
        do_use_step = True
        basename += "1064"

    if do_use_step:
        # http://radware.phy.ornl.gov/gf3/gf3.html#Fig.2.
        fit_formula += " + [6]*TMath::Erfc((x-[1])/sqrt(2)/[2])"
            

    n_bins = int((max_bin-min_bin)/bin_width)

    selection = []
    if channel == None:
        energy_var = "chargeEnergy"
        #energy_var = struck_analysis_parameters.get_single_site_cmd()
        #selection.append(struck_analysis_parameters.get_negative_energy_cut())
        #selection.append(struck_analysis_parameters.get_short_drift_time_cut())
        selection.append(struck_analysis_parameters.get_long_drift_time_cut())
    else:
        selection.append( "channel==%i" % channel)
        #selection.append( "rise_time_stop95-trigger_time>5.0")
        #selection.append( "rise_time_stop95-trigger_time>8.5")
    #print "\n".join(selection)



    fit_start_energy = line_energy - fit_half_width
    fit_stop_energy = line_energy + fit_half_width


    #-------------------------------------------------------------------------------

    if not do_individual_channels and channel != None:
        print "==> skipping individual channel %i" % channel
        return

    print "====> fitting channel:", channel

    canvas = TCanvas("canvas","", 700, 800)
    canvas.Divide(1,2)
    pad1 = canvas.cd(1)
    #canvas.SetLeftMargin(0.12)
    if channel != None:
        channel_name = struck_analysis_parameters.channel_map[channel]
        hist_title = "ch %i: %s" % (channel, channel_name)
    else:
        channel_name = "all"
        hist_title = "all channels"

    hist = TH1D("fit_hist", hist_title, n_bins, min_bin, max_bin)
    bin_width = hist.GetBinWidth(1)
    hist.SetXTitle("Energy [keV]")
    hist.GetYaxis().SetTitleOffset(1.2)
    resid_hist = hist.Clone("resid_hist") # use same binning, titles, etc.
    hist.SetYTitle("Counts / %.1f keV" % bin_width)

    resid_hist.SetYTitle("residual [#sigma]")
    resid_hist.SetTitle("")
    resid_hist.SetMarkerStyle(8)
    resid_hist.SetMarkerSize(0.8)



    draw_cmd = "%s >> fit_hist" % energy_var
    print "draw command:", draw_cmd

    selection = " && ".join(selection)
    print "selection:", selection

    hist_title += " " + selection
    hist.SetTitle(hist_title)
    entries = tree.Draw(draw_cmd, selection, "goff")
    print "tree entries: %i" % entries
    print "hist entries: %i" % hist.GetEntries()


    # setup the fit function, assuming things are already close to calibrated:
    testfit = TF1("testfit", fit_formula, fit_start_energy, fit_stop_energy)
    testfit.SetLineColor(TColor.kBlue)
    gaus_integral_guess = hist.GetBinContent(hist.FindBin(line_energy))*math.sqrt(2*math.pi)*sigma_guess
    fit_start_height = hist.GetBinContent(hist.FindBin(fit_start_energy))
    fit_stop_height = hist.GetBinContent(hist.FindBin(fit_stop_energy))
    print fit_start_height, fit_stop_height
    if fit_stop_height == 0.0: fit_stop_height = 1.0
    decay_const_guess = math.log(fit_stop_height/fit_start_height)/(fit_start_energy - fit_stop_energy)
    print "decay_const_guess:",  decay_const_guess
    #decay_const_guess = 0.0
    exp_height_guess = hist.GetBinContent(hist.FindBin(fit_start_energy))*math.exp(fit_start_energy*decay_const_guess)
    print "exp_height_guess", exp_height_guess

    testfit.SetParameters(
        gaus_integral_guess,   # peak counts
        line_energy,    # peak centroid
        sigma_guess,     # peak resolution
        exp_height_guess,    # exp decay height at zero energy
        decay_const_guess,   # exp decay constant
        0.0,
    )

    if do_use_step:
        testfit.SetParameter(6, gaus_integral_guess*0.01)

    fit_result = hist.Fit(testfit,"NIRLS")
    prob = fit_result.Prob()
    chi2 = fit_result.Chi2()
    ndf = fit_result.Ndf()


    resid_graph = TGraph()
    resid_graph.SetMarkerSize(0.8)
    resid_graph.SetMarkerStyle(8)

    # calculate residuals:
    x = fit_start_energy
    while x < fit_stop_energy:

        # calculate values from hist:
        i_bin = hist.FindBin(x)
        counts = hist.GetBinContent(i_bin)
        error = hist.GetBinError(i_bin)

        fit_counts = testfit.Integral(x, x+bin_width)/bin_width
        diff = counts - fit_counts

        if error == 0.0:
            residual = 0.0
            print "ZERO error at x=%.1f!" % x
        else:
            residual = diff / error


        if do_debug:
            print "bin: %i | low edge: %.1f | counts: %i +/- %.1f | fit counts: %.1f | diff:  %.1f | resid: %.1f" % (
                i_bin,
                hist.GetBinLowEdge(i_bin),
                counts,
                error,
                fit_counts,
                diff,
                residual,
            )

        resid_graph.SetPoint(
            resid_graph.GetN(),
            hist.GetBinCenter(i_bin),
            residual,
        )
        #resid_hist.SetBinContent(i_bin, residual)

        x += bin_width



    bestfit_exp = TF1("bestfite","[0]*TMath::Exp(-[1]*x) + [2]", fit_start_energy, fit_stop_energy)
    bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4), testfit.GetParameter(5))
    bestfit_exp.SetLineColor(TColor.kBlack)

    bestfit_gaus = TF1("bestfitg", "gausn(0)", fit_start_energy, fit_stop_energy)
    bestfit_gaus.SetParameters(testfit.GetParameter(0), testfit.GetParameter(1), testfit.GetParameter(2))
    bestfit_gaus.SetLineColor(TColor.kRed)

    if do_use_step:
        bestfit_step = TF1("bestfits", "[0]*TMath::Erfc((x-[1])/sqrt(2)/[2])", fit_start_energy, fit_stop_energy)
        bestfit_step.SetParameters(testfit.GetParameter(6), testfit.GetParameter(1), testfit.GetParameter(2))
        bestfit_step.SetLineColor(TColor.kGreen+2)

    calibration_ratio = line_energy/testfit.GetParameter(1)
    sigma = testfit.GetParameter(2) # *calibration_ratio
    if channel != None:
        new_calibration_value = struck_analysis_parameters.calibration_values[channel]*calibration_ratio
    else:
        new_calibration_value = calibration_ratio


    pad1 = canvas.cd(1)
    pad1.SetGrid(1,1)
    hist.SetMaximum(1.2*fit_start_height)
    peak_height = hist.GetBinContent(hist.FindBin(testfit.GetParameter(1)))
    if peak_height > fit_start_height:
        hist.SetMaximum(1.2*peak_height)
        print "peak height:", peak_height
    hist.Draw()
    testfit.Draw("same")
    bestfit_gaus.Draw("same")
    bestfit_exp.Draw("same")
    if do_use_step: bestfit_step.Draw("same")
    hist.Draw("same")

    n_peak_counts = testfit.GetParameter(0)/bin_width


    leg = TLegend(0.49, 0.7, 0.99, 0.9)
    leg.AddEntry(hist, "Data")
    leg.AddEntry(testfit, "Total Fit: #chi^{2}/DOF = %.1f/%i, P-val = %.1E" % (chi2, ndf, prob),"l")
    leg.AddEntry(bestfit_gaus, "Gaus Fit: #sigma = %.1f #pm %.1f keV, %.1E #pm %.1E cts" % ( 
        sigma, testfit.GetParError(2), n_peak_counts, testfit.GetParError(0)), "l")
    leg.AddEntry(bestfit_gaus, "centroid = %.1f #pm %.1f keV" % (testfit.GetParameter(1), testfit.GetParError(1)), "")
    leg.AddEntry(bestfit_exp,  "Exp + const background fit", "l")
    if do_use_step: 
        leg.AddEntry(bestfit_step, "Erfc step: height = %.1E #pm %.1E" % (testfit.GetParameter(6), testfit.GetParError(6)), "l")
    leg.SetFillColor(0)
    leg.Draw()

    resid_hist.SetMaximum(3.5)
    resid_hist.SetMinimum(-3.5)
    pad2 = canvas.cd(2)
    pad2.SetGrid(1,1)
    #resid_hist.Draw("hist P")
    resid_hist.Draw("")
    resid_graph.Draw("p")
    pad2.SetGrid(1,1)

    if channel != None:
        plot_name = "fit_ch%i_%s" % (channel, basename)
    else:
        plot_name = "fit_all_%s" % basename

    # log scale
    #pad1.SetLogy(1)
    #canvas.Update()
    #canvas.Print("%s_log.pdf" % plot_name)

    # lin scale
    pad1.SetLogy(0)
    hist.SetMinimum(0)
    canvas.Update()
    canvas.Print("%s_lin.pdf" % plot_name)

    # save some results
    result = {}
    result["channel"] = channel
    result["calibration_value"] = "%.6e" % new_calibration_value
    result["peak_counts"] = "%.2f" % n_peak_counts
    result["peak_counts_err"] = "%.2f" % (testfit.GetParError(0)/bin_width)
    result["centroid"] = "%.2f" % testfit.GetParameter(1)
    result["centroid_err"] = "%.2f" % testfit.GetParError(1)
    result["sigma"] = "%.2f" % sigma
    result["sigma_err"] = "%.2f" % testfit.GetParError(2)
    result["line_energy"] = "%.2f" % line_energy
    result["sigma_over_E"] = "%.3e" % (sigma/line_energy)
    result["ratio"] = "%.4f" % calibration_ratio # correction ratio
    result["fit_formula"] = fit_formula
    result["fit_start_energy"] = "%.2f" % fit_start_energy
    result["fit_stop_energy"] = "%.2f" % fit_stop_energy
    result["chi2"] = "%.3f" % chi2
    result["ndf"] = "%i" % ndf
    result["red_chi2"] = "%.3e" % chi2/ndf
    result["prob"] = "%.3e" % prob
    result["selection"] = selection
    result["draw_cmd"] = draw_cmd
    result["cuts_label"] = struck_analysis_parameters.get_cuts_label(draw_cmd, selection) 
    if do_use_step:
        result["step_height"] = testfit.GetParameter(6)
        result["step_height_err"] = testfit.GetParError(6)

    keys = result.keys()
    keys.sort()

    print "saved results:"
    for key in keys:
        print "\t%s : %s" % (key, result[key])


    if not gROOT.IsBatch():
        value = raw_input("any key to continue (b = batch, q to quit) ")
        if value == 'q':
            sys.exit()
        if value == 'b':
            gROOT.SetBatch(True)


    return result



def process_file(filename, do_1064_fit=False):

    print "--> processing", filename
    basename = os.path.splitext(os.path.basename(filename))[0]

    now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_')
    basename = now + basename
    print basename

    root_file = TFile(filename)
    tree = root_file.Get("tree")
    try:
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
    except AttributeError:
        print "could not get entries from tree"

    all_results = {}
    result = fit_channel(tree, None, basename, do_1064_fit)
    all_results["all"] = result

    for channel in struck_analysis_parameters.channels:
        if struck_analysis_parameters.charge_channels_to_use[channel]:
            result = fit_channel(tree, channel, basename, do_1064_fit)
            if result:
                all_results["channel %i" % channel] = result

    # write results to file
    result_file = file("fit_results_%s.txt" % basename, 'w')
    json.dump(all_results, result_file, indent=4, sort_keys=True)


if __name__ == "__main__":
    

    
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        sys.exit(1)

    process_file(sys.argv[1], do_1064_fit=False)
    process_file(sys.argv[1], do_1064_fit=True)

