import ROOT
#ROOT.gROOT.SetBatch(True)
import sys
import os
import struck_analysis_parameters
from array import array



filename = "/nfs/slac/g/exo_data4/users/alexis4/test-stand/2016_03_07_7thLXe/tier1/tier1_overnight_cell_full_cathode_bias_1700V_2Vinput_DT1750mV_disc_teed_preamp_extraamplified_trigger_200delay_2016-03-08_10-08-33.root"

num_channels = 16
offset = 500
ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetTitleStyle(0)
ROOT.gStyle.SetTitleBorderSize(0)
#c1 = ROOT.TCanvas("canvas","",800,1100)
c1 = ROOT.TCanvas()
c1.SetGrid(1,1)
c1.SetTopMargin(0.15)

#energy_cut = 570.0
#energy_cut = 1000.0
energy_cut = 0.0
n_plots_total = 100
#n_plots_total = 200
trigger_time = 8.0

color_list = struck_analysis_parameters.get_colors()
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

def GetTier3_Channel_Energy(tfile, entries, entry, channel):
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
            if channel < 8:
                return tier3_tree.energy1_pz[channel]
            else:
                return tier3_tree.wfm_max[channel] - tier3_tree.baseline_mean[channel]
    else:
        print "No Tier3 file found??"
        sys.exit(1)




def DrawEvents(fname):
    tfile = ROOT.TFile(fname)
    good_trees, entries, channel_numbers = GetGoodTrees(tfile)
    
    GetTier3_Energy(fname, entries, 0)


    # get tier3 file:
    directory =  os.path.dirname(fname).replace("tier1", "tier3_external")
    basename =  os.path.basename(fname).replace("tier1", "tier3")
    tier3_file_name =  os.path.join(directory, basename)
    tier3_file = ROOT.TFile(tier3_file_name)
    tier3_tree = tier3_file.Get("tree")
    print "%i entries in tier3" % tier3_tree.GetEntries()

    hists = []
    print "making hists"
    for (i, tree) in enumerate(good_trees):
        hist = ROOT.TH1D("hist%i" % i,"",10,0,10)
        try:
            color = color_list[i]
        except IndexError:
            color = TColor.kBlack

        hist.SetLineColor(color)
        hist.SetFillColor(color)
        hists.append(hist)
        print "%i entries in %s" % (tree.GetEntries(), tree.GetName())
    n_plots = 0
    for eventi in range(0,entries,1):
        tree.GetEntry(eventi)
        tier3_tree.GetEntry(eventi)
        n_rms_above_threshold = 0
        for i_ch in xrange(8):
            rms_keV = tier3_tree.baseline_rms[i_ch]*tier3_tree.calibration[i_ch]
            if rms_keV > 40.0: 
                print "ch %i RMS [keV]: %.3f" % (i_ch, rms_keV)
                n_rms_above_threshold += 1
        if n_rms_above_threshold == 0:
            print "Skipping Event based on RMS:", eventi
            continue
        cE = GetTier3_Energy(fname, entries, eventi)
        if cE < energy_cut:
            print "Skipping Event based on energy:", eventi
            continue
        else:
            print "---> Got Event %i with Energy %s" % (eventi,  cE)
        frame_hist = ROOT.TH1D("hist", "", 100, 0, 800/25.0e6*1e6)
        frame_hist.SetLineColor(ROOT.kWhite)
        #frame_hist.SetTitle("Waveforms")
        frame_hist.SetXTitle("Time [#mus]")
        frame_hist.SetYTitle("Energy (Arbitrary Offset) [keV]")
        frame_hist.GetYaxis().SetTitleOffset(1.3)
        frame_hist.SetBinContent(1, pow(2,14))
        frame_hist.Draw()
        legend = ROOT.TLegend(0.1, 0.86, 0.9, 0.99)
        legend.SetFillColor(0)
        legend.SetNColumns(4)
        sum_wfm = [0.0]*800
        x_wfm = [0.0]*800
        y_wfm = [0.0]*800
        sum_graph = ROOT.TGraph()
        x_graph = ROOT.TGraph()
        y_graph = ROOT.TGraph()
        #sum_graph.SetLineWidth(2)
        for i, tree in enumerate(good_trees):
            calib = struck_analysis_parameters.calibration_values[channel_numbers[i]]
            if name_list[i] != "PMT":
                calib = calib/2.5 #2V range not 5V

            else:
                calib = 1.0
            draw_cmd = "((wfm - wfm[0])*%f + %i):Iteration$*40/1e3" % (calib, (i+2)*offset)
            print "\t", i, eventi, draw_cmd, calib
            tree.SetLineColor(color_list[i])
            tree.SetLineWidth(2)
            tree.Draw(draw_cmd,"Entry$=="+str(eventi), "l same")
            chanE = GetTier3_Channel_Energy(fname, entries, eventi, i)
            legend.AddEntry(hists[i], name_list[i] + " E = %.1f" % chanE, "f")
            if name_list[i] != "PMT":
                wfm = array('d',tree.wfm)
                baseline = sum(wfm[:100])/100.0
                sum_wfm = [sum_wfm[j] + (wfm[j] - baseline)*calib for j in xrange(len(wfm))]
                if i < 4:
                    x_wfm = [x_wfm[j] + (wfm[j] - baseline)*calib for j in xrange(len(wfm))]
                else:
                    y_wfm = [y_wfm[j] + (wfm[j] - baseline)*calib for j in xrange(len(wfm))]

        for j,val in enumerate(sum_wfm):
            sum_graph.SetPoint(sum_graph.GetN(),j*0.040,val)
            x_graph.SetPoint(x_graph.GetN(),j*0.040,x_wfm[j]+offset)
            y_graph.SetPoint(y_graph.GetN(),j*0.040,y_wfm[j]+offset*2)
        
        print "Final Thing"
        frame_hist.SetMinimum(-offset/1.5)
        frame_hist.SetMaximum(offset*(len(name_list)+3))
        legend.AddEntry(sum_graph, "Sum Charge E = %.1f" % cE,"l")
        sum_graph.Draw("l")
        x_graph.SetLineColor(ROOT.TColor.kRed)
        y_graph.SetLineColor(ROOT.TColor.kBlue)
        #x_graph.Draw("l") # x channel sum
        #y_graph.Draw("l") # y channel sum
        print "Leg Draw"
        legend.Draw()

        # vertical line at trigger time
        x_val = trigger_time
        line = ROOT.TLine(x_val, frame_hist.GetMinimum(), x_val, frame_hist.GetMaximum())
        line.SetLineStyle(2)
        line.Draw()

        # vertical line at trigger time
        x_val = trigger_time + struck_analysis_parameters.max_drift_time
        line2 = ROOT.TLine(x_val, frame_hist.GetMinimum(), x_val, frame_hist.GetMaximum())
        line2.SetLineStyle(2)
        line2.Draw()

        print "Update"
        c1.Update()
        print "Updated"
        #raw_input("Event HOLD UNTIL ENTER")
        n_plots += 1
        plot_name = "%iEventsWithChargeAbove%ikeV_7thLXe.pdf" % (
            n_plots_total,
            int(energy_cut),
        )
        if not ROOT.gROOT.IsBatch():
            val = raw_input("--> press enter to continue, p to print ")
            print val
            if val == "p":
                c1.Print("Event_%i_%s" % (eventi, plot_name))

        # print a multi-page pdf:
        if n_plots == 1:
            plot_name = plot_name + "("
        if n_plots >= n_plots_total:
            plot_name = plot_name + ")"
        
        c1.Print(plot_name)


        if n_plots >= n_plots_total:
            print "quitting..."
            sys.exit()

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print "WARNING BYPASSING ARG AND JUST LOOKING AT HARDCODED FILE"
        raw_input("enter to continue")
    else:
        filename = sys.argv[1]
    
    DrawEvents(filename)
    

