"""
19 slices takes 20 minutes
"""

import os
import sys
import json
import fit_peak
import commands
import struck_analysis_parameters

from ROOT import gROOT
from ROOT import TFile
from ROOT import TLegend
from ROOT import TH1D
from ROOT import TCanvas
gROOT.SetBatch(True)

def process_file(filename):

    # options 
    all_energy_var = "energy1_pz"
    max_drift_length = 19.0 # mm
    n_slices = 19
    single_strip_cut = struck_analysis_parameters.get_single_strip_cut(10.0)
    n_bins = 160
    min_bin = 0
    max_bin = 1600

    selections = []
    selections.append(single_strip_cut)

    print "---> processing", filename
    basename = os.path.splitext(os.path.basename(filename))[0]

    # cuts label prefix:
    #cuts_label = struck_analysis_parameters.get_cuts_label(all_energy_var, selection) 
    #cuts_label = "_".join(cuts_label.split("+"))
    #basename = cuts_label + "_" + basename

    basename = "z_slices_" + basename
    all_results = {}

    drift_velocity = struck_analysis_parameters.drift_velocity
    dt = max_drift_length/drift_velocity/n_slices # microsecond
    print "dt [microsecond]: %.3f" % dt

    root_file = TFile(filename)
    tree = root_file.Get("tree")
    try:
        n_entries = tree.GetEntries()
        print "%i entries" % n_entries
    except AttributeError:
        print "could not get entries from tree"

    legend = TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetNColumns(5)

    hists = []

    hist = TH1D("hist_all", "",n_bins,min_bin,max_bin)
    tree.Draw("%s >> %s" % (all_energy_var, hist.GetName()),"","goff")
    hists.append(hist)
    legend.AddEntry(hist,"all","l")

    hist = TH1D("hist_ss", "",n_bins,min_bin,max_bin)
    tree.Draw("%s >> %s" % (all_energy_var, hist.GetName()),single_strip_cut,"goff")
    hists.append(hist)
    legend.AddEntry(hist,"single-strip","l")

    t = 0.0
    i = 0
    while t < max_drift_length/drift_velocity: # microseconds
        
        print "---> %i: t=%.1f microseconds" % (i,t)
        drift_time_cut = "(rise_time_stop95-trigger_time>%s)&&(rise_time_stop95-trigger_time<%s)" % (t, t+dt)
        selection = " && ".join(selections + [drift_time_cut])
        print selection

        print "\t drift_time_cut", drift_time_cut

        result = fit_peak.fit_channel(
            tree=tree, 
            channel=None, 
            basename=basename, 
            do_1064_fit=False, 
            all_energy_var=all_energy_var, 
            selection=selection,
            do_use_step=True,    
            min_bin=200,
            max_bin=1000,
            fit_half_width = 300,
            do_use_exp=True,
        )
        result["dt"] = dt
        all_results[t] = result

        hist = TH1D("hist_%i_to_%i" % (t*1e3, (t+dt)*1e3), "",n_bins,min_bin,max_bin)
        hists.append(hist)
        tree.Draw("%s >> %s" % (all_energy_var, hist.GetName()),selection,"goff")
        legend.AddEntry(hist,"%.1f to %.1f #mus" % (t, t+dt),"l")
        print "%i entries in %s" % (hist.GetEntries(), hist.GetName())
        plot_name = "fit_all_%s_lin.pdf" % basename
        new_plot_name = "z_slice_fit_%i_to_%i.pdf" % (t*1e3, (t+dt)*1e3)
        cmd = "mv -f %s %s" % (plot_name, new_plot_name)
        output = commands.getstatusoutput(cmd)
        if output[0] != 0:
            print output[1]

        t += dt
        i += 1

    # write results to file
    result_file = file("fit_results_%s_%i.txt" % (basename,i), 'w')
    json.dump(all_results, result_file, indent=4, sort_keys=True)

    c1 = TCanvas("c1","")
    c1.SetGrid(1,1)
    c1.SetLogy(1)
    bin_max = hists[0].GetBinContent(hists[0].FindBin(50))
    hists[0].SetMaximum(bin_max*1.5)
    hists[0].SetMinimum(0.5)
    for i,hist in enumerate(hists):
        hist.SetLineWidth(2)
        if i == 0:
            hist.Draw()
            hist.SetXTitle("Energy [keV]")
            hist.SetYTitle("Counts / %.1f keV" % hist.GetBinWidth(1))
            hist.SetLineColor(1)
        else:
            colors = struck_analysis_parameters.get_colors()
            i_color = colors[(i-1) % len(colors)]
            hist.SetLineColor(i_color)
            i_style = (i-1) / len(colors) + 1
            print "i_style", i_style
            hist.SetLineStyle(i_style)
            hist.Draw("same")

    legend.Draw()
    c1.Update()
    c1.Print("z_slices_%i.pdf" % (len(hists)-2))

    if not gROOT.IsBatch():
        raw_input("enter to continue ")


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        sys.exit(1)

    process_file(sys.argv[1])


