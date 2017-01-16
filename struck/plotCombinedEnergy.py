
import os
import sys
import ROOT
#ROOT.gROOT.SetBatch(True)

import struck_analysis_cuts
import struck_analysis_parameters

canvas = ROOT.TCanvas()
canvas.SetLeftMargin(0.12)
canvas.SetGrid()

def get_hist(tree, draw_cmd, selection, name="hist"):
     

    # options
    energy_max = 3000.0
    n_bins = int(energy_max/5.0)
    hist = ROOT.TH1D(name, name, n_bins, 0, energy_max)
    hist.GetDirectory().cd()
    hist.SetLineWidth(2)
    hist.SetXTitle("Energy [keV]")
    hist.SetYTitle("Counts / %s keV" % (energy_max/n_bins))
    hist.GetYaxis().SetTitleOffset(1.5)
    hist.SetMarkerStyle(21)
    hist.SetMarkerSize(0.9)

    print "--> making hist", name
    print "\t draw_cmd:", draw_cmd
    print "\t selection:", selection
    n_drawn = tree.Draw("%s >> %s" % (draw_cmd, hist.GetName()), selection, "goff")
    print "\t %i drawn | %i in %s" % (n_drawn, hist.GetEntries(), hist.GetName())

    # 570-keV peak
    hist.SetAxisRange(400, 1400)
    line_energy = hist.GetBinCenter(hist.GetMaximumBin())
    print "line_energy:", line_energy
    hist.SetLineColor(ROOT.kBlue+2) # for the fit
    delta_E = 70.0
    fcn = ROOT.TF1("fcn","gaus(0)",line_energy-delta_E, line_energy+delta_E)
    fcn.SetParameter(0, hist.GetBinContent(hist.FindBin(line_energy))) # peak height
    fcn.SetParameter(1, line_energy) # mean
    fcn.SetParameter(2, 60.0) # sigma
    fcn.SetLineColor(ROOT.kRed)

    # 1063-keV peak
    hist.SetAxisRange(1000, 1400)
    line_energy = hist.GetBinCenter(hist.GetMaximumBin())
    print "line_energy:", line_energy
    hist.SetLineColor(ROOT.kBlue+2) # for the fit
    delta_E = 65.0
    fcn2 = ROOT.TF1("fcn2","gaus(0)",line_energy-delta_E, line_energy+delta_E)
    fcn2.SetParameter(0, hist.GetBinContent(hist.FindBin(line_energy))) # peak height
    fcn2.SetParameter(1, line_energy) # mean
    fcn2.SetParameter(2, 60.0) # sigma
    fcn2.SetLineColor(ROOT.kGreen+2)



    # draw before fit
    hist.SetAxisRange(400, 1400)
    hist.Draw()
    fcn.Draw("same")
    fcn2.Draw("same")
    canvas.Update()
    #if not ROOT.gROOT.IsBatch(): raw_input("any key to continue... ")

    print "--> fitting..."
    hist.Fit(fcn,"SRNI") # do the fit
    hist.Fit(fcn2,"SRNI") # do the fit

    # update title with fit results
    hist.SetTitle("%s: #bar{x}_{570} = %.2f #pm %.2f, #sigma_{570} = %.2f #pm %.2f, #sigma/#bar{x} = %.3f, #bar{x}_{1062} = %.2f #pm %.2f, #sigma_{1063} = %.2f #pm %.2f, #sigma/#bar{x} = %.3f" % (
        hist.GetName(),
        fcn.GetParameter(1),    # mean
        fcn.GetParError(1),     # mean error
        fcn.GetParameter(2),    # sigma
        fcn.GetParError(2),     # sigma error
        fcn.GetParameter(2)/fcn.GetParameter(1), # sigma/E
        fcn2.GetParameter(1),   # mean
        fcn2.GetParError(1),    # mean error
        fcn2.GetParameter(2),   # sigma
        fcn2.GetParError(2),    # sigma error
        fcn2.GetParameter(2)/fcn2.GetParameter(1), # sigma/E
    ))

    # draw after fit results
    hist.Draw()
    fcn.Draw("same")
    fcn2.Draw("same")
    canvas.Update()
    canvas.Print("fit_%s.pdf" % name)
    #if not ROOT.gROOT.IsBatch(): raw_input("any key to continue... ")

    hist.SetTitle("")
    hist.SetAxisRange(0, energy_max)
    return hist
           

if len(sys.argv) < 2:
    filename = "/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v4.root" 
else:
    filename = sys.argv[1]

print "---> processing", filename

basename = os.path.splitext(os.path.basename(filename))[0]
print basename

tfile = ROOT.TFile(filename)
tree = tfile.Get("tree")
n_entries = tree.GetEntries()
print "%i entries in tree" % n_entries

hists = []
hist_stack = ROOT.THStack("hist_stack","")

#-------------------------------------------------------------------------------
# current tests
#-------------------------------------------------------------------------------

#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(),"","5x_baseline_rms"))

#hists.append(get_hist(tree, "SignalEnergy","", "SignalEnergy"))

drift_cut = struck_analysis_cuts.get_drift_time_cut(drift_time_high=struck_analysis_parameters.max_drift_time)

# current best:
#hists.append(get_hist(tree, "SignalEnergy", struck_analysis_cuts.get_drift_time_selection(drift_time_high=struck_analysis_parameters.max_drift_time), "SignalEnergy_drift_sel"))

#hists.append(get_hist(tree, "SignalEnergy", drift_cut, "drift_cut"))
hist_stack.Add(get_hist(tree, "SignalEnergy", drift_cut, "drift_cut"))

#hists.append(get_hist(tree, "Sum$(bundle_energy)","", "bundle_energy")) # same as SignalEnergy

#hists.append(get_hist(tree, "Sum$(bundle_energy)","nbundlesX<2 && nbundlesY<2", "bundle_energy_1"))

#hists.append(get_hist(tree, "SignalEnergy", "nsignals==1 && %s" % drift_cut, "single_strip_drift_cut"))
hist_stack.Add(get_hist(tree, "SignalEnergy", "nsignals==1 && %s" % drift_cut, "single_strip_drift_cut"))

#hists.append(get_hist(tree, "SignalEnergy", "nbundlesX<2 && nbundlesY<2 && %s" % drift_cut, "1_x_or_y_drift_cut"))
hist_stack.Add(get_hist(tree, "SignalEnergy", "nbundlesX<2 && nbundlesY<2 && %s" % drift_cut, "1_x_or_y_drift_cut"))

#hists.append(get_hist(tree, "Sum$(bundle_energy)",
#    "nbundlesX<2 && nbundlesY<2 && %s" % struck_analysis_cuts.get_drift_time_selection(drift_time_high=struck_analysis_parameters.max_drift_time), 
#    "bundle_energy_1_dt_sel"))

#hists.append(get_hist(tree, "SignalEnergy", "(nbundlesX>1 || nbundlesY>1) && %s" % drift_cut, "up_to_1_x_or_y_drift_cut"))
hist_stack.Add(get_hist(tree, "SignalEnergy", "(nbundlesX>1 || nbundlesY>1) && %s" % drift_cut, "up_to_1_x_or_y_drift_cut"))

# doesn't work! too many operators:
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(),
#    "%s && %s" % (
#        struck_analysis_cuts.get_drift_time_selection(drift_time_high=struck_analysis_parameters.max_drift_time),
#        struck_analysis_cuts.get_drift_time_cut(drift_time_high=struck_analysis_parameters.max_drift_time),
#    ),
#    "5x_baseline_rms_dt_low_and_hi_cut_and_sel"))



#-------------------------------------------------------------------------------
# previous attempts
#-------------------------------------------------------------------------------

# constant threshold:
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd(),"","10-keV"))
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd(energy_threshold=20.0),"","20-keV"))

# channel-dependent threshold (uses rms_keV):
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_rms_keV(),"","5xRMS_keV"))
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_rms_keV(n_sigma=4.0),"","4xRMS_keV"))

# wfm-dependent threshold (uses baseline_rms):
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(n_sigma=1.0),"","1x_baseline_rms"))
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(n_sigma=2.0),"","2x_baseline_rms"))
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(n_sigma=3.0),"","3x_baseline_rms"))
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(n_sigma=4.0),"","4x_baseline_rms"))
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(),"","5x_baseline_rms"))
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_baseline_rms(n_sigma=6.0),"","6x_baseline_rms"))

# single-strip channels only
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_one_strip_channels(n_sigma=5.0),"","5x_baseline_rms_single_ch"))

# two-strip channels only
#hists.append(get_hist(tree, struck_analysis_cuts.get_few_two_strip_channels(n_sigma=5.0),"","5x_baseline_rms_single_ch"))

# chargeEnergy
#hists.append(get_hist(tree, "chargeEnergy","", "chargeEnergy"))

legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.9, 0.9, 0.99)
legend.SetNColumns(2)
# add entry to legend for each hist...
hist_list = hist_stack.GetHists() # a TList
for i in xrange(hist_list.GetEntries()):
    hist = hist_list.At(i) 
    hist.SetLineColor(struck_analysis_parameters.colors[i])
    hist.SetMarkerColor(struck_analysis_parameters.colors[i])
    entry = " ".join(hist.GetName().split("_"))
    legend.AddEntry(hist, "%s: %.3e" % (entry, hist.GetEntries()), "p")

# draw hists
hist_stack.Draw("nostack")
"""
hists[0].SetAxisRange(200, 1400.0)
y_max = hists[0].GetMaximum()
hists[0].SetAxisRange(0, 3000.0)
hists[0].Draw()
hists[0].SetMaximum(y_max*1.2)
for i, hist in enumerate(hists):
    hist.Draw("same")
    hist.SetLineColor(struck_analysis_parameters.colors[i])
    hist.SetMarkerColor(struck_analysis_parameters.colors[i])
    entry = " ".join(hist.GetName().split("_"))
    legend.AddEntry(hist, "%s: %.3e" % (entry, hist.GetEntries()), "p")
"""
legend.Draw()

#hists[0].SetAxisRange(0, 2000.0)
hist_stack.Draw("nostack")
hist_stack.GetXaxis().SetRange(50, 2000)
hist_stack.GetHistogram().SetAxisRange(50,2000)
canvas.Update()
canvas.Print("energies.pdf")

canvas.SetLogy(1)
canvas.Update()
canvas.Print("energies_log.pdf")
canvas.SetLogy(0)

#hists[0].SetAxisRange(400, 750.0)
hist_stack.Draw("nostack")
hist_stack.GetXaxis().SetRange(200, 1400)
hist_stack.GetHistogram().SetAxisRange(400,750)
canvas.Update()
canvas.Print("energies_zoom_peak.pdf")

canvas.SetLogy(1)
canvas.Update()
canvas.Print("energies_zoom_peak_log.pdf")
canvas.SetLogy(0)


#hists[0].SetAxisRange(200, 1400.0)
hist_stack.Draw("nostack")
hist_stack.GetXaxis().SetRange(200, 1400)
hist_stack.GetHistogram().SetAxisRange(200,1400)
canvas.Update()
canvas.Print("energies_zoom.pdf")
canvas.SetLogy(1)
canvas.Update()
canvas.Print("energies_zoom_log.pdf")

if not ROOT.gROOT.IsBatch(): raw_input("any key to continue... ")

