"""
Script to plot single PE spectra from PMT

19 July 2016
"""

import os
import sys
import ROOT

filenames = sys.argv[1:]

# defeat python/root garbage collection:
hists = []
root_files = []

# loop over files, fill hists with wfm max:
for i_file, filename in enumerate(filenames):
    print "---> processing file %i of %i: %s" % (i_file+1, len(filenames), filename)
    
    channel = 0

    root_file = ROOT.TFile(filename)
    root_files.append(root_file)

    tree = root_file.Get("tree%i" % channel)
    n_entries = tree.GetEntries()
    print "\t %i entries in tree" % n_entries

    basename = os.path.splitext(os.path.basename(filename))[0]
    hist = ROOT.TH1D("hist%i" % i_file, basename, pow(2,14), 0, pow(2,14))
    hist.Rebin(pow(2,6))
    print "\t n bins:", hist.GetNbinsX()
    hist.SetXTitle("Wfm height [ADC units]")
    hist.SetYTitle("Counts / %.1f ADC units" % hist.GetBinWidth(1))

    
    # construct a string to average the baseline over many samples
    n_samples = 10
    baseline_average = []
    for i_sample in xrange(n_samples):
        baseline_average.append("wfm[%i]/%.1f" % (i_sample, n_samples))
    baseline_average = " + ".join(baseline_average)
    baseline_average = "(%s)" % baseline_average
    #print baseline_average # testing

    # draw the wfm max minus baseline_average
    draw_cmd = "Max$(wfm)-%s >> %s" % (baseline_average, hist.GetName())
    #print draw_cmd # testing

    n_drawn = tree.Draw(draw_cmd, "", "goff")
    print "\t %i entries drawn to %s" % (n_drawn, hist.GetName())
    print "\t %i entries in %s" % (hist.GetEntries(), hist.GetName())
    hists.append(hist)

    # end loop over files


legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
legend.SetNColumns(2)
canvas = ROOT.TCanvas("canvas","")
print "--> drawing hists..."
# loop over hists and draw
for i_hist, hist in enumerate(hists):
    legend.AddEntry(hist, hist.GetTitle(),"f")
    n_entries = hist.GetEntries()
    hist.Scale(1.0/n_entries) # normalize to 1
    print "\t %s | %s: %i entries" % (hist.GetName(), hist.GetTitle(), hist.GetEntries())
    if i_hist == 0:
        hist.SetTitle("")
        hist.Draw()
    hist.Draw("same")
    hist.SetLineColor(i_hist+1)
    hist.SetFillColor(i_hist+1)
    hist.SetFillStyle(3004)
    hist.SetLineWidth(2)
    

legend.Draw()
canvas.SetLogy(1)
canvas.SetGrid()
canvas.Update()
canvas.Print("pmt_comparison.pdf")
raw_input("any key to continue... ") # pause
    




