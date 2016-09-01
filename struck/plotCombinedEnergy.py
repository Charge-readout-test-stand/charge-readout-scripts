
import os
import sys
import ROOT

import struck_analysis_cuts
import struck_analysis_parameters

def get_hist(tree, draw_cmd, selection, name="hist"):
     

    # options
    energy_max = 3000.0
    n_bins = int(energy_max/2.0)
    hist = ROOT.TH1D(name, "", n_bins, 0, energy_max)
    hist.GetDirectory().cd()
    hist.SetLineWidth(2)
    hist.SetXTitle("Energy [keV]")
    hist.SetYTitle("Counts / %s keV" % (energy_max/n_bins))
    hist.GetYaxis().SetTitleOffset(1.35)

    print "--> making hist", name
    print "\t draw_cmd:", draw_cmd
    print "\t selection:", selection
    n_drawn = tree.Draw("%s >> %s" % (draw_cmd, hist.GetName()), selection, "goff")
    print "\t %i drawn | %i in hist" % (n_drawn, hist.GetEntries())
    return hist
           

filename = sys.argv[1]

print "---> processing", filename

basename = os.path.splitext(os.path.basename(filename))[0]
print basename

tfile = ROOT.TFile(filename)
tree = tfile.Get("tree")
n_entries = tree.GetEntries()
print "%i entries in tree" % n_entries

hists = []


# constant threshold:
hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd(),"","10-keV"))
hists.append(get_hist(tree,
struck_analysis_cuts.get_few_channels_cmd(energy_threshold=20.0),"","20-keV"))

# channel-dependent threshold (uses rms_keV):
hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_rms_keV(),"","5xRMS_keV"))
hists.append(get_hist(tree, struck_analysis_cuts.get_few_channels_cmd_rms_keV(n_sigma=4.0),"","4xRMS_keV"))

# wfm-dependent threshold (uses baseline_rms):
hists.append(get_hist(tree,
    struck_analysis_cuts.get_few_channels_cmd_baseline_rms(),"","5x_baseline_rms"))
hists.append(get_hist(tree,
    struck_analysis_cuts.get_few_channels_cmd_baseline_rms(n_sigma=4.0),"","4x_baseline_rms"))

hists.append(get_hist(tree, "chargeEnergy","", "chargeEnergy"))

canvas = ROOT.TCanvas()
canvas.SetGrid()

legend = ROOT.TLegend(0.1, 0.9, 0.9, 0.99)
legend.SetNColumns(2)

# draw hists
hists[0].SetAxisRange(200, 1400.0)
y_max = hists[0].GetMaximum()
hists[0].SetAxisRange(0, 3000.0)
hists[0].Draw()
hists[0].SetMaximum(y_max*1.2)
for i, hist in enumerate(hists):
    hist.Draw("same")
    hist.SetLineColor(struck_analysis_parameters.colors[i])
    hist.SetMarkerStyle(21)
    hist.SetMarkerSize(0.9)
    hist.SetMarkerColor(struck_analysis_parameters.colors[i])
    legend.AddEntry(hist, hist.GetName(), "p")

legend.Draw()
canvas.Update()
canvas.Print("energies.pdf")

hists[0].SetAxisRange(0, 1400.0)
canvas.Update()
canvas.Print("energies_zoom.pdf")
raw_input("any key to continue... ")

