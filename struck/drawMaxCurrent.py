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

low_cut = 0.65
high_cut = 0.8

drift_time_high = struck_analysis_parameters.max_drift_time
drift_time_low = struck_analysis_parameters.drift_time_threshold
#drift_time_high = 8.0
#drift_time_low = 8.0
#drift_time_high = 8.5
#drift_time_high = 9.0
nsignals = 1
nstrips = 1 # use 1-strip channels or 2-strip channels
# the usual:
selection = []
selection.append("SignalEnergy>200")
#selection.append("signal_map[16]==0") # exclude noisy X1-12

# some interesting channels:
#selection.append("signal_map[7]") # Y17
#selection.append("signal_map[21]") # X17
#selection.append("signal_map[25]") # X21
#selection.append("signal_map[19]") # X15
#selection.append("signal_map[17]") # X13

if nstrips != 0:
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
if nsignals!=0: selection.append("nsignals==%i" % nsignals)
#selection.append("rise_time_stop95_sum-trigger_time>%s" % drift_time_low)
#selection.append("rise_time_stop95_sum-trigger_time<%s" % drift_time_high)

# other stuff
#selection.append("(nbundlesX>1||nbundlesY>1)") # distinct x or y bundles; prob.  compton scatter?
#selection.append("(nXsignals==1||nYsignals==1)")
#selection.append("(nXsignals==2||nYsignals==2)") 

selection.append("!is_pulser")
selection.append("!is_bad")
selection = " && ".join(selection)


# hist options
min_bin = 0.0
max_bin = 1.0
#bin_width = 0.1 # keV
#n_bins = int((max_bin - min_bin)/bin_width)
n_bins = 100
minE = 200
maxE = 1400


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
struck_hist = ROOT.TH1D("struck_hist","", n_bins, min_bin, max_bin*1.5)
struck_hist.SetXTitle("%s" % draw_cmd)
#struck_hist.SetXTitle("%s [keV]" % draw_cmd)
#struck_hist.SetYTitle("Counts / %.1f keV" % struck_hist.GetBinWidth(1))
struck_hist.GetYaxis().SetTitleOffset(1.5)
struck_hist.SetLineColor(ROOT.kBlue)
struck_hist.SetFillColor(ROOT.kBlue)
struck_hist.SetFillStyle(3004)
struck_hist.SetLineWidth(2)
struck_hist.SetMarkerColor(ROOT.kBlue)


energy_hist = ROOT.TH1D("energy_hist","", n_bins, minE, maxE)
energy_hist.SetLineWidth(2)
energy_hist.SetLineColor(ROOT.kBlue)
energy_hist.SetFillColor(ROOT.kBlue)
energy_hist.SetFillStyle(3004)
energy_hist.SetXTitle("SignalEnergy [keV]")

energy_hist2 = energy_hist.Clone("energy_hist2")
energy_hist2.SetLineColor(ROOT.kRed)
energy_hist2.SetFillColor(ROOT.kRed)

energy_hist3 = energy_hist.Clone("energy_hist3")
energy_hist3.SetLineColor(ROOT.kGreen+2)
energy_hist3.SetFillColor(ROOT.kGreen+2)

struck_hist2 = ROOT.TH2D("hist2d","",n_bins, minE, maxE, n_bins, min_bin, max_bin)
struck_hist2.SetXTitle("SignalEnergy")
struck_hist2.SetYTitle(draw_cmd)
struck_hist2.SetTitle(selection)


struck_hist2.GetDirectory().cd()
print "selection:", selection
struck_tree.Draw("%s:SignalEnergy >> %s" % (draw_cmd, struck_hist2.GetName()),selection)
print "\t %i entries in hist" % struck_hist2.GetEntries()

struck_hist.GetDirectory().cd()
print "draw_cmd:", draw_cmd
print "selection:", selection
struck_tree.Draw("%s >> %s" % (draw_cmd, struck_hist.GetName()),
    "SignalEnergy>%.1f && %s" % (minE, selection))
print "\t %i entries in hist" % struck_hist.GetEntries()


energy_hist.GetDirectory().cd()
struck_tree.Draw("SignalEnergy >> %s" % energy_hist.GetName(),selection)
energy_hist2.GetDirectory().cd()
struck_tree.Draw("SignalEnergy >> %s" % energy_hist2.GetName(),
  "%s && %s/SignalEnergy>%.2f" % (selection, current_var, low_cut))
energy_hist3.GetDirectory().cd()
struck_tree.Draw("SignalEnergy >> %s" % energy_hist3.GetName(),
  "%s && %s/SignalEnergy<%.2f" % (selection, current_var, high_cut))

legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
legend.SetNColumns(3)
legend.AddEntry(energy_hist, "no A/E cut","f")
legend.AddEntry(energy_hist2, "A/E>%.2f" % low_cut,"f")
legend.AddEntry(energy_hist3, "A/E<%.2f" % high_cut,"f")

struck_hist.Draw()
canvas.Update()
plotname = "%s_%istrips_%isignals_%i_to_%i" % (
    current_var, nstrips, nsignals, drift_time_low*1e3, drift_time_high*1e3)
canvas.Print("%s_%s.pdf" % (plotname, basename))

canvas.SetLogy(0)
canvas.SetLogz(1)
struck_hist2.Draw("colz")
canvas.Update()
canvas.Print("%s_2d_%s.pdf" % (plotname, basename))

#canvas.SetLogy(1)
energy_hist.Draw()
energy_hist2.Draw("same")
energy_hist3.Draw("same")
legend.Draw()
canvas.Print("%s_energy_%s.pdf" % (plotname, basename))

if not ROOT.gROOT.IsBatch():
    raw_input("any key to continue... ")

