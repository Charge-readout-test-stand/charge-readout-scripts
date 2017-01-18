"""

copied from compareMCtoData_noise_branch.py

"""

import os
import sys
import ROOT
ROOT.gROOT.SetBatch(True)

from struck import struck_analysis_cuts
from struck import struck_analysis_parameters

# options
#draw_cmd = "baseline_rms"
#draw_cmd = "energy_rms1"
draw_cmd = "energy1"
selection = "is_pulser"


# hist options
min_bin = 0.0
max_bin = 30.0
n_bins = 200

if draw_cmd == "energy1":
    min_bin = -30.0
    max_bin = 30.0


if len(sys.argv) < 3:
    print "provide tier3 files as arguments: struck file 1 , struck file 2"
    sys.exit(1)

ninth_filename = sys.argv[1]
tenth_filename = sys.argv[2]

canvas = ROOT.TCanvas("canvas","")
canvas.SetLeftMargin(0.12)
canvas.SetGrid(1,1)

ninth_basename = os.path.splitext(os.path.basename(ninth_filename))[0]
tenth_basename = os.path.splitext(os.path.basename(tenth_filename))[0]
basename = "%s_%s" % (ninth_basename, tenth_basename)

print "--> 9th LXe:", ninth_filename
ninth_file = ROOT.TFile(ninth_filename)
ninth_tree = ninth_file.Get("tree")
print "\t %i entries" % ninth_tree.GetEntries()
ninth_hist = ROOT.TH1D("ninth_hist","", n_bins, min_bin, max_bin)
ninth_hist.SetLineColor(ROOT.kRed)
ninth_hist.SetFillColor(ROOT.kRed)
ninth_hist.SetFillStyle(3004)
ninth_hist.SetMarkerColor(ROOT.kRed)
ninth_hist.SetMarkerStyle(21)
ninth_hist.SetMarkerSize(1.5)
ninth_hist.SetLineWidth(2)


print "--> 10th LXe:", tenth_filename
tenth_file = ROOT.TFile(tenth_filename)
tenth_tree = tenth_file.Get("tree")
print "\t %i Struck entries" % tenth_tree.GetEntries()
tenth_hist = ROOT.TH1D("tenth_hist","", n_bins, min_bin, max_bin)
tenth_hist.SetXTitle("%s" % draw_cmd)
tenth_hist.SetYTitle("Counts / %.1f" % tenth_hist.GetBinWidth(1))
tenth_hist.GetYaxis().SetTitleOffset(1.5)
tenth_hist.SetLineColor(ROOT.kBlue)
tenth_hist.SetFillColor(ROOT.kBlue)
tenth_hist.SetFillStyle(3004)
tenth_hist.SetMarkerColor(ROOT.kBlue)
tenth_hist.SetMarkerStyle(21)
tenth_hist.SetMarkerSize(1.5)
tenth_hist.SetLineWidth(2)

for tree in [tenth_tree, ninth_tree]:
    tree.SetBranchStatus("*",0) # first turn off all branches
    tree.SetBranchStatus("is_pulser",1) 
    tree.SetBranchStatus(draw_cmd,1) 


# map 10th LXe channels to 9th LXe channels
channel_map_10th_to_9th = {}
channel_map_10th_to_9th[8] = 4 # Y14
channel_map_10th_to_9th[7] = 5
channel_map_10th_to_9th[6] = 6
channel_map_10th_to_9th[5] = 7
channel_map_10th_to_9th[4] = 8
channel_map_10th_to_9th[3] = 9
channel_map_10th_to_9th[2] = 10 # Y20

channel_map_10th_to_9th[15] = 18 # X14
channel_map_10th_to_9th[14] = 19
channel_map_10th_to_9th[13] = 20
channel_map_10th_to_9th[12] = 21
channel_map_10th_to_9th[11] = 22
channel_map_10th_to_9th[10] = 23
channel_map_10th_to_9th[9] = 24 # X20


for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
    if val == 0: continue

    legend = ROOT.TLegend(canvas.GetLeftMargin(), 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)

    label = struck_analysis_parameters.channel_map[channel]

    legend.AddEntry(ninth_hist,"9th LXe %s = ch %i" % (label, channel_map_10th_to_9th[channel]), "f")
    legend.AddEntry(tenth_hist,"10th LXe %s = ch %i" % (label, channel), "f")

    ninth_hist.GetDirectory().cd()
    ninth_draw_cmd = "%s[%i]" % (draw_cmd, channel_map_10th_to_9th[channel])
    print "ninth_draw_cmd:", ninth_draw_cmd
    print "ninth_selection:", selection
    ninth_tree.Draw("%s >> %s" % (ninth_draw_cmd, ninth_hist.GetName()),selection)
    print "\t %i entries in hist" % ninth_hist.GetEntries()

    tenth_hist.GetDirectory().cd()
    tenth_draw_cmd = "%s[%i]" % (draw_cmd, channel)
    print "draw_cmd:", tenth_draw_cmd
    print "selection:", selection
    tenth_tree.Draw("%s >> %s" % (tenth_draw_cmd, tenth_hist.GetName()),selection)
    print "\t %i entries in hist" % tenth_hist.GetEntries()

    # this doesn't work well for low stats:
    #if draw_cmd != "energy1_pz":
    if True:
        tenth_hist.SetMaximum() # reset since we keep filling the same hist... 
        y_max = tenth_hist.GetMaximum()
        if ninth_hist.GetMaximum() > y_max: y_max = ninth_hist.GetMaximum()
        tenth_hist.SetMaximum(y_max*1.1)

    tenth_hist.Draw()
    ninth_hist.Draw("hist same")
    tenth_hist.Draw("same")
    legend.Draw()
    canvas.Update()
    plotname = "comparison_%s" % draw_cmd

    plotname += "_%s" % label

    canvas.Print("%s_%s.pdf" % (plotname, basename))

    if not ROOT.gROOT.IsBatch():
        val = raw_input("any key to continue... ")
        if val == 'q': sys.exit()


