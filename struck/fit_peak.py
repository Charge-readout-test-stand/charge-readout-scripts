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


def fit_channel(tree, channel, basename):

    #-------------------------------------------------------------------------------
    # options
    #-------------------------------------------------------------------------------

    energy_var = "energy1_pz"

    do_debug = False

    min_bin = 200
    max_bin = 1000
    n_bins = int((max_bin-min_bin)/5)
    line_energy = 570
    sigma_guess = 40

    fit_start_energy = 400
    fit_stop_energy = 770

    fit_formula = "gausn(0) + [3]*TMath::Exp(-[4]*x) + [5]"

    #-------------------------------------------------------------------------------

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


    if channel == None:
        #energy_var = "energy1_pz[0] + energy1_pz[1] + energy1_pz[2] + energy1_pz[3] + energy1_pz[4]"
        energy_var = "chargeEnergy"


    draw_cmd = "%s >> fit_hist" % energy_var
    print "draw command:", draw_cmd

    selection = [
        #"%s > 100" % energy_var,
    ]
    if channel != None:
        selection.append( "rise_time_stop95-trigger_time>8.5")
        selection.append( "channel==%i" % channel)
    #print "\n".join(selection)

    selection = " && ".join(selection)
    hist_title += " " + selection
    hist.SetTitle(hist_title)
    print "selection:", selection
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


    calibration_ratio = line_energy/testfit.GetParameter(1)
    sigma = testfit.GetParameter(2) # *calibration_ratio
    if channel != None:
        new_calibration_value = struck_analysis_parameters.calibration_values[channel]*calibration_ratio
    else:
        new_calibration_value = calibration_ratio


    pad1 = canvas.cd(1)
    pad1.SetGrid(1,1)
    hist.SetMaximum(1.2*fit_start_height)
    hist.Draw()
    testfit.Draw("same")
    bestfit_gaus.Draw("same")
    bestfit_exp.Draw("same")
    hist.Draw("same")

    n_peak_counts = testfit.GetParameter(0)/bin_width


    leg = TLegend(0.49, 0.7, 0.99, 0.9)
    leg.AddEntry(hist, "Data")
    leg.AddEntry(testfit, "Total Fit: #chi^{2}/DOF = %.1f/%i, P-val = %.1E" % (chi2, ndf, prob),"l")
    leg.AddEntry(bestfit_gaus, "Gaus Peak Fit: #sigma = %.1f #pm %.1f keV, %.1E cts" % (sigma, testfit.GetParError(2), n_peak_counts), "l")
    leg.AddEntry(bestfit_exp,  "Exp + const background fit", "l")
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
    result["peak counts"] = "%.2f" % n_peak_counts
    result["peak counts_err"] = "%.2f" % (testfit.GetParError(0)/bin_width)
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
    result["prob"] = "%.3e" % prob
    result["selection"] = selection
    result["draw_cmd"] = draw_cmd

    print "saved results:"
    for (key, value) in result.items():
        print "\t%s : %s" % (key, value)


    if not gROOT.IsBatch():
        value = raw_input("any key to continue (q to quit) ")
        if value == 'q':
            sys.exit()


    return result


def process_file(filename):

    print "--> processing", filename
    basename = os.path.splitext(os.path.basename(filename))[0]
    print basename

    root_file = TFile(filename)
    tree = root_file.Get("tree")
    try:
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
    except AttributeError:
        print "could not get entries from tree"

    all_results = {}
    result = fit_channel(tree, None, basename)
    all_results["all"] = result


    for channel in struck_analysis_parameters.channels:
        if struck_analysis_parameters.charge_channels_to_use[channel]:
            result = fit_channel(tree, channel, basename)
            all_results["channel %i" % channel] = result

    # write results to file
    result_file = file("fit_results_%s.txt" % basename, 'w')
    json.dump(all_results, result_file, indent=4, sort_keys=True)


if __name__ == "__main__":

    
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"

    process_file(sys.argv[1])

