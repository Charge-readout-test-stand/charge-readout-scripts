"""
A quick and dirty spectrum from NGM files
"""
import os
import sys
import ROOT
from struck import struck_analysis_parameters
ROOT.gROOT.SetBatch(True)



filenames = sys.argv[1:]
tree = ROOT.TChain("HitTree")
for filename in filenames:
    print "--> adding %s to chain" % filename
    tree.Add(filename)
#tree.Show(0,32) # debugging
n_entries = tree.GetEntries()

# options:
n_points = 10 # for wfm average
#max_entry = int(0.01*n_entries)
max_entry = n_entries # don't skip any events


legend = ROOT.TLegend(0.12, 0.86, 0.9, 0.99)
legend.SetNColumns(7)

print "%i entries in tree" % n_entries
print "considering %i entries, %.1f" % (max_entry, 100.0*max_entry/n_entries) + "%"

hists = []
mean_max = 0.0 # keep track of maximum mean
y_max = 0
#for channel in xrange(5): # debugging
for channel in xrange(32):
    print "---> channel %i" % channel

    calibration = struck_analysis_parameters.calibration_values[channel]
    color = struck_analysis_parameters.get_colors()[channel]
    label = struck_analysis_parameters.channel_map[channel]

    hist = ROOT.TH1D("hist%i" % channel, "",120,0,1800)
    hist.SetLineColor(color)
    hist.SetLineWidth(2)
    hist.SetMarkerColor(color)
    hist.SetMarkerStyle(21)
    hist.SetMarkerSize(1.2)
    hist.SetXTitle("Energy [keV]")
    hist.SetYTitle("Counts / %.1f keV" % hist.GetBinWidth(1))
    hist.GetYaxis().SetTitleOffset(1.5)
    #hist.SetFillColor(color)
    #hist.SetFillStyle(3004)

    selection = "_slot==%i && _channel==%i" % (channel/16, channel%16)
    if max_entry < n_entries: selection = ("Entry$<%i && " % max_entry) + selection

    # calculate a quick energy approximation
    draw_cmd = []
    for i_point in xrange(n_points):
        draw_cmd.append("_waveform[%i] - _waveform[%i]" % (799-i_point, i_point))
    draw_cmd = "+".join(draw_cmd)
    draw_cmd = "(%s)*%.5f" % (draw_cmd, calibration/n_points)

    #print "\t draw_cmd:", draw_cmd
    print "\t selection:", selection

    n_drawn = tree.Draw("%s >> %s" % (draw_cmd, hist.GetName()), selection, "goff")
    print "\t %i-point average | %i drawn | %i in hist | %i expected" % (n_points, n_drawn, hist.GetEntries(), n_entries/32)

    if hist.GetMean() > mean_max: mean_max = hist.GetMean()
    if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()

    legend.AddEntry(hist, "%s %.1f" % (label, hist.GetMean()), "p")
    hists.append(hist)

canvas = ROOT.TCanvas()
canvas.SetTopMargin(0.15)
canvas.SetLeftMargin(0.12)
canvas.SetGrid()

hists[0].SetMaximum(y_max*1.12)
#hists[0].SetAxisRange(0, mean_max*8.0)
hists[0].Draw()
for hist in hists:
    hist.Draw("same")

legend.Draw()
canvas.Update()
basename = os.path.basename(filename)
basename = os.path.splitext(basename)[0]
print "basename", basename
canvas.Print("lin_spectrum_%s.pdf" % basename)
canvas.SetLogy(1)
canvas.Update()
canvas.Print("log_spectrum_%s.pdf" % basename)

if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue")



