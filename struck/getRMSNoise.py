import ROOT
import struck_analysis_parameters

def getRMS():

    tree = ROOT.TChain("tree")
    tree.Add("/home/teststand/2016_08_15_8th_LXe_overnight/tier3_llnl/overnight8thLXe.root")

    plot_name = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_llnl/RMSNoise.pdf"
    
    canvas = ROOT.TCanvas("canvas")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()
    canvas.Print("%s[" % plot_name) # open multi-page canvas

    n_bins = 500
    energy_max = 200.0

    log = open('/home/teststand/2016_08_15_8th_LXe_overnight/tier3_llnl/log_RMSNoise.txt', 'w')

    log.write("# Fits are in %s \n" % plot_name)
    
    mygaus   = ROOT.TF1("mygaus", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)", 0, energy_max)

    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        
        if not value:
            #not a used channel
            log_out =  "rms_keV[%i] = %f # %s \n" %(channel, 0.0, "Not Used")
            log.write(log_out)
            continue

        hist = ROOT.TH1D("hist_%i" % channel,"",n_bins,0, energy_max)
        hist.SetXTitle("RMS Noise [keV]")
        hist.SetYTitle("Counts")
        hist.GetYaxis().SetTitleOffset(1.2)
        hist.SetLineWidth(3)
        color = struck_analysis_parameters.get_colors()[channel]
        hist.SetLineColor(color)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.8)

        #draw_cmd = "baseline_rms*calibration >> %s" % (hist.GetName())
        #selection = "channel==%i"%channel

        draw_cmd = "baseline_rms[%i]*calibration[%i] >> %s" % (channel, channel, hist.GetName())
        selection = ""

        n_drawn = tree.Draw(draw_cmd, selection)
        
        canvas.Update()
        #raw_input("Pause before fit")

        #mygaus.SetParameter(1, hist.GetBinCenter(hist.GetMaximumBin())) #mean
        #mygaus.SetParameter(0, hist.GetMaximum()) #amplitude
        #mygaus.SetParameter(2, 40) #sigma
        #fit_result = hist.Fit("mygaus", "QWBRS")
        #mean = mygaus.GetParameter(1)
        #mean_error = mygaus.GetParError(1)
        
        mean = hist.GetMean()
        mean_error = hist.GetMeanError()
        log_out =  "rms_keV[%i] = %f  # +/- %f  \n" %(channel, mean, mean_error)
        
        print log_out
        log.write(log_out)

        label = struck_analysis_parameters.channel_map[channel]
        title = "ch %i: %s | %.2e counts | %s | #tau = %f #pm %f" % (channel, label, n_drawn, selection, mean, mean_error)
        hist.SetTitle(title)

        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        #raw_input()

        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        #raw_input()

    canvas.Print("%s]" % plot_name) # close multi-page canvas


if __name__ == "__main__":

    getRMS()


