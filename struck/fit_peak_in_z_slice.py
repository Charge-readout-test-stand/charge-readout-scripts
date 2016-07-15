"""
19 slices takes 20 minutes
"""

from ROOT import gROOT
#gROOT.SetBatch(True)

import os
import sys
import json
import fit_peak
import commands
import struck_analysis_parameters
import struck_analysis_cuts

from ROOT import TFile
from ROOT import TLegend
from ROOT import TH1D
from ROOT import TCanvas

def process_file(filename):

    # options 
    do_fit = True # whether to do fits of z slices
    max_drift_length = 18.0 # for Liang
    n_slices = 9 # for Liang
    all_energy_var = "chargeEnergy*%s" % struck_analysis_parameters.struck_energy_multiplier # for Liang
    #all_energy_var = "energy1_pz"
    #max_drift_length = 19.0 # mm
    #n_slices = 19 # 1-mm slices
    #n_slices = 8 # ~2-mm slices
    #n_slices = 3 # 3 detector regions
    #n_slices = 4 # 3 detector regions
    single_strip_cut = struck_analysis_cuts.get_single_strip_cut(10.0)
    n_bins = 160
    min_bin = 0
    max_bin = 1600
    fit_half_width=200
    #fit_half_width=170

    selections = []
    #selections.append(single_strip_cut) # ignore for Liang's plot
    #selections.append("channel<8") # ignore for Liang's plot

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
    out_file = TFile("%s_%i.root" % (basename, n_slices), "recreate")

    hist = TH1D("hist_all", "",n_bins,min_bin,max_bin)
    tree.Draw("%s >> %s" % (all_energy_var, hist.GetName()),"","goff")
    print "%i entries in hist %s" % (hist.GetEntries(), hist.GetName())
    hists.append(hist)
    legend.AddEntry(hist,"all","l")

    hist = TH1D("hist_ss", "",n_bins,min_bin,max_bin)
    tree.Draw("%s >> %s" % (all_energy_var, hist.GetName()),single_strip_cut,"goff")
    print "%i entries in hist %s" % (hist.GetEntries(), hist.GetName())
    hists.append(hist)
    legend.AddEntry(hist,"single-strip","l")

    t = 8.0
    i = 0
    if n_slices == 4:
        legend.SetNColumns(3)
    while t < max_drift_length/drift_velocity: # microseconds

        # special handling for 3 slices: close to anode, flat region, cathode
        if n_slices == 3:
            if i == 0:
                dt = struck_analysis_parameters.drift_time_threshold
            elif i == 1:
                t = dt
                dt = 18.0/drift_velocity-t
            elif i == 2:
                dt = 1.0/drift_velocity

        if n_slices == 4:
            if i == 0:
                dt=4.0
            elif i == 1:
                t = 4.0
                dt = struck_analysis_parameters.drift_time_threshold-t
            elif i == 2:
                t = struck_analysis_parameters.drift_time_threshold
                dt = 18.0/drift_velocity-t
            elif i == 3:
                dt = 1.0/drift_velocity
            
        
        print "---> %i: t=%.2f microseconds, dt=%.2f" % (i,t, dt)
        drift_time_cut = "(rise_time_stop99-trigger_time>%s)&&(rise_time_stop99-trigger_time<%s)" % (t, t+dt)
        if "chargeEnergy" in all_energy_var:
            drift_time_cut = struck_analysis_cuts.get_drift_time_cut(
                drift_time_low=t,
                drift_time_high=t+dt,
            )
        selection = " && ".join(selections + [drift_time_cut])
        print "\t selection:", selection

        print "\t drift_time_cut", drift_time_cut

        if do_fit:
            result = fit_peak.fit_channel(
                tree=tree, 
                channel=None, 
                basename=basename, 
                do_1064_fit=False, 
                all_energy_var=all_energy_var, 
                selection=selection,
                do_use_step=True,    
                min_bin=200,
                max_bin=1500,
                line_energy = 570,
                fit_half_width=fit_half_width,
                do_use_exp=True,
            )
            result["dt"] = dt
            all_results[t] = result


            # rename fit plot to something more descriptive:
            plot_name = "fit_all_%s_lin.pdf" % basename
            new_plot_name = "z_slice_fit_%i_to_%i.pdf" % (t*1e3, (t+dt)*1e3)
            cmd = "mv -f %s %s" % (plot_name, new_plot_name)
            output = commands.getstatusoutput(cmd)
            if output[0] != 0:
                print output[1]



            fit_peak.fit_channel(
                tree=tree, 
                channel=None, 
                basename=basename, 
                do_1064_fit=True, 
                all_energy_var=all_energy_var, 
                selection=selection,
                do_use_step=True,    
                min_bin=200,
                max_bin=1500,
                line_energy = 1060, # not sure this does anything for 1-MeV peak...
                fit_half_width=fit_half_width,
                do_use_exp=True,
            )



        hist = TH1D("hist_%i_to_%i" % (t*1e3, (t+dt)*1e3), "",n_bins,min_bin,max_bin)
        hists.append(hist)
        tree.Draw("%s >> %s" % (all_energy_var, hist.GetName()),selection,"goff")
        print "%i entries in hist %s" % (hist.GetEntries(), hist.GetName())
        print selection
        print all_energy_var
        legend.AddEntry(hist,"%.1f to %.1f #mus" % (t, t+dt),"l")

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
    c1.SetLogy(0)
    c1.Update()
    c1.Print("z_slices_%i_lin.pdf" % (len(hists)-2))

    if not gROOT.IsBatch():
        raw_input("enter to continue ")

    out_file.Write()


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        sys.exit(1)

    process_file(sys.argv[1])


