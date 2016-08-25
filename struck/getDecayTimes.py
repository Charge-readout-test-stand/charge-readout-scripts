import ROOT
import struck_analysis_parameters

def getDecayTimes():

    tree = ROOT.TChain("tree")
    tree.Add("/home/teststand/2016_08_15_8th_LXe_overnight/DecayTimes/Testing/tier3*.root")

    plot_name = "/home/teststand/2016_08_15_8th_LXe_overnight/DecayTimes/Testing/DecayDist.pdf"
    
    canvas = ROOT.TCanvas("canvas")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()
    canvas.Print("%s[" % plot_name) # open multi-page canvas

    n_bins = 500
    decay_max = 3000

    landau = ROOT.TF1("landau","[0]*TMath::Landau(x,[1],[2],0)", 0, decay_max)
    
    decay_log = open('/home/teststand/2016_08_15_8th_LXe_overnight/DecayTimes/Testing/decay_log.txt', 'w')

    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        
        if not value:
            continue

        hist = ROOT.TH1D("hist_%i" % channel,"",n_bins,0, decay_max)
        hist.SetXTitle("Decay Time [#mus]")
        hist.SetYTitle("Counts")
        hist.GetYaxis().SetTitleOffset(1.2)
        hist.SetLineWidth(3)
        color = struck_analysis_parameters.get_colors()[channel]
        hist.SetLineColor(color)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.8)

        draw_cmd = "decay_fit[%i] >> %s" % (channel, hist.GetName())
        selection = ""
        n_drawn = tree.Draw(draw_cmd, selection)
        
        landau.SetParameter(1, hist.GetBinCenter(hist.GetMaximumBin()))
        landau.SetParameter(2, 150)
        landau.SetParameter(0, hist.GetMaximum())

        fit_result = hist.Fit("landau", "QWBRS")
        #print "Fit = ", landau.GetParameter(1), "+/-", landau.GetParError(1), "Entries = ", hist.GetEntries()
        
        log_out =  "decay_time_values[%i] =  %f*microsecond # +/- %f  \n" %(channel, landau.GetParameter(1), landau.GetParError(1))
        print log_out
        decay_log.write(log_out)

        label = struck_analysis_parameters.channel_map[channel]
        title = "ch %i: %s | %.2e counts | %s | #tau = %f #pm %f" % (channel, label, n_drawn, selection, landau.GetParameter(1), landau.GetParError(1))
        hist.SetTitle(title)

        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("%s" % plot_name)

        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("%s" % plot_name)

    canvas.Print("%s]" % plot_name) # close multi-page canvas


if __name__ == "__main__":

    getDecayTimes()


