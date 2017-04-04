"""
Draw is_bad bits

Should add some kind of correlation plot to show which happen at the same time. 
"""

import os
import sys

import ROOT
ROOT.gROOT.SetBatch(True)

ROOT.gROOT.SetStyle("Plain")     
ROOT.gStyle.SetOptStat(0)        
ROOT.gStyle.SetPalette(1)        
ROOT.gStyle.SetTitleStyle(0)     
ROOT.gStyle.SetTitleBorderSize(0)       

import struck_analysis_cuts
import struck_analysis_parameters

def process_files(filenames):

    is_bad_bits = {}
    is_bad_bits[0] = "pmt sig shape"
    is_bad_bits[1] = "RMS noise too high"
    is_bad_bits[2] = "energy1_pz noise too high"
    is_bad_bits[3] = "wfm_min==0"
    is_bad_bits[4] = "wfm_max==2^14-1"
    is_bad_bits[5] = "n channels != 32"
    is_bad_bits[6] = "RMS noise too low"
    is_bad_bits[7] = "energy1_pz noise too low"


    hists = []

    colors = [
        ROOT.kBlue,
        ROOT.kRed,
        ROOT.kGreen+2,
        ROOT.kViolet,
        ROOT.kCyan+3,
        ROOT.kOrange+1,
    ]
    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    #threshold = 10

    # set up a canvas
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)
    canvas.SetBottomMargin(0.15)

    for (i, filename) in enumerate(filenames):
        
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        print "processing file: ", filename

        n_bins = len(is_bad_bits)+1
        hist = ROOT.TH1D("hist%i" % len(hists), basename, n_bins*2, -0.5, n_bins-0.5)
        #print "\t hist:", hist.GetName()
        color = colors[len(hists)]
        hist.SetLineColor(color)
        hist.SetFillColor(color)
        bar_width = 1.0/len(filenames)-0.1
        print "\t bar_width:", bar_width
        bar_offset = (0.1+bar_width)*i
        print "\t bar_offset:", bar_offset
        hist.SetBarWidth(bar_width)
        hist.SetBarOffset(bar_offset)
        #hist.SetFillStyle(3004)
        hist.SetLineWidth(2)
        #hist.SetLineStyle(len(hists)+1)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(1.5)
        hists.append(hist)

        # open the root file and grab the tree
        #root_file = ROOT.TFile(filename)
        #tree = root_file.Get("tree")
        
        tfile = ROOT.TFile(filename)
        tree = tfile.Get("tree")
        #tree = ROOT.TChain("tree")
        #tree.Add(filename)
        tree.SetBranchStatus("*",0)
        tree.SetBranchStatus("is_bad",1)
        
        n_entries = tree.GetEntries()
        print "\t %i entries" % n_entries
        hist = hists[i]
        hist.GetDirectory().cd()

        is_MC = True
        try:
            tree.GetEntry(0)
            tree.MCchargeEnergy
        except:
            is_MC = False
        print "\t is_MC:", is_MC

        for ibit, label in is_bad_bits.items():

            val = pow(2,ibit)
            print "\t bit %i, val: %i, %s" % (ibit, val, label)
            draw_cmd = "%i >> +%s" % (ibit, hist.GetName()) # append to hist
            print "\t\t draw_cmd:", draw_cmd
            selection = "is_bad & %i" % val
            print "\t\t selection:", selection

            n_entries = tree.Draw(
                draw_cmd,
                selection,
                "goff",
            )

            print "\t\t %i entries drawn" % n_entries
            n_entries = hist.GetEntries()
            print "\t\t %i hist entries" % n_entries

            ibin = hist.FindBin(ibit)
            hist.GetXaxis().SetBinLabel(ibin, label)

        n_entries = tree.GetEntries()
        hist.Scale(1.0/n_entries)
        legend.AddEntry(hist, hist.GetTitle(), "f")

    y_max = 0
    for hist in hists:
        if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()

    hists[0].SetMaximum(y_max*1.05)
    hists[0].SetTitle("")
    hists[0].Draw("b hist")
    for hist in hists:
        hist.Draw("b hist same")

    n_files = len(filenames)


    canvas.SetLogy(1)
    legend.Draw()
    canvas.Update()
    canvas.Print("is_bad_%i.pdf" % n_files)

    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("is_bad_lin_%i.pdf" % n_files)

    if not ROOT.gROOT.IsBatch(): raw_input("any key to continue  ")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        filenames = sys.argv[1:]
    else:
        print "arguments: tier3 files"
        sys.exit()

    process_files(filenames)

