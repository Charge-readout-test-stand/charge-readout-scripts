"""
compare early and late times from 9th LXe
"""

import os
import sys
import ROOT
ROOT.gROOT.SetBatch(True)

from struck import struck_analysis_cuts
from struck import struck_analysis_parameters

# options
current_var = "maxCurrent4"
draw_cmd = "%s/SignalEnergy" % current_var # the usual

drift_time_high = struck_analysis_parameters.max_drift_time
drift_time_low = struck_analysis_parameters.drift_time_threshold
#drift_time_high = 8.0
#drift_time_low = 8.0
#drift_time_high = 8.5
#drift_time_high = 9.0
nsignals = 2
nstrips = 1 # use 1-strip channels or 2-strip channels
# the usual:
selection = []
selection.append("signal_map[16]==0") # exclude noisy X1-12

strips_excluded = []
# exclude channels w multiple strips
for channel, val in struck_analysis_parameters.struck_to_mc_channel_map.items():
    #print channel, val
    if len(val) != nstrips:
        strips_excluded.append("signal_map[%i]" % channel)
        print "\t ch %i excluded" % channel
strips_excluded = "+".join(strips_excluded)
strips_excluded = "(%s==0)" % strips_excluded
print "strips_excluded:", strips_excluded
selection.append(strips_excluded)

# the usual:
selection.append("nsignals==%i" % nsignals)
selection.append("rise_time_stop95_sum-trigger_time>%s" % drift_time_low)
selection.append("rise_time_stop95_sum-trigger_time<%s" % drift_time_high)

# other stuff
#selection.append("(nbundlesX>1||nbundlesY>1)") # distinct x or y bundles; prob.  compton scatter?
selection.append("(nXsignals==1||nYsignals==1)") # distinct x or y bundles; prob.  compton scatter?


selection.append("!is_pulser")
selection.append("!is_bad")
selection = " && ".join(selection)


# hist options
min_bin = 0.0
max_bin = 10.0
#bin_width = 0.1 # keV
#n_bins = int((max_bin - min_bin)/bin_width)
n_bins = 100


if len(sys.argv) < 2:
    print "provide tier3 files as arguments"
    sys.exit(1)

struck_filenames = sys.argv[1:]

canvas = ROOT.TCanvas("canvas","")
canvas.SetLeftMargin(0.12)
canvas.SetGrid(1,1)
canvas.SetLogy(1)

basename = os.path.commonprefix(struck_filenames)
basename = os.path.splitext(os.path.basename(basename))[0]
print "basename:", basename

#print "--> Struck file:", struck_filename
#struck_file = ROOT.TFile(struck_filename)
#struck_tree = struck_file.Get("tree")

struck_tree = ROOT.TChain("tree")
for filename in struck_filenames:
    struck_tree.Add(filename)

print "%i entries in tree" % struck_tree.GetEntries()

struck_tree.SetBranchStatus("*",0) # first turn off all branches
struck_tree.SetBranchStatus("SignalEnergy",1) 
struck_tree.SetBranchStatus("nsignals",1) 
struck_tree.SetBranchStatus("signal_map",1) 
struck_tree.SetBranchStatus("rise_time_stop95_sum",1) 
struck_tree.SetBranchStatus("trigger_time",1) 
struck_tree.SetBranchStatus("is_pulser",1) 
struck_tree.SetBranchStatus("is_bad",1) 
struck_tree.SetBranchStatus("nbundlesX",1) 
struck_tree.SetBranchStatus("nbundlesY",1) 
struck_tree.SetBranchStatus("nXsignals",1) 
struck_tree.SetBranchStatus("nYsignals",1) 
struck_tree.SetBranchStatus(current_var,1) 

print "\t %i Struck entries" % struck_tree.GetEntries()
struck_hist = ROOT.TH1D("struck_hist","", n_bins, min_bin, max_bin)
struck_hist.SetXTitle("%s" % draw_cmd)
#struck_hist.SetXTitle("%s [keV]" % draw_cmd)
#struck_hist.SetYTitle("Counts / %.1f keV" % struck_hist.GetBinWidth(1))
struck_hist.GetYaxis().SetTitleOffset(1.5)
struck_hist.SetLineColor(ROOT.kBlue)
struck_hist.SetFillColor(ROOT.kBlue)
struck_hist.SetFillStyle(3004)
struck_hist.SetMarkerColor(ROOT.kBlue)
struck_hist.SetMarkerStyle(21)
struck_hist.SetMarkerSize(1.5)
struck_hist.SetLineWidth(2)

struck_hist2 = ROOT.TH2D("hist2d","",n_bins, 200, 1400, n_bins, min_bin, 1.0)
struck_hist2.SetXTitle("SignalEnergy")
struck_hist2.SetYTitle(draw_cmd)
struck_hist2.SetTitle(selection)

struck_selection = selection

legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
legend.SetNColumns(2)
legend.SetFillStyle(0)
legend.SetFillColor(0)

struck_hist2.GetDirectory().cd()
print "selection:", selection
struck_tree.Draw("%s:SignalEnergy >> %s" % (draw_cmd, struck_hist2.GetName()),selection)
print "\t %i entries in hist" % struck_hist2.GetEntries()

struck_hist.GetDirectory().cd()
print "draw_cmd:", draw_cmd
print "selection:", selection
struck_tree.Draw("%s >> %s" % (draw_cmd, struck_hist.GetName()),selection)
print "\t %i entries in hist" % struck_hist.GetEntries()

start_bin = struck_hist.FindBin(300.0)
stop_bin = struck_hist.FindBin(1400.0)

struck_hist.SetMaximum() # reset since we keep filling the same hist... 
y_max = struck_hist.GetMaximum()
if struck_hist2.GetMaximum() > y_max: y_max = struck_hist2.GetMaximum()
struck_hist.SetMaximum(y_max*1.1)

struck_hist.Draw()
#struck_hist.Draw("same")
#legend.Draw()
canvas.Update()
plotname = "%s_%istrips_1X1Y__%isignals_%i_to_%i" % (
    current_var, nstrips, nsignals, drift_time_low*1e3, drift_time_high*1e3)
canvas.Print("%s_%s.pdf" % (plotname, basename))

canvas.SetLogy(0)
canvas.SetLogz(1)
struck_hist2.Draw("colz")
canvas.Update()
canvas.Print("%s_2d_%s.pdf" % (plotname, basename))

pavetext = ROOT.TPaveText(0.12, 0.8, 0.9, 0.9, "ndc")
pavetext.AddText(struck_selection[:200])
#pavetext.AddText("\nstruck 2 amplitude x %.2f" % (scale_factor, ))
pavetext.SetBorderSize(0)
pavetext.SetFillStyle(0)
pavetext.Draw()

if not ROOT.gROOT.IsBatch():
    raw_input("any key to continue... ")

