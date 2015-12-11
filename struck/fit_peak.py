#!/bin/env python

"""
Script to calibrate energies based on location of 570-keV peak. 
Currently doing binned fit, using exponential background model
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
from ROOT import gSystem

import struck_analysis_parameters


def fit_channel(tree, channel, basename):

    #-------------------------------------------------------------------------------
    # options
    #-------------------------------------------------------------------------------

    energy_var = "energy1_pz"

    n_bins = 200
    max_bin = 2000
    line_energy = 570
    sigma_guess = 40

    fit_start_energy = 300
    fit_stop_energy = 800
    fit_start_energy = line_energy - 200
    fit_stop_energy = line_energy + 250

    fit_formula = "gausn(0) + [3]*TMath::Exp(-[4]*x)"
    #-------------------------------------------------------------------------------

    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)
    canvas.SetLeftMargin(0.12)
    channel_name = struck_analysis_parameters.channel_map[channel]

    hist = TH1D("fit_hist", "channel %i: %s" % (channel, channel_name), 
        n_bins, 0, max_bin)
    bin_width = hist.GetBinWidth(1)
    hist.SetXTitle("Energy [keV]")
    hist.SetYTitle("Counts / %.1f keV" % bin_width)
    hist.GetYaxis().SetTitleOffset(1.3)


    draw_cmd = "%s >> fit_hist" % energy_var
    print "draw command:", draw_cmd

    selection = [
        "channel==%i" % channel,
        #"%s > 100" % energy_var,
    ]
    #print "\n".join(selection)

    selection = " && ".join(selection)
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
        decay_const_guess   # exp decay constant
    )


    hist.Fit(testfit,"IRLS")

    bestfit_exp = TF1("bestfite","[0]*TMath::Exp(-[1]*x)", fit_start_energy, fit_stop_energy)
    bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4))
    bestfit_exp.SetLineColor(TColor.kBlack)

    bestfit_gaus = TF1("bestfitg", "gausn(0)", fit_start_energy, fit_stop_energy)
    bestfit_gaus.SetParameters(testfit.GetParameter(0), testfit.GetParameter(1), testfit.GetParameter(2))
    bestfit_gaus.SetLineColor(TColor.kRed)


    calibration_ratio = line_energy/testfit.GetParameter(1)
    sigma = testfit.GetParameter(2)*calibration_ratio
    new_calibration_value = struck_analysis_parameters.calibration_values[channel]*calibration_ratio


    hist.Draw()
    bestfit_gaus.Draw("same")
    bestfit_exp.Draw("same")


    leg = TLegend(0.6, 0.7, 0.95, 0.90)
    leg.AddEntry(hist, "Data")
    leg.AddEntry(testfit, "Total Fit","l")
    leg.AddEntry(bestfit_gaus, "Gaus Peak Fit (#sigma = %.1f keV)" % sigma, "l")
    leg.AddEntry(bestfit_exp,  "Exp Background Fit", "l")
    leg.SetFillColor(0)
    leg.Draw()

    # log scale
    canvas.Update()
    canvas.Print("fit_ch%i_%s_log.pdf" % (channel, basename))

    # lin scale
    #hist.SetMaximum(1.5*hist.GetBinContent(hist.FindBin(line_energy)))
    hist.SetMaximum(1.1*fit_start_height)
    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("fit_ch%i_%s_lin.pdf" % (channel, basename))

    if not gROOT.IsBatch():
        value = raw_input("any key to continue (q to quit) ")
        if value == 'q':
            sys.exit()

    # save some results
    result = {}
    result["channel"] = channel
    result["calibration_value"] = "%.6e" % new_calibration_value
    result["peak counts"] = "%.2f" % testfit.GetParameter(0)
    result["sigma"] = "%.3f" % sigma  # sigma, keV
    result["line_energy"] = "%.2f" % line_energy
    result["sigma_over_E"] = "%.3e" % (sigma/line_energy)
    result["ratio"] = "%.4f" % calibration_ratio # correction ratio
    result["fit_formula"] = fit_formula
    result["fit_start_energy"] = "%.2f" % fit_start_energy
    result["fit_stop_energy"] = "%.2f" % fit_stop_energy

    for (key, value) in result.items():
        print "%s : %s" % (key, value)

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

