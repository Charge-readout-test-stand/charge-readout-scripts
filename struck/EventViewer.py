import ROOT
import sys
import os
import struck_analysis_parameters



filename = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2016_03_07_7thLXe/tier1/tier1_overnight_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03-08_10-08-33.root"

num_channels = 16
offset = 500
ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetTitleStyle(0)
ROOT.gStyle.SetTitleBorderSize(0)
c1 = ROOT.TCanvas()


color_list = [ROOT.kRed, ROOT.kGreen, ROOT.kBlue, ROOT.kBlack, ROOT.kYellow, ROOT.kOrange, ROOT.kPink, ROOT.kMagenta, ROOT.kCyan]
name_list = ["X16", "X17", "X18", "X19", "Y16", "Y17", "Y18", "Y19", "PMT"]


def GetGoodTrees(tfile):
    good_trees = []
    channel_numbers = []
    entries = 0
    for i in range(0, num_channels):
        tname = "tree"+str(i)
        tree = tfile.Get(tname)
        if tree.GetEntries() > 0:
            print "Using tree", tname, " Entries = ", tree.GetEntries()
            if entries == 0:
                entries = tree.GetEntries()
            elif entries != tree.GetEntries():
                sys.exit("not same number of entries is this actually bad????")
            good_trees.append(tree)
            channel_numbers.append(i)
    return good_trees, entries, channel_numbers


def GetTier3_Energy(tfile, entries, entry):
    directory =  os.path.dirname(tfile).replace("tier1", "tier3_external")
    basename =  os.path.basename(tfile).replace("tier1", "tier3")
    fullname =  os.path.join(directory, basename)
    if os.path.isfile(fullname):
        tier3 = ROOT.TFile(fullname)
        tier3_tree = tier3.Get("tree")
        if tier3_tree.GetEntries() != entries:
            print "Tier3 and Tier1 don't quite line up"
            print tier3_tree.GetEntries(), entries
            sys.exit(1)
        else:
            tier3_tree.GetEntry(entry)
            return tier3_tree.chargeEnergy
    else:
        print "No Tier3 file found??"
        sys.exit(1)




def DrawEvents(fname):
    tfile = ROOT.TFile(fname)
    good_trees, entries, channel_numbers = GetGoodTrees(tfile)
    
    GetTier3_Energy(fname, entries, 0)

    hists = []
    for (i, tree) in enumerate(good_trees):
        hist = ROOT.TH1D("hist%i" % i,"",10,0,10)
        try:
            color = color_list[i]
        except IndexError:
            color = TColor.kBlack

        hist.SetLineColor(color)
        hist.SetFillColor(color)
        hists.append(hist)
    
    for eventi in range(0,entries,1):
        cE = GetTier3_Energy(fname, entries, eventi)
        if cE < 100:
            print "Skipping Event", eventi
            continue
        else:
            print "Got Event with Energy", cE
        frame_hist = ROOT.TH1D("hist", "", 100, 0, 800/25.0e6*1e6)
        frame_hist.SetLineColor(ROOT.kWhite)
        #frame_hist.SetTitle("Waveforms")
        frame_hist.SetXTitle("Time [#mus]")
        frame_hist.SetYTitle("ADC Units (Arbitrary Offset)")
        frame_hist.GetYaxis().SetTitleOffset(1.3)
        frame_hist.SetBinContent(1, pow(2,14))
        frame_hist.Draw()
        legend = ROOT.TLegend(0.1, 0.86, 0.9, 0.99)
        legend.SetNColumns(3)
        
        for i, tree in enumerate(good_trees):
            calib = struck_analysis_parameters.calibration_values[channel_numbers[i]]
            draw_cmd = "((wfm - wfm[0])*%f + %i):Iteration$*40/1e3" % (calib, i*offset)
            print i, eventi, draw_cmd, calib
            tree.SetLineColor(color_list[i])
            tree.SetLineWidth(2)
            tree.Draw(draw_cmd,"Entry$=="+str(eventi), "l same")
            legend.AddEntry(hists[i], name_list[i] + " E = ")
        
        print "Final Thing"
        frame_hist.SetMinimum(-1000)
        frame_hist.SetMaximum(6000)
        print "Leg Draw"
        legend.Draw()
        print "Update"
        c1.Update()
        print "Updated"
        raw_input("Event HOLD UNTIL ENTER")
        


if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "Need File Name"
        sys.exit(1)

    #filename = sys.argv[1]
    DrawEvents(filename)
    

