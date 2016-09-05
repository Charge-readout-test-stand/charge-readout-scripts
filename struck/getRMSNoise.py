import os
import ROOT
import struck_analysis_parameters

def getRMS(calibrate):

    filename = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v3.root"
    tree = ROOT.TChain("tree")
    tree.Add(filename)

    basename = os.path.splitext(os.path.basename(filename))[0]
    print "basename:", basename


    log_name = "log_RMSNoise.txt"
    plot_name = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_%s.pdf" % basename
    out_fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_%s.root" % basename
    
    if calibrate:
        plot_name = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_calibrated_%s.pdf" % basename
        out_fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_calibrated_%s.root" % basename
        log_name = "log_RMSNoise_calibrated.txt"

    out_rfile = ROOT.TFile(out_fname, "RECREATE")

    canvas = ROOT.TCanvas("canvas")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()
    canvas.Print("%s[" % plot_name) # open multi-page canvas

    n_bins = 500
    energy_max = 200.0

    log = open(log_name, 'w')

    log.write("# Fits are in %s \n" % plot_name)
    
    mygaus   = ROOT.TF1("mygaus", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)", 0, energy_max)
    legend = ROOT.TLegend(0.1, 0.85, 0.9, 0.99)
    legend.SetNColumns(8)
    calibration_values = struck_analysis_parameters.calibration_values

    hist_list = []

    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        
        if not value:
            #not a used channel
            log_out =  "rms_keV[%i] = %f # %s \n" %(channel, 0.0, "Not Used")
            log.write(log_out)
            continue

        hist = ROOT.TH1D("hist_%i" % channel,"",n_bins,0, energy_max)
        hist.SetXTitle("RMS Noise [ADC units]")
        hist.SetYTitle("Counts")
        hist.GetYaxis().SetTitleOffset(1.2)
        hist.SetLineWidth(3)
        color = struck_analysis_parameters.get_colors()[channel]
        hist.SetLineColor(color)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.8)
        hist.SetDirectory(0)

        draw_cmd = ""
        if calibrate:
            draw_cmd = "baseline_rms[%i]*%s >> %s" % (channel, calibration_values[channel], hist.GetName())
        else:
            # use ADC units:
            draw_cmd = "baseline_rms[%i] >> %s" % (channel, hist.GetName())

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
        
        log_out =  "rms_keV[%i] = %f*calibration_values[%i]  # +/- %f  \n" %(channel, mean, channel, mean_error)

        if calibrate:
            log_out =  "rms_keV[%i] = %f # +/- %f  \n" %(channel, mean, mean_error)

        print log_out
        log.write(log_out)

        label = struck_analysis_parameters.channel_map[channel]
        title = "ch %i: %s | %.2e counts | RMS = %f #pm %f" % (channel, label, n_drawn, mean, mean_error)
        hist.SetTitle(title)
        legend.AddEntry(hist, label, "p")
        
        hist.Write()
        hist_list.append(hist)

        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        #raw_input()

        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        #raw_input()
    
    out_rfile.Close()

    #Draw total Hist
    hist_list[0].SetTitle("")
    hist_list[0].Draw()
    for hist in hist_list:
        hist.Draw("SAME")
    
    legend.Draw()
    raw_input()
    canvas.Print("%s" % plot_name)


    canvas.Print("%s]" % plot_name) # close multi-page canvas

def plotRMS():
    fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_calibrated_overnight8thLXe_v3.root"
    rfile = ROOT.TFile(fname)
    
    canvas = ROOT.TCanvas("canvas")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()

    calibration_values = struck_analysis_parameters.calibration_values
    

    legend = ROOT.TLegend(0.1, 0.85, 0.9, 0.99)
    legend.SetNColumns(8)
    
    drawn = False
    nchs = len(struck_analysis_parameters.charge_channels_to_use)
    noise_hist = ROOT.TH1F("nhist","nhist", nchs, 0, nchs)

    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        
        label = struck_analysis_parameters.channel_map[channel]
        bini = channel+1
        noise_hist.GetXaxis().SetBinLabel(bini, label)

        if not value:
            noise_hist.SetBinContent(bini,0.0)
            noise_hist.SetBinError(bini, 0.0)
            continue

        hist = rfile.Get("hist_%i" % channel)
 
        if drawn: 
            hist.Draw("SAME")
        else:
            hist.SetTitle("")
            hist.GetXaxis().SetRangeUser(9, 60)
            hist.Draw()
            drawn=True
        
        #canvas.Update()
        mean = hist.GetMean()
        mean_error = hist.GetMeanError()
        
        print label, mean

        noise_hist.SetBinContent(bini, mean)
        noise_hist.SetBinError(bini, mean_error)

        legend.AddEntry(hist, label, "p")

    legend.Draw()
    canvas.Update()
    canvas.Print("CombinedNoise.pdf")
    print "Holding"
    raw_input("Hold Enter")
    
    print "Doing Noise"
    canvas.SetGrid(False)
    noise_hist.SetMarkerStyle(21)
    noise_hist.GetXaxis().SetLabelSize(0.03)
    noise_hist.SetMarkerColor(ROOT.kRed)
    noise_hist.Draw()
    noise_hist.SetTitle("Channel RMS Noise")
    noise_hist.GetYaxis().SetTitle("RMS Noise[keV]")
    noise_hist.GetXaxis().SetTitle("Channel")
    canvas.Update()
    canvas.Print("Noise_vs_Channel.pdf")
    print "Noise Plot"
    raw_input("Hold Enter")


if __name__ == "__main__":
    remake = False
    calibrate = True
    if remake:
        getRMS(calibrate)
    else:
        plotRMS()


