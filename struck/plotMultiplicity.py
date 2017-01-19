"""
Draw multiplicity plot
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

    #selection = "chargeEnergy*%s>1000 & chargeEnergy*%s<1200" % (multiplier, multiplier)
    #selection = ""
    #selection = "%s > 200" % struck_analysis_cuts.get_few_channels_cmd_baseline_rms()
    selection = "SignalEnergy>200 && SignalEnergy<1500"


    hists = []
    ch_hists = []

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

    for (i, filename) in enumerate(filenames):
        
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        print "processing file: ", filename

        max_bin = len(struck_analysis_parameters.charge_channels_to_use)
        n_bins = max_bin*2

        hist = ROOT.TH1D("hist%i" % len(hists), basename, n_bins, -0.25, max_bin-0.25)
        print "\thist:", hist.GetName()
        color = colors[len(hists)]
        hist.SetLineColor(color)
        hist.SetFillColor(color)
        bar_width = 1.0/len(filenames)-0.1
        print "\tbar_width:", bar_width
        bar_offset = (0.1+bar_width)*i
        print "\tbar_offset:", bar_offset
        hist.SetBarWidth(bar_width)
        hist.SetBarOffset(bar_offset)
        #hist.SetFillStyle(3004)
        hist.SetLineWidth(2)
        #hist.SetLineStyle(len(hists)+1)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(1.5)
        #hist.SetXTitle("Multiplicity [channels above %.1f keV]" % threshold)
        hist.SetXTitle("Multiplicity")
        hists.append(hist)

        # open the root file and grab the tree
        #root_file = ROOT.TFile(filename)
        #tree = root_file.Get("tree")
        
        tree = ROOT.TChain("tree")
        tree.Add(filename)
        tree.SetBranchStatus("*",0)
        tree.SetBranchStatus("SignalEnergy",1)
        tree.SetBranchStatus("signal_map",1)
        tree.SetBranchStatus("nsignals",1)
        tree.SetBranchStatus("channel",1)
        
        n_entries = tree.GetEntries()
        print "\t%i entries" % n_entries
        hist = hists[i]
        hist.GetDirectory().cd()

        is_MC = True
        try:
            tree.GetEntry(0)
            tree.MCchargeEnergy
        except:
            is_MC = False
        print "\tis_MC:", is_MC

        multiplier = 1.0
        if is_MC:
            multiplier = 1.15

        if False: # ch hist doesn't work for comparing 9th and 10th LXe

            # draw channels hit:    
            #ch_hist = ROOT.TH1D("ch_hist%i" % len(hists), basename,n_bins, -0.25, max_bin-0.25)
            ch_hist = hist.Clone("ch_hist%i" % len(hists))
            #ch_hist.SetLineColor(color)
            #ch_hist.SetLineWidth(2)
            #ch_hist.SetFillColor(color)
            #ch_hist.SetFillStyle(3004)
            #ch_hist.SetBarWidth(bar_width)
            #ch_hist.SetBarOffset(bar_offset)
            ch_hist.SetXTitle("Channel hit")

            ##selection = "energy1_pz>%s" % (threshold/multiplier)
            sel = "signal_map==1 && %s" % selection 
            n_drawn = tree.Draw("channel >> %s" % ch_hist.GetName(), sel,)


            for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):

                i_bin = ch_hist.FindBin(channel)
                n_strips = struck_analysis_parameters.channel_to_n_strips_map[channel]
                label = struck_analysis_parameters.channel_map[channel]
                print "\t\tch %i | %s | %i strips" % (channel, label, n_strips)
                ch_hist.GetXaxis().SetBinLabel(i_bin, label)
                if n_strips>1:
                    ch_hist.SetBinContent(i_bin, ch_hist.GetBinContent(i_bin)/n_strips)

                # set contents to 0 for unused channels
                if val == 0:
                    if channel == struck_analysis_parameters.pmt_channel: continue
                    content = ch_hist.GetBinContent(i_bin)
                    ch_hist.SetBinContent(i_bin, 0.0)
                    print "\t\t\tset ch %i %s bin %i from %i to 0" % (channel, struck_analysis_parameters.channel_map[channel], i_bin, content)


            canvas.SetLogy(1)
            canvas.Update()
            canvas.Print("hitChannels_%s.pdf" % basename)
            ch_hists.append(ch_hist)

            canvas.SetLogy(0)
            canvas.Update()
            canvas.Print("hitChannels_%s_lin.pdf" % basename)

            if not ROOT.gROOT.IsBatch(): raw_input("any key to continue  ")



        #draw_cmd = struck_analysis_cuts.get_multiplicity_cmd(energy_threshold=threshold/multiplier, isMC=is_MC)
        draw_cmd = "nsignals"
        draw_cmd = "%s >> %s" % (draw_cmd, hist.GetName())

        title = selection[:100] + "..."
        print "\tdraw_cmd:", draw_cmd
        print "\tselection", selection

        options = "goff"

        n_entries = tree.Draw(
            draw_cmd,
            selection,
            options,
        )

        print "\t%i drawn entries" % n_entries
        n_entries = hist.GetEntries()
        print "\t%i hist entries" % n_entries
        print "\tmean", hist.GetMean()

        legend.AddEntry(hist, hist.GetTitle(), "f")

    y_max = 0
    for hist in hists:
        n_entries = hist.GetEntries()
        print "scale_factor:", 1.0/n_entries
        hist.Scale(1.0/n_entries)
        if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()


    hists[0].SetMaximum(y_max*1.05)
    hists[0].SetTitle("")
    hists[0].Draw("b")
    for hist in hists:
        hist.Draw("b same")

    n_files = len(filenames)

    canvas.SetLogy(1)
    legend.Draw()
    canvas.Update()
    canvas.Print("multiplicity_%i.pdf" % n_files)

    canvas.SetLogy(0)
    canvas.Update()
    canvas.Print("multiplicity_lin_%i.pdf" % n_files)

    hists[0].SetAxisRange(0, 7.5)
    canvas.Update()
    canvas.Print("multiplicity_lin_zoom_%i.pdf" % n_files)

    if not ROOT.gROOT.IsBatch(): raw_input("any key to continue  ")



    if len(ch_hists) > 0:
        ch_hists[0].SetTitle("")
        #ch_hists[0].Draw("b norm")
        ch_hists[0].Draw("b")
        for hist in ch_hists:
            hist.Draw("b same")

        canvas.SetLogy(1)
        legend.Draw()
        canvas.Update()
        canvas.Print("hitChannels.pdf")

        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("hitChannels_lin.pdf")

        if not ROOT.gROOT.IsBatch(): raw_input("any key to continue  ")



if __name__ == "__main__":


    # data and MC after 6th LXe
    #filenames = [
    #"/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier3_from_tier2/tier2to3_overnight.root",
    #"/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/gamma_1MeV_Ralph/Tier3/all_tier3_gamma_1MeV_Ralph_dcoef0.root",
    #"/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization_NEW/Bi207_Full_Ralph/combined/all_tier3_Bi207_Full_Ralph_dcoef0.root",
    #"/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/digitization/electron_1MeV_Ralph/Tier3/all_tier3_electron_1MeV_Ralph_dcoef0.root",
    #]

    # 8th LXe
    filenames = [
        #"~/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v2.root", # ubuntu DAQ
        #"~/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v3.root", # ubuntu DAQ
        "/p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v4.root ", # LLNL
    ]

    if len(sys.argv) > 1:
        filenames = sys.argv[1:]

    process_files(filenames)



