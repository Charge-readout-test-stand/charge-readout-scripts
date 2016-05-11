
"""
Compare different energy spectra from NEST, G4, tier3 between different tier3
directories
"""

import sys
import glob

from ROOT import gROOT
gROOT.SetBatch(True)
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
    #prefix = "gamma_and_e"
    prefix = "new_physics"

    print "--> drawing %i hists" % len(hists)

    legend = TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetFillColor(0)


    if len(hists) == 2:
        hist = hists[1]
        fill_style = hist.GetFillStyle()
        color = hist.GetLineColor()
        hist.SetFillStyle(3005)
        hist.SetLineColor(TColor.kBlack)
        hist.SetFillColor(TColor.kBlack)


    basename = hists[0].GetTitle()
    hists[0].SetTitle("") # set to empty for plotting
    hists[0].Draw()
    hists[0].SetXTitle("Energy [keV]")
    hists[0].SetYTitle("Counts / %.1f keV" % hists[0].GetBinWidth(1))
    y_max = 0
    for i_hist, hist in enumerate(hists):
        if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()
        hist.Draw("same")
        title = hist.GetTitle()
        if i_hist == 0: title = basename
        legend_entry = "%s: (%.2e), mean=%.2f" % (title, hist.GetEntries(), hist.GetMean())
        legend.AddEntry(hist, legend_entry,)
    hists[0].SetMaximum(y_max*1.1)
    hists[0].SetMinimum(0.5)
    legend.Draw()
    canvas.Update()
    if plot_name is None: plot_name = hists[0].GetName()
    canvas.Print("%s_%s.pdf" % (prefix, plot_name))
    hists[0].SetTitle(basename) # reset after plotting
    if len(hists) == 2: # reset after plotting
        hist = hists[1]
        hist.SetFillStyle(fill_style)
        hist.SetLineColor(color)
        hist.SetFillColor(color)

    if not gROOT.IsBatch():
        raw_input("press enter to continue... ")

def get_hist(
    tree, 
    draw_command, 
    name, color, fill_style,
    n_bins=125, min_bin=0, max_bin=2500,
    gr_zero=True, # only use event > 0
    selection=None,
    basename=None,
):

    print "--> filling hist"
    hist = TH1D(name,"",n_bins, min_bin, max_bin)
    if basename:
        title = "%s, %s" % (basename, draw_command)
        if selection:
            title += " {%s}" % selection
        hist.SetTitle(title)
    hist.SetLineColor(color)
    hist.SetFillColor(color)
    hist.SetFillStyle(fill_style)
    if selection is None:
        selection = ""
        if gr_zero:
            selection = "%s>0" % draw_command
    print "\t %s {%s}" % (draw_command, selection)
    print "\t %i entries drawn" % tree.Draw(
        "%s >> %s" % (draw_command, hist.GetName()), 
        selection,
        "goff" # graphics off during this operation
    )
    print "\t %i entries in hist %s: %s" % (hist.GetEntries(), hist.GetName(),
        hist.GetTitle())

    if "NumTE" in draw_command:
        # this is only for 1-MeV e- or gamma sims:
        Wvalue = struck_analysis_parameters.Wvalue
        new_Wvalue = 1e3/hist.GetMean()*Wvalue
        print "new W-value: ", new_Wvalue, ", new/old: ", (new_Wvalue/Wvalue)
    
    return hist

def draw_plots(directories):

    Wvalue = struck_analysis_parameters.Wvalue
    colors = struck_analysis_parameters.get_colors()
    eDiff=300 # keV

    print "%i directories" % len(directories)

    mc_energy_hists = [] # E in active LXe, no NEST
    mc_all_energy_hists = [] # E in all LXE, no NEST
    nest_energy_hists = [] # NEST E in all LXe
    te_energy_hists = [] # NEST TEs
    mc_minus_nest_hists = [] 
    mc_minus_te_hists = []
    charge_energy_hists = [] # instrumented charge channels
    mc_charge_energy_hists = [] # all charge channels

    legend = TLegend(0.1, 0.9, 0.9, 0.99)
    legend.SetFillColor(0)

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)

    for directory in directories:

        file_names = "%s/tier3_*.root" % directory
        print "--> processing %s:" % file_names

        basename = "%i" % len(mc_all_energy_hists)
        for part in directory.split("/"):
            if "dcoef" in part: basename = part
        print "basename:", basename

        i_hist = len(mc_all_energy_hists)
        color = colors[i_hist]
        fill_style = 3004 + i_hist

        tree = TChain("tree")
        print "%i files added" % tree.Add(file_names)
        print "%i entries in tree" % tree.GetEntries()


        
        # make a 2-D plot
        if True:
            canvas.SetLogz(1)
            n_bins = 200
            hist = TH2D("2dhist%i" % len(mc_all_energy_hists),"",n_bins,0,2500,n_bins,0,2500)
            hist.SetTitle(basename)
            hist.SetXTitle("MCtotalEventLXeEnergy*1e3 [keV]")
            hist.SetYTitle("NumTE*%s/1e3 [keV]" % Wvalue)
            hist.GetYaxis().SetTitleOffset(1.3)
            n_2d = tree.Draw(
                "NumTE*%s/1e3:MCtotalEventLXeEnergy*1e3 >> %s" % (Wvalue, hist.GetName()),
                "","colz")
            print "%i entries in 2D hist" % n_2d
            line = TLine(0.0,0.0,2500,2500)
            line.Draw()
            canvas.Update()
            canvas.Print("%s.pdf" % basename)
            if not gROOT.IsBatch():
                raw_input("press enter to continue... ")


        selection = None
        #selection = "MCtotalEventLXeEnergy>0.999"

        hist = get_hist(tree,"MCchargeEnergy", "chargeE%i" % i_hist,
        color, fill_style, selection=selection, basename=basename)
        mc_charge_energy_hists.append(hist)

        hist = get_hist(tree,"chargeEnergy", "MCchargeE%i" % i_hist,
        color, fill_style, selection=selection, basename=basename)
        charge_energy_hists.append(hist)

        hist = get_hist(tree,"MCtotalEventEnergy*1e3", "Mc%i" % i_hist,
        color, fill_style, selection=selection, basename=basename)
        mc_energy_hists.append(hist)

        hist = get_hist(tree,"MCtotalEventLXeEnergy*1e3", "McAllLXe%i" % i_hist,
        color, fill_style, selection=selection, basename=basename)
        mc_all_energy_hists.append(hist)

        hist = get_hist(tree,"NumTE*%s/1e3" % Wvalue, "TE%i" % i_hist, color,
        fill_style, selection=selection, basename=basename)
        te_energy_hists.append(hist)
        
        hist = get_hist(tree,"MCnestEventEnergy*1e3", "NestE%i" % i_hist, color,
        fill_style, selection=selection, basename=basename)
        nest_energy_hists.append(hist)

        hist = get_hist(tree,"(MCtotalEventLXeEnergy*1e3-NumTE*%s/1e3)" % Wvalue, 
        "McminusTE%i" % i_hist, color, fill_style, gr_zero=False, basename=basename,
        min_bin=-eDiff, max_bin=eDiff, selection="MCtotalEventLXeEnergy>0||NumTE>0")
        #min_bin=-eDiff, max_bin=eDiff, selection="MCtotalEventLXeEnergy>0.999&&NumTE>0")
        mc_minus_nest_hists.append(hist)

        hist = get_hist(tree,"(MCtotalEventLXeEnergy-MCnestEventEnergy)*1e3", 
        "McminusNest%i" % i_hist, color, fill_style, gr_zero=False, basename=basename,
        min_bin=-eDiff, max_bin=eDiff,selection="MCtotalEventLXeEnergy>0||MCnestEventEnergy>0")
        #min_bin=-eDiff, max_bin=eDiff,selection="MCtotalEventLXeEnergy>0.999&&MCnestEventEnergy>0")
        mc_minus_te_hists.append(hist)


        # end loop over directories

      
        
    canvas.SetLogy(1)

    # print an MC vs. TE hist for each directory
    for i in xrange(len(mc_all_energy_hists)):
        draw_hists(canvas, legend, [mc_all_energy_hists[i], te_energy_hists[i]],"mcAllVsTE%i"%i)
        draw_hists(canvas, legend, [charge_energy_hists[i], te_energy_hists[i]],"CEVsTE%i"%i)
        draw_hists(canvas, legend, [mc_all_energy_hists[i], charge_energy_hists[i]],"mcAllVsCE%i"%i)
        draw_hists(canvas, legend, [mc_charge_energy_hists[i], charge_energy_hists[i]],"mcCEVsCE%i"%i)
        draw_hists(canvas, legend, [mc_energy_hists[i], charge_energy_hists[i]],"mcVsCE%i"%i)
        draw_hists(canvas, legend, [mc_all_energy_hists[i], mc_energy_hists[i]],"mcAllVsMc%i"%i)

    if len(mc_all_energy_hists) > 1:
        draw_hists(canvas,legend, mc_energy_hists)
        draw_hists(canvas,legend, charge_energy_hists)
        draw_hists(canvas,legend, mc_charge_energy_hists)
        draw_hists(canvas,legend, mc_all_energy_hists)
        draw_hists(canvas,legend, te_energy_hists)
        draw_hists(canvas,legend, nest_energy_hists)
        draw_hists(canvas,legend, mc_minus_nest_hists)
        draw_hists(canvas,legend, mc_minus_te_hists)

        
        
if __name__ == "__main__":


    if len(sys.argv) < 2:
        print "arguments: MC tier 3 to compare"
        sys.exit()

    draw_plots(sys.argv[1:])
    

