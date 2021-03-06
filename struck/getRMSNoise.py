import os
import sys
import ROOT
ROOT.gROOT.SetBatch(True)
import struck_analysis_parameters

def getRMS(calibrate):

    #filename = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v3.root"
    #filename = "/home/teststand/2016_09_13_pulser_tests/tier3_SIS3316Raw_20160913233650_digitizer_noise_tests__1-ngm.root"
    filename = "noiselib/NoiseLib_9thLXe.root"

    if len(sys.argv) > 1:
        filename = sys.argv[1]

    print "--> getRMS:", filename

    tree = ROOT.TChain("tree")
    tree.Add(filename)
    tree.SetBranchStatus("*",0) # first turn off all branches
    tree.SetBranchStatus("baseline_rms",1) 

    basename = os.path.splitext(os.path.basename(filename))[0]
    print "basename:", basename

    log_name = "log_RMSNoise.txt"
    plot_name = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_%s.pdf" % basename
    out_fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_%s.root" % basename

    if calibrate:
        plot_name = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_calibrated_%s.pdf" % basename
        out_fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_calibrated_%s.root" % basename
        log_name = "log_RMSNoise_calibrated.txt"

    if len(sys.argv) > 1:
        plot_name = "RMSNoise_%s.pdf" % basename
        out_fname = "RMSNoise_%s.root" % basename
    
    out_rfile = ROOT.TFile(out_fname, "RECREATE")

    canvas = ROOT.TCanvas("canvas")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()
    canvas.Print("%s[" % plot_name) # open multi-page canvas

    n_bins = 2000
    energy_max = 200.0

    log = open(log_name, 'w')

    log.write("# Fits are in %s \n" % plot_name)
    
    mygaus   = ROOT.TF1("mygaus", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)", 0, energy_max)
    legend = ROOT.TLegend(0.1, 0.85, 0.9, 0.99)
    legend.SetNColumns(8)
    calibration_values = struck_analysis_parameters.calibration_values

    hist_list = []

    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        
        #if not value:
        #    #not a used channel
        #log_out =  "rms_keV[%i] = %f # %s \n" %(channel, 0.0, "Not Used")
        #    log.write(log_out)
        #    continue

        hist = ROOT.TH1D("hist_%i" % channel,"",n_bins,0, energy_max)
        hist.SetXTitle("RMS Noise [ADC units]")
        if calibrate:
            hist.SetXTitle("RMS Noise [keV]")
        hist.SetYTitle("Counts")
        hist.GetYaxis().SetTitleOffset(1.2)
        hist.SetLineWidth(3)
        color = struck_analysis_parameters.get_colors()[channel]
        hist.SetLineColor(color)
        hist.SetMarkerColor(color)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.8)
        hist.GetDirectory().cd()
        #hist.SetDirectory(0)

        draw_cmd = ""
        if calibrate:
            draw_cmd = "baseline_rms[%i]*%s >> %s" % (channel, calibration_values[channel], hist.GetName())
        else:
            # use ADC units:
            draw_cmd = "baseline_rms[%i] >> %s" % (channel, hist.GetName())

        selection = ""
        print draw_cmd
        print selection

        n_drawn = tree.Draw(draw_cmd, selection)
        print "n_drawn", n_drawn
        print "entries in hist:", hist.GetEntries()
        
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
        sigma = hist.GetRMS()
        sigma_error = hist.GetRMSError()
        label = struck_analysis_parameters.channel_map[channel]
        
        log_out =  "rms_keV[%i] = %f*calibration_values[%i]  # +/- %f %s\n" %(channel, mean, channel, mean_error, label)
        log_out += "rms_keV_sigma[%i] = %f*calibration_values[%i] # +/- %f %s\n" % (channel, sigma, channel, sigma_error, label)

        if calibrate:
            log_out =  "rms_keV[%i] = %f # +/- %f  \n" %(channel, mean, mean_error)
            log_out += "rms_keV_sigma[%i] = %f # +/- %f\n" % (channel, sigma, sigma_error)


        print log_out
        log.write(log_out)

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
    

    #Draw total Hist
    hist_list[0].SetTitle("")
    hist_list[0].Draw()
    for i_hist, hist in enumerate(hist_list):
        print "printing hist %i of %i" % (i_hist, len(hist_list))
        hist.Draw("SAME")
    
    legend.Draw()
    if not ROOT.gROOT.IsBatch():
        raw_input("press enter")
    canvas.Print("%s" % plot_name)


    canvas.Print("%s]" % plot_name) # close multi-page canvas
    out_rfile.Close()

def plotRMS(calibrate):
    fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_calibrated_overnight8thLXe_v3.root"
    fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_calibrated_tier3_SIS3316Raw_20160913233650_digitizer_noise_tests__1-ngm.root"
    fname = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/RMSNoise_tier3_SIS3316Raw_20160913233650_digitizer_noise_tests__1-ngm.root"
    fname = "noiselib/NoiseLib_9thLXe.root"

    if len(sys.argv) > 1:
        fname = sys.argv[1]
        basename = os.path.splitext(os.path.basename(fname))[0]
        fname = "RMSNoise_%s.root" % basename
    
    print "---> plotRMS:", fname

    rfile = ROOT.TFile(fname)
    
    canvas = ROOT.TCanvas("canvas")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()

    calibration_values = struck_analysis_parameters.calibration_values
    

    legend = ROOT.TLegend(0.1, 0.85, 0.9, 0.99)
    legend.SetNColumns(8)
    
    drawn = False
    nchs = len(struck_analysis_parameters.charge_channels_to_use)
    noise_hist = ROOT.TH1F("nhist","", nchs-2, 0, nchs-2)
    noise_hist.SetMinimum(0)
    noise_hist.SetLineColor(ROOT.kBlue+1)
    noise_hist.SetMarkerColor(ROOT.kBlue+1)
    noise_hist.SetLineWidth(2)
    #noise_hist.GetXaxis().SetLabelSize(0.03)
    noise_hist.GetXaxis().SetTitleOffset(1.7)
    plot_name = "Noise_vs_Channel"
    noise_hist.SetTitle("Channel RMS Noise")
    noise_hist.GetYaxis().SetTitle("RMS Noise [ADC units]")
    if calibrate:
        noise_hist.GetYaxis().SetTitle("RMS Noise [keV]")
        noise_hist.SetTitle("")
        plot_name += "_keV"
    noise_hist.GetXaxis().SetTitle("Channel")
    noise_hist_single = noise_hist.Clone("nhist1")
    noise_hist_double = noise_hist.Clone("nhist2")
    noise_hist_many = noise_hist.Clone("nhistX")
    y_max = 0

    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        
        if not value: # skip PMT & pulser
            continue

        label = struck_analysis_parameters.channel_map[channel]
        bini = channel+1
        noise_hist.GetXaxis().SetBinLabel(bini, label)
        noise_hist_single.GetXaxis().SetBinLabel(bini, label)
        noise_hist_double.GetXaxis().SetBinLabel(bini, label)
        noise_hist_many.GetXaxis().SetBinLabel(bini, label)


        n_strips = struck_analysis_parameters.channel_to_n_strips_map[channel]

        hist = rfile.Get("hist_%i" % channel)
 
        if drawn: 
            hist.Draw("SAME")
        else:
            hist.SetTitle("")
            hist.GetXaxis().SetRangeUser(0, 60)
            hist.Draw()
            drawn=True
        
        if hist.GetMaximum() > y_max: y_max = hist.GetMaximum()

        #canvas.Update()
        mean = hist.GetMean()
        #mean_error = hist.GetMeanError()
        mean_error = hist.GetRMS()
        
        print label, mean

        # find the appropriation "other" noise hist, based on n_strips
        other_noise_hist = noise_hist_many
        if n_strips == 1: other_noise_hist = noise_hist_single
        elif n_strips == 2: other_noise_hist = noise_hist_double

        noise_hist.SetBinContent(bini, mean)
        noise_hist.SetBinError(bini, mean_error)
        other_noise_hist.SetBinContent(bini, mean)
        other_noise_hist.SetBinError(bini, mean_error)

        legend.AddEntry(hist, label, "p")
    hist = rfile.Get("hist_0")
    hist.SetMaximum(y_max*1.1)

    legend.Draw()
    canvas.Update()
    canvas.Print("CombinedNoise.pdf")
    if not ROOT.gROOT.IsBatch():
        print "Holding"
        raw_input("Hold Enter")
    
    print "Plotting noise vs. channel"
    canvas.SetGrid(1,1)
    noise_hist.SetMarkerStyle(20)
    noise_hist_single.SetMarkerStyle(20)
    noise_hist_double.SetMarkerStyle(25)
    noise_hist_many.SetMarkerStyle(21)
    # https://root.cern.ch/root/roottalk/roottalk02/0083.html
    # https://root.cern.ch/root/html534/TH1.html
    noise_hist_many.LabelsOption("v","X") # x-axis labels: vertical 

    noise_hist_many.Draw("E1 X0")
    noise_hist_single.Draw("E1 X0 same")
    noise_hist_double.Draw("E1 X0 same")
    #noise_hist_many.Draw("E1 X0 same")
    canvas.SetTopMargin(0.08)
    canvas.SetBottomMargin(0.15)
    legend2 = ROOT.TLegend(0.1, 1.01 - canvas.GetTopMargin(), 0.9, 0.99)
    legend2.SetNColumns(3)
    legend2.AddEntry(noise_hist_single, "One strip", "p")
    legend2.AddEntry(noise_hist_double, "Two strips", "p")
    legend2.AddEntry(noise_hist_many, "Many strips", "p")
    legend2.Draw()
    canvas.Update()
    canvas.Print("%s.pdf" % plot_name)
    if not ROOT.gROOT.IsBatch():
        print "Noise Plot"
        raw_input("Hold Enter")


if __name__ == "__main__":
    #remake = True
    remake = False
    #calibrate = False
    calibrate = True
    if remake:
        getRMS(calibrate)
    plotRMS(calibrate)


