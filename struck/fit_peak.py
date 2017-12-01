#!/bin/env python

"""
Script to calibrate energies based on location of 570-keV peak. 
Currently doing binned fit, using exponential background model

All channels (SignalEnergy) are fit first, then each channel individually. 

This script was adapted from mca/fit_to_resolution.py 

#Single Channel and MC Fits
python fit_peak.py /p/lscratchd/alexiss/11th_LXe/2017_02_01_overnight_vme/tier3_added/overnight_11thLXeB_v5.root

#Full Fit for MC
python fit_peak.py /p/lscratchd/alexiss/mc/Bi207_Full_Ralph_dcoeff50_11thLXe/Bi207_Full_Ralph_dcoeff50_7000.root

"""


import os
import sys
import json
import math
import commands
import datetime
import numpy as np
from array import array

import ROOT
ROOT.gROOT.SetBatch(True) # run in batch mode

import struck_analysis_parameters
import struck_analysis_cuts

# set ROOT style:
ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       


def fit_channel(
    tree, 
    channel, # channel number, or None for all channels
    basename, 
    do_1064_fit, # wheter to fit 1064-keV peak instead of 570
    all_energy_var, # used if channel==None, usually "SignalEnergy"
    selection, # selection for draw commands
    do_use_step=False, # whether to use Erfc step
    min_bin=200, # just for drawing plots
    max_bin=1200, # just for plotting
    line_energy = 570, # calibrated energy
    #line_energy = 585, # calibrated energy
    #line_energy = 487, # 10th LXe FIXME
    #line_energy = 565,
    fit_half_width=170,#120, # half width for fit range
    do_use_exp=True, # whether to use exponential function in the fit
    energy_var = "energy1_pz", # energy variable
    zslice = None,
    do_use_erf=False
):
    """
    Perform a fit of one channel, or all channels together if channel is None. 
    """

    #-------------------------------------------------------------------------------
    # options
    #-------------------------------------------------------------------------------

    do_debug = False # print some debugging info
    do_individual_channels = True # whether to fit individual channels

    # defaults for 570-keV
    bin_width = 5
    #line_energy = 620

    sigma_guess = 40
    if do_1064_fit: # 1064-keV peak fit
        min_bin = 500
        max_bin = 2000
        line_energy = 1150
        #line_energy = 1063
        sigma_guess = 60
        bin_width = 10
        fit_half_width = 300
        do_use_step = True


    fit_center = line_energy # the usual
    #fit_center = 530 # FIXME for 10th LXe
    fit_start_energy = fit_center - fit_half_width
    fit_stop_energy = fit_center + fit_half_width
    print "fit_start_energy", fit_start_energy
    print "fit_stop_energy", fit_stop_energy


    #-------------------------------------------------------------------------------
    # form strings for the TFormula to describe the fit function
    #-------------------------------------------------------------------------------

    # main part: gaus + exponential bkg or linear bkg
    step_amplitude_index = 6
    if do_use_exp:
        fit_formula = "gausn(0) + [3]*TMath::Exp(-[4]*x) + [5]"
    else:
        fit_formula = "gausn(0) + pol1(3)" # 1st-degree polynomial
        step_amplitude_index = 5
        #fit_formula = "gausn(0) + pol2(3)" # 2nd-degree polynomial
        #fit_formula = "gausn(0)" 

    # add a compton shoulder/step
    if do_use_step:
        # http://radware.phy.ornl.gov/gf3/gf3.html#Fig.2.
        fit_formula += " + [%i]*TMath::Erfc((x-[1])/sqrt(2)/[2])" % step_amplitude_index

        # exp tail
        # y = constant * EXP( (x-c)/beta ) * ERFC( (x-c)/(SQRT(2)*sigma) + sigma/(SQRT(2)*beta) )
        #fit_formula += " + [%i]*exp((x-[1])/[%i])*TMath::Erfc((x-[1])/sqrt(2)/[2] + [2]/sqrt(2)/[%i])" % (
        #    step_amplitude_index, step_amplitude_index+1, step_amplitude_index+1)
            
    if channel == None: # this is the sum energy
        plot_name = "%s/fit_all_%s" % (basename, basename)
        energy_var = all_energy_var
    else: # this is an individual channel
        plot_name = "%s/fit_ch%i_%s" % (basename, channel, basename)
        selection_list = []
        selection_list.append("(channel==%i)" % channel)
        if channel_selection != None: selection_list.append(channel_selection)
        selection = " && ".join(selection_list)
    if zslice != None:
        plot_name += "_zslice%i" % zslice

    n_bins = int((max_bin-min_bin)/bin_width)

    #-------------------------------------------------------------------------------

    isMC = struck_analysis_parameters.is_tree_MC(tree)
    if isMC:
        print "this is MC!"

    if not do_individual_channels and channel != None:
        print "==> skipping individual channel %i" % channel
        return

    print "====> fitting channel:", channel

    canvas = ROOT.TCanvas("canvas","", 700, 800)
    canvas.Divide(1,2)
    pad1 = canvas.cd(1)
    #canvas.SetLeftMargin(0.12)
    if channel != None:
        try:
            channel_name = struck_analysis_parameters.channel_map[channel]
        except KeyError:
            channel_name = "?"
        hist_title = "ch %i: %s" % (channel, channel_name)
    else:
        channel_name = "all"
        hist_title = "all channels"

    hist = ROOT.TH1D("fit_hist", hist_title, n_bins, min_bin, max_bin)
    bin_width = hist.GetBinWidth(1)
    hist.SetXTitle("Energy [keV]")
    hist.GetYaxis().SetTitleOffset(1.2)
    resid_hist = hist.Clone("resid_hist") # use same binning, titles, etc.
    hist.SetYTitle("Counts / %.1f keV" % bin_width)

    resid_hist.SetYTitle("residual [#sigma]")
    resid_hist.SetTitle("")
    resid_hist.SetMarkerStyle(8)
    resid_hist.SetMarkerSize(0.8)

    # test new calibration:
    if channel != None:
        tree.GetEntry(0)
        cal_vals = array('d',tree.calibration)
        print "calibration:", cal_vals[channel]
        draw_cmd = "%s*%s/calibration >> fit_hist" % (
            energy_var,
            struck_analysis_parameters.calibration_values[channel], 
        )
    else:
        draw_cmd = "%s >> fit_hist" % energy_var
        #if isMC:
            #draw_cmd = "%s*1.05 >> fit_hist" % energy_var #Old from Alexis to make it look like data I think 
            #draw_cmd = "%s*1.0 >> fit_hist" % energy_var # what is in ../mc/compareMCtoData_noise_branch.py
        #else:
            #draw_cmd = "%s*0.976027397260274 >> fit_hist" % energy_var #this is for 570.0
        #    draw_cmd  = "%s*0.956937799043 >> fit_hist" % energy_var #this is from the mc draw_cmd in ../mc/compareMCtoData_noise_branch.py

    print "draw command:", draw_cmd
    print "selection:"
    print "\t" + "\n\t||".join(selection.split("||"))

    hist_title += " " + selection[:150] + " ..."
    hist.SetTitle(hist_title)
    entries = tree.Draw(draw_cmd, selection, "goff")
    print "tree entries: %i" % entries
    print "hist entries: %i" % hist.GetEntries()

    #-------------------------------------------------------------------------------
    # parameter estimates
    #-------------------------------------------------------------------------------

    # setup the fit function, assuming things are already close to calibrated:
    testfit = ROOT.TF1("testfit", fit_formula, fit_start_energy, fit_stop_energy)
    testfit.SetLineColor(ROOT.kBlue)
    fit_start_height = hist.GetBinContent(hist.FindBin(fit_start_energy))
    fit_stop_height = hist.GetBinContent(hist.FindBin(fit_stop_energy))
    print "\tfit_stop_height", fit_stop_height
    print "\tfit_start_height", fit_start_height
    if fit_stop_height == 0.0: fit_stop_height = 1.0
    try:
        decay_const_guess = math.log(fit_stop_height/fit_start_height)/(fit_start_energy - fit_stop_energy)
    except ZeroDivisionError:
        decay_const_guess = 0.0
    if do_use_exp:
        exp_height_guess = hist.GetBinContent(hist.FindBin(fit_start_energy))*math.exp(fit_start_energy*decay_const_guess)
        bkg_height = exp_height_guess*math.exp(-line_energy*decay_const_guess)
        print "\tdecay_const_guess:",  decay_const_guess
        print "\texp_height_guess", exp_height_guess
    else:
        slope_guess = (fit_stop_height - fit_start_height)/(fit_stop_energy-fit_start_energy)
        const_guess = fit_stop_height-slope_guess*fit_stop_energy
        print "\tconst_guess:", const_guess
        print "\tslope_guess:", slope_guess
        bkg_height = const_guess + line_energy*slope_guess 
    print "\tbackground height under peak:", bkg_height
    gaus_height_guess = hist.GetBinContent(hist.FindBin(line_energy)) - bkg_height

    # estimate the peak width, sigma
    if channel != None:
        sigma_guess = (
            (struck_analysis_parameters.rms_keV[channel]*math.sqrt(2.0/struck_analysis_parameters.n_baseline_samples))**2 + \
            struck_analysis_parameters.resolution_guess**2
        )**0.5

    gaus_integral_guess = gaus_height_guess*math.sqrt(2*math.pi)*sigma_guess
    if gaus_integral_guess < 0:
        print "\t gaus_integral_guess was less than 0:", gaus_integral_guess
        gaus_integral_guess = 300.0
    print "\tgaus_height_guess:", gaus_height_guess
    print "\tgaus_integral_guess:", gaus_integral_guess
    print "\tsigma_guess:", sigma_guess
    centroid_guess = line_energy # + 30.0
    print "\tcentroid_guess:", centroid_guess

    if do_use_exp:
        testfit.SetParameters(
            gaus_integral_guess,   # peak counts
            centroid_guess,    # peak centroid
            sigma_guess,     # peak resolution
            exp_height_guess,    # exp decay height at zero energy
            decay_const_guess,   # exp decay constant
            0.0
        )
    else:
        testfit.SetParameters(
            gaus_integral_guess,   # peak counts
            centroid_guess,    # peak centroid
            sigma_guess,     # peak resolution
            const_guess,    # a0
            slope_guess,   # a1
        )
        testfit.SetParameter(5, 0.0)

    if do_use_step:
        step_height_guess = gaus_integral_guess*0.0001
        print "\tstep height guess:", step_height_guess
        testfit.SetParameter(step_amplitude_index, step_height_guess)
        testfit.SetParameter(step_amplitude_index+1, 20.0)

    original_max = hist.GetMaximum()
    
    if do_debug: # show functions before fit

        if do_use_exp:
            bestfit_exp = ROOT.TF1("bestfite","[0]*TMath::Exp(-[1]*x) + [2]", fit_start_energy, fit_stop_energy)
            bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4), testfit.GetParameter(5))
        else:
            #bestfit_exp = ROOT.TF1("bestfite","pol1(0)", fit_start_energy, fit_stop_energy)
            #bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4))
            bestfit_exp = ROOT.TF1("bestfite","pol1(0)", fit_start_energy, fit_stop_energy)
            bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4), testfit.GetParameter(5))
        bestfit_exp.SetLineColor(ROOT.kBlack)

        bestfit_gaus = ROOT.TF1("bestfitg", "gausn(0)", fit_start_energy, fit_stop_energy)
        bestfit_gaus.SetParameters(testfit.GetParameter(0),
            testfit.GetParameter(1), testfit.GetParameter(2))
        bestfit_gaus.SetLineColor(ROOT.kRed)

        if do_use_step:
            bestfit_step = ROOT.TF1("bestfits", "[0]*TMath::Erfc((x-[1])/sqrt(2)/[2])", fit_start_energy, fit_stop_energy)
            #bestfit_step = ROOT.TF1("bestfits", "[0]*exp((x-[1])/[3])*TMath::Erfc((x-[1])/sqrt(2)/[2] + [2]/sqrt(2)/[3])", fit_start_energy, fit_stop_energy)
            bestfit_step.SetParameters(testfit.GetParameter(step_amplitude_index), 
                testfit.GetParameter(1), testfit.GetParameter(2), testfit.GetParameter(step_amplitude_index+1))
            bestfit_step.SetLineColor(ROOT.kGreen+2)

        pad1 = canvas.cd(1)
        pad1.SetGrid(1,1)
        hist.SetMaximum(1.2*fit_start_height)
        #peak_height = hist.GetBinContent(hist.FindBin(line_energy))
        peak_height = testfit.Eval(testfit.GetParameter(1))
        if peak_height > fit_start_height:
            hist.SetMaximum(1.2*peak_height)
            print "peak height:", peak_height
        hist.Draw()
        testfit.Draw("same")
        bestfit_gaus.Draw("same")
        bestfit_exp.Draw("same")
        if do_use_step: bestfit_step.Draw("same")
        hist.Draw("same")


        leg = ROOT.TLegend(0.49, 0.7, 0.99, 0.9)
        leg.AddEntry(hist, "Data (%i entries)" % hist.GetEntries())
        leg.AddEntry(testfit, "Total Fit fcn before fit","l")
        leg.AddEntry(bestfit_gaus, 
            "Gaus Peak: #sigma=%.1f, centroid = %.1f" % (
                testfit.GetParameter(2),
                testfit.GetParameter(1),
            ),
            "l"
        )

        if do_use_exp:
            leg.AddEntry(bestfit_exp,  "Exp + const", "l")
        else:
            leg.AddEntry(bestfit_exp,  "linear bkg", "l")
        if do_use_step: 
            leg.AddEntry(bestfit_step, "Erfc step: height = %.1E #pm %.1E" % (testfit.GetParameter(step_amplitude_index), testfit.GetParError(step_amplitude_index)), "l")
        leg.SetFillColor(0)
        leg.Draw()
        hist.SetMinimum(0)
        canvas.Update()
        canvas.Print("%s_pre_lin.pdf" % plot_name)

        if not ROOT.gROOT.IsBatch():
            value = raw_input("any key to continue (b = batch, q to quit) ")
            if value == 'q':
                sys.exit()
            if value == 'b':
                ROOT.gROOT.SetBatch(True)

    #-------------------------------------------------------------------------------
    # do the fit
    #-------------------------------------------------------------------------------
    ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(50000)
    fit_result = hist.Fit(testfit,"NIRLS")
    prob = fit_result.Prob()
    chi2 = fit_result.Chi2()
    ndf = fit_result.Ndf()
    fit_status = fit_result.Status()

    resid_graph = ROOT.TGraph()
    resid_graph.SetMarkerSize(0.8)
    resid_graph.SetMarkerStyle(8)

    # calculate residuals:
    x = fit_start_energy
    resid_min = -3.5
    resid_max = 3.5
    while x < fit_stop_energy: # loop over bins

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
        if residual > resid_max: resid_max = residual
        if residual < resid_min: resid_min = residual

        x += bin_width


    print "--> grabbing fit parameters"
    # grab fit parameters
    centroid = testfit.GetParameter(1)
    centroid_err = testfit.GetParError(1)
    calibration_ratio = line_energy/centroid
    calibration_ratio_err = line_energy/(centroid*centroid)*centroid_err
    sigma = testfit.GetParameter(2) # *calibration_ratio
    sigma_err = testfit.GetParError(2) # *calibration_ratio
    n_peak_counts = testfit.GetParameter(0)/bin_width
    n_peak_counts_err = testfit.GetParError(0)/bin_width

    # set up some functions
    if do_use_exp:
        print "--> grabbing exp parameters"
        bestfit_exp = ROOT.TF1("bestfite","[0]*TMath::Exp(-[1]*x) + [2]", fit_start_energy, fit_stop_energy)
        bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4), testfit.GetParameter(5))
    else:
        print "--> grabbing pol1 parameters"
        bestfit_exp = ROOT.TF1("bestfite","pol1(0)", fit_start_energy, fit_stop_energy)
        bestfit_exp.SetParameters(testfit.GetParameter(3), testfit.GetParameter(4))
    bestfit_exp.SetLineColor(ROOT.kBlack)


    print "--> grabbing gauss parameters"
    bestfit_gaus = ROOT.TF1("bestfitg", "gausn(0)", fit_start_energy, fit_stop_energy)
    bestfit_gaus.SetParameters(testfit.GetParameter(0), centroid, sigma)
    bestfit_gaus.SetLineColor(ROOT.kRed)

    if do_use_step:
        print "--> grabbing step parameters"
        bestfit_step = ROOT.TF1("bestfits", "[0]*TMath::Erfc((x-[1])/sqrt(2)/[2])", fit_start_energy, fit_stop_energy)
        #bestfit_step = ROOT.TF1("bestfits", "[0]*exp((x-[1])/[3])*TMath::Erfc((x-[1])/sqrt(2)/[2] + [2]/sqrt(2)/[3])", fit_start_energy, fit_stop_energy)
        bestfit_step.SetParameters(testfit.GetParameter(step_amplitude_index), 
            centroid, sigma)
        bestfit_step.SetLineColor(ROOT.kGreen+2)

    if channel != None:

        # grab old calibration values:
        if isMC:
            calibration_value = struck_analysis_parameters.Wvalue
        else:
            calibration_value = struck_analysis_parameters.calibration_values[channel]

        new_calibration_value = calibration_value*calibration_ratio
        new_calibration_value_err = calibration_value*calibration_ratio_err
    else:
        new_calibration_value = calibration_ratio
        new_calibration_value_err = calibration_ratio_err


    # draw the fit results
    pad1 = canvas.cd(1)
    pad1.SetGrid(1,1)
    hist.SetMaximum(1.2*fit_start_height)
    #peak_height = hist.GetBinContent(hist.FindBin(centroid))
    peak_height = testfit.Eval(centroid)
    if peak_height > fit_start_height:
        hist.SetMaximum(1.2*peak_height)
        print "peak height:", peak_height
    hist.Draw()
    testfit.Draw("same")
    bestfit_gaus.Draw("same")
    bestfit_exp.Draw("same")
    if do_use_step: bestfit_step.Draw("same")
    hist.Draw("same")

    print plot_name
    roo_out_name = "%s_output.root" % plot_name
    print "Saving to ROOT file", roo_out_name
    raw_input()
    root_file = ROOT.TFile(roo_out_name, "RECREATE")
    root_file.WriteTObject(hist)
    root_file.WriteTObject(testfit)
    root_file.WriteTObject(bestfit_exp)
    root_file.WriteTObject(bestfit_gaus)
    if do_use_step: root_file.WriteTObject(bestfit_step)
    root_file.Close()

    leg = ROOT.TLegend(0.49, 0.7, 0.99, 0.9)
    leg.AddEntry(hist, "Data (%i entries)" % hist.GetEntries())
    leg.AddEntry(testfit, "Total Fit: #chi^{2}/DOF = %.1f/%i, P-val = %.1E" % (chi2, ndf, prob),"l")
    leg.AddEntry(bestfit_gaus, "Gaus Peak: #sigma = %.1f #pm %.1f keV, %.1E #pm %.1E cts" % ( 
        sigma, sigma_err, n_peak_counts, n_peak_counts_err), "l")
    leg.AddEntry(bestfit_gaus, "#bar{x} = %.1f #pm %.1f keV | status=%i | #sigma/E = %.2f #pm %.2f" % (
        centroid, centroid_err, fit_status, sigma/centroid*100.0, sigma_err/centroid*100.0) + "%", "")
    if do_use_exp:
        leg.AddEntry(bestfit_exp,  "Exp + const", "l")
    else:
        leg.AddEntry(bestfit_exp,  "linear bkg", "l")
    if do_use_step: 
        leg.AddEntry(bestfit_step, "Erfc step: height = %.1E #pm %.1E" % (testfit.GetParameter(step_amplitude_index), testfit.GetParError(step_amplitude_index)), "l")

    leg.SetFillColor(0)
    leg.Draw()

    # draw residuals
    resid_hist.SetMaximum(resid_max+0.1)
    resid_hist.SetMinimum(resid_min-0.1)
    pad2 = canvas.cd(2)
    pad2.SetGrid(1,1)
    #resid_hist.Draw("hist P")
    resid_hist.Draw("")
    resid_graph.Draw("p")
    pad2.SetGrid(1,1)

    # log scale
    #pad1.SetLogy(1)
    #canvas.Update()
    #canvas.Print("%s_log.pdf" % plot_name)

    pad1.cd()
    pave_text = ROOT.TPaveText(0.01, 0.01, 0.2, 0.05, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    pave_text.SetTextAlign(11)
    try:
        cuts_label = struck_analysis_cuts.get_cuts_label(draw_cmd, selection) 
        pave_text.AddText(cuts_label)
    except:
        print "==> No cuts label"
        cuts_label = ""


    # lin scale
    pad1.SetLogy(0)
    pave_text.Draw()
    hist.SetMinimum(0)
    canvas.Update()
    print "original_max:", original_max
    print "max", hist.GetMaximum()
    #hist.SetMaximum(original_max*1.2)
    canvas.Print("%s_lin.pdf" % plot_name)
    print "printed %s" % plot_name

    # save some results for json file
    result = {}
    result["a_label"] = channel_name
    result["channel"] = channel
    result["calibration_value"] = "%.6e" % new_calibration_value
    result["peak_counts"] = "%.2f" % n_peak_counts
    result["peak_counts_err"] = "%.2f" % n_peak_counts_err
    result["integral_counts"] = hist.Integral(hist.FindBin(fit_start_energy), hist.FindBin(fit_stop_energy))
    result["centroid"] = "%.2f" % centroid
    result["centroid_err"] = "%.2f" % centroid_err
    result["sigma"] = "%.2f" % sigma
    result["sigma_err"] = "%.2f" % sigma_err
    result["line_energy"] = "%.2f" % line_energy
    result["sigma_over_E"] = "%.3e" % (sigma/centroid)
    result["sigma_over_E_err"] = "%.3e" % (sigma_err/centroid)
    result["ratio"] = "%.4f" % calibration_ratio # correction ratio
    result["fit_formula"] = fit_formula
    result["fit_start_energy"] = "%.2f" % fit_start_energy
    result["fit_stop_energy"] = "%.2f" % fit_stop_energy
    result["chi2"] = "%.3f" % chi2
    result["ndf"] = "%i" % ndf
    result["red_chi2"] = "%.3e" % (chi2/ndf)
    result["prob"] = "%.3e" % prob
    result["selection"] = selection
    result["draw_cmd"] = draw_cmd
    result["cuts_label"] = cuts_label
    result["fit_status"] = fit_status
    if do_use_step:
        result["step_height"] = testfit.GetParameter(step_amplitude_index)
        result["step_height_err"] = testfit.GetParError(step_amplitude_index)
    result["do_use_exp"] = do_use_exp

    keys = result.keys()
    keys.sort()

    print "saved results:"
    for key in keys:
        print "\t%s : %s" % (key, result[key])
        

    # write stuff to file -- if channel is None, we are fitting all channels 
    label = "all"
    ch_label = "all"
    if channel != None:
        label = struck_analysis_parameters.channel_map[channel]
        ch_label = channel

    new_calibration = "calibration_values[%s] = %.6f # +/- %.6f " % (
        ch_label, 
        new_calibration_value,
        new_calibration_value_err,
    )
    new_calibration += label
    if channel == None:
        new_calibration = "# " + new_calibration
    print new_calibration
    new_calib_file = file("%s/new_calib_%s.txt" % (basename, basename),"a")
    new_calib_file.write(new_calibration + "\n")
    new_calib_file.close()


    if not ROOT.gROOT.IsBatch():
        value = raw_input("any key to continue (b = batch, q to quit) ")
        if value == 'q':
            sys.exit()
        if value == 'b':
            ROOT.gROOT.SetBatch(True)

    return result



def process_file(
    filename, 
    do_1064_fit=False,
    all_energy_var="SignalEnergy",
    selection="",
    channel_selection="",
    do_use_step=True,
    energy_var="energy1_pz",
    do_use_exp=True,
):
    """
    Process one file, fitting all channels
    """

    print "--> processing", filename
    basename = os.path.splitext(os.path.basename(filename))[0]

    if do_use_step:
        basename = "step_" + basename

    # cuts label prefix:
    if all_energy_var!= None:
        cuts_label = struck_analysis_cuts.get_cuts_label(all_energy_var, selection) 
        cuts_label = "_".join(cuts_label.split("+"))
        basename = cuts_label + "_" + basename

    # prepend line energy to baseline
    if do_1064_fit:
        basename = "1064_" + basename
    else:
        basename = "570_" + basename

    # append date & time to basename
    now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_')
    basename = basename + "_" + now

    print basename
    cmd = "mkdir %s" % basename
    #print cmd
    output = commands.getstatusoutput(cmd)
    if output[0] != 0:
        print output[1]

    root_file = ROOT.TFile(filename)
    tree = root_file.Get("tree")
    try:
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
    except AttributeError:
        print "could not get entries from tree"

    # speed things up by only turning on the branches we need
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus(all_energy_var,1)
    tree.SetBranchStatus("SignalEnergy",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("is_bad",1)
    tree.SetBranchStatus("is_pulser",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("calibration",1)
    tree.SetBranchStatus("energy1_pz",1)
    tree.SetBranchStatus("trigger_time",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)
    tree.SetBranchStatus("rise_time_stop95",1)
    if "nXsignals" in selection:
        tree.SetBranchStatus("nXsignals",1)
    if "nYsignals" in selection:
        tree.SetBranchStatus("nYsignals",1)
    if "nsignal_strips" in selection:
        tree.SetBranchStatus("nsignal_strips",1)

    # start the calibration file
    print "%s/new_calib_%s.txt" % (basename, basename)
    new_calib_file = file("%s/new_calib_%s.txt" % (basename, basename),"w")
    new_calib_file.write("# basename: %s \n" % basename)
    new_calib_file.write("# selection: %s \n" % selection)
    new_calib_file.write("# channel_selection: %s \n" % selection)
    new_calib_file.close()

    raw_input("===============Pause===============")
    all_results = {}
    #if all_energy_var != None:
    if True:
        #Skip if only want single channels
        result = fit_channel(tree, None, basename, do_1064_fit, all_energy_var, selection, do_use_step, do_use_exp=do_use_exp)
        all_results["all"] = result
    else:
        print "Skipping the Full Fit"

    raw_input("==============Pause==================")

    isMC = struck_analysis_parameters.is_tree_MC(tree)

    if isMC:
        charge_channels_to_use = struck_analysis_parameters.MCcharge_channels_to_use
    else:
        charge_channels_to_use = struck_analysis_parameters.charge_channels_to_use
    
    print "Chs to use", charge_channels_to_use
    
    #charge_channels_to_use[:]   = np.zeros_like(charge_channels_to_use)
    #charge_channels_to_use[21]  = 1
    #charge_channels_to_use[7]   = 1
    raw_input("=============Pasue==============")

    for channel, value in enumerate(charge_channels_to_use):
        print channel, value, struck_analysis_parameters.channel_map[channel]
        raw_input("========Pause===============")
        #continue # skipping indiv channels for now... 
        if value:
            result = fit_channel(tree, channel, basename, do_1064_fit, all_energy_var, channel_selection, do_use_step, energy_var=energy_var, do_use_exp=do_use_exp)
            if result:
                all_results["channel %i" % channel] = result

    # write results to file
    result_file = file("%s/fit_results_%s.txt" % (basename, basename), 'w')
    json.dump(all_results, result_file, indent=4, sort_keys=True)


if __name__ == "__main__":
    

    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        sys.exit(1)

    tfile = ROOT.TFile(sys.argv[1])
    tree = tfile.Get("tree")
    isMC = struck_analysis_parameters.is_tree_MC(tree)


    #drift_time_high=9.0 # microseconds
    drift_time_high = struck_analysis_parameters.max_drift_time+2.0

    # best cut so far for 11B:
    # nXsignals==1 && nYsignals==1 && nsignal_strips==2 &&
    # rise_time_stop95_sum-trigger_time >= 9.465 &&
    # rise_time_stop95_sum-trigger_time <= 15.615

    # selections for the SignalEnergy plot
    selection = []
    selection.append(struck_analysis_cuts.get_single_strip_cut())
    selection.append(struck_analysis_cuts.get_drift_time_selection( drift_time_high=drift_time_high, isMC=isMC))

    # best cuts so far for 11B:
    if True:
        selection = []

        #For Total Energy
        selection.append("nXsignals==1")
        selection.append("nYsignals==1")
        selection.append("nsignal_strips==2")

        #For Singal Strip Calibration do
        #selection.append("nsignals==1")
        #selection.append("(nXsignals==1 || nYsignals==1)")

        selection.append(struck_analysis_cuts.get_drift_time_selection(
            drift_time_high=struck_analysis_parameters.max_drift_time-0.5))
            #drift_time_high=struck_analysis_parameters.max_drift_time-1.0))



    selection.append("!is_pulser")
    selection.append("!is_bad") 
    selection = " && ".join(selection)

    # selections for individual channels
    channel_selection = selection

    #channel_selection = []
    ##channel_selection.append(struck_analysis_cuts.get_drift_time_cut(is_single_channel=True, drift_time_high=drift_time_high))
    #channel_selection.append(struck_analysis_cuts.get_single_strip_cut())
    #channel_selection.append("!is_pulser")
    #channel_selection.append("!is_bad")
    #channel_selection = " && ".join(channel_selection)
    ##channel_selection = None

    all_energy_var = "SignalEnergy"
    #all_energy_var = None
    #if isMC: all_energy_var = "SignalEnergy*1.05" # 11B
    print "all_energy_var:", all_energy_var
    do_use_step=False
    do_use_exp=True
    do_1064_fit=False

    print selection
    print channel_selection
    
    raw_input("--------------PAUSE----------------")

    for filename in sys.argv[1:]:
        process_file(filename, do_1064_fit, all_energy_var, selection, channel_selection, do_use_step=do_use_step, energy_var="energy1_pz", do_use_exp=do_use_exp)

