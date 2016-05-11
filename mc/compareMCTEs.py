
"""
Compare TE distributions in different MC files
"""

import os
import sys
import glob

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TChain
from ROOT import TCanvas
from ROOT import TLegend
from ROOT import TH1D
from ROOT import TLine
from ROOT import TH2D
from ROOT import TColor

from struck import struck_analysis_parameters


def draw_hists(canvas,legend,hists, plot_name=None):

    #prefix = "windowed"
    #prefix = "not_windowed"
    prefix = "gamma_and_e"

    print "--> drawing %i hists" % len(hists)

    legend = TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetFillColor(0)

    basename = hists[0].GetTitle()
    print basename
    hists[0].SetTitle("") # set to empty for plotting
    hists[0].Draw()
    hists[0].SetXTitle("NumTE")
    y_max = 0
    ref_mean = None
    for i_hist, hist in enumerate(hists):
        if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()
        hist.Draw("same")
        title = hist.GetTitle()
        if i_hist == 0: title = basename
        if ref_mean == None:
            ref_mean = hist.GetMean()
        print title, "B-scale:", hist.GetMean()/ref_mean
        legend_entry = "%s: mean=%.2e" % (title, hist.GetMean())
        legend.AddEntry(hist, legend_entry,"lf")
    hists[0].SetMaximum(y_max*1.1)
    legend.Draw()
    canvas.Update()
    if plot_name is None: plot_name = hists[0].GetName()
    canvas.Print("%s_%s.pdf" % (prefix, plot_name))
    hists[0].SetTitle(basename) # reset after plotting

    if not gROOT.IsBatch():
        raw_input("press enter to continue... ")

def get_hist(
    tree, 
    draw_command, 
    name, color, fill_style,
    n_bins=100, min_bin=0, max_bin=50000,
    gr_zero=True, # only use event > 0
    selection=None
):

    print "--> filling hist"
    hist = TH1D(name,"",n_bins, min_bin, max_bin)
    hist.SetLineColor(color)
    hist.SetFillColor(color)
    hist.SetFillStyle(fill_style)
    if selection is None:
        selection = ""
        if gr_zero:
            selection = "%s>0" % draw_command
    print "\t", draw_command, selection
    print "\t %i entries drawn" % tree.Draw(
        "%s >> %s" % (draw_command, hist.GetName()), 
        selection,
        "goff" # graphics off during this operation
    )
    print "\t %i entries in hist %s: %s" % (hist.GetEntries(), hist.GetName(),
        hist.GetTitle())
    return hist

def draw_plots(directories):

    Wvalue = struck_analysis_parameters.Wvalue
    #colors = struck_analysis_parameters.get_colors()
    colors = [TColor.kRed, TColor.kBlue]
    eDiff=300 # keV

    print "%i directories" % len(directories)

    te_energy_hists = []

    legend = TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetFillColor(0)

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)

    for directory in directories:

        #file_names = "%s/tier3_*.root" % directory
        file_name = directory
        print "--> processing %s:" % file_name

        basename = os.path.basename(file_name)
        basename = os.path.splitext(basename)[0]
        print "basename:", basename

        i_hist = len(te_energy_hists)
        color = colors[i_hist]
        fill_style = 3004 + i_hist

        tree = TChain("nEXOevents")
        print "%i files added" % tree.Add(file_name)

        hist = get_hist(tree,"NumTE", "TE%i" % i_hist, color, fill_style)
        hist.SetTitle(basename)
        te_energy_hists.append(hist)
        #legend.AddEntry(hist, basename, "lf") # one legend is sufficient for all plots


        # end loop over directories

      
        
    canvas.SetLogy(1)

    draw_hists(canvas,legend, te_energy_hists)
        
        
if __name__ == "__main__":


    if len(sys.argv) < 2:
        print "arguments: MC tier 3 to compare"
        sys.exit()

    draw_plots(sys.argv[1:])
    

