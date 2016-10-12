"""
Draw RGA scan from converted txt to root files.
"""

import os
import sys
import ROOT

def main(filenames):

    colors = []
    colors.append(ROOT.kBlue)
    colors.append(ROOT.kRed)
    colors.append(ROOT.kGreen+2)
    colors.append(ROOT.kViolet)

    canvas = ROOT.TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid()

    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)

    # use these to keep trees & files in memory
    trees = []
    tfiles = []

    # use hist to set axis limits
    frame_hist = ROOT.TH1D("hist","",100,0,80)
    frame_hist.SetMinimum(1e-10)
    frame_hist.SetMaximum(3e-7)
    frame_hist.Draw("axis")
    frame_hist.Draw("axig same")
    frame_hist.SetYTitle("Pressure [Torr]")
    frame_hist.SetXTitle("Mass")

    for i, filename in enumerate(filenames):

        basename = os.path.splitext(os.path.basename(filename))[0]
        color = colors[ len(trees)  % len(colors)]
        line_style = len(trees) / len(colors) 

        tfile = ROOT.TFile(filename)
        tree = tfile.Get("tree")
        data_tree = tfile.Get("data_tree")
        data_tree.GetEntry(0)
        noise_floor = data_tree.noise_floor # scan speed
        #if noise_floor == 0: continue # noise floor 0 seems to be scan speed 1 (slowest)
        if noise_floor == 2: continue

        n_entries = tree.GetEntries()
        print "\t %i entries" % n_entries
        if n_entries < 1000: continue

        print "--> processing", i, filename
        #print i, line_style
        #print color

        tree.SetLineColor(color)
        n_drawn = tree.Draw("pressure:mass","","l same")
        legend.AddEntry(tree, basename, "l")
        trees.append(tree)
        tfiles.append(tfile)

    legend.Draw()
    canvas.Update()
    canvas.Print("RGA_scans.pdf")
    raw_input("enter to continue...")


if __name__ == "__main__":


    filenames = []

    # Rogers 4003 PCB samples for BNL ASIC tests:
    #filenames.append("2016_10_07_before_PCB_samples.root")
    #filenames.append("2016_10_07_before_PCB_samples_2.root")
    #filenames.append("2016_10_07_before_PCB_samples_3.root")
    filenames.append("2016_10_07_before_PCB_samples_4.root")
    filenames.append("2016_10_10_AEM_PCB_sample_4.root")
    filenames.append("2016_10_12_EEM_PCB_sample_1.root")

    if len(sys.argv) > 1:
        filenames = sys.argv[1:]
    main(filenames)

