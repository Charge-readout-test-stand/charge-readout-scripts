import ROOT
import struck_analysis_parameters
import os
ROOT.gROOT.SetBatch(True)

def getDecayTimes():
    
    filename = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/overnight8thLXe_v3.root"
    tree = ROOT.TChain("tree")
    tree.Add(filename)

    basename = os.path.splitext(os.path.basename(filename))[0]
    print "basename:", basename

    plot_name = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/DecayTime_%s.pdf" % basename

    canvas = ROOT.TCanvas("canvas")
    canvas.SetTopMargin(0.15)
    canvas.SetGrid()
    canvas.Print("%s[" % plot_name) # open multi-page canvas

    n_bins = 500
    decay_max = 3000.0 #max energy

    fitter = 1  #0=gaus, 1=landau
    if fitter < 0.5: 
        #For the Gaussian don't need the tail
        decay_max = 700.0
        n_bins = 200

    landau = ROOT.TF1("landau","[0]*TMath::Landau(x,[1],[2],0)", 0, decay_max)
    mygaus   = ROOT.TF1("mygaus", "[0]*TMath::Exp(-0.5*((x-[1])/[2])^2)", 0, decay_max)

    decay_log = open('/home/teststand/2016_08_15_8th_LXe_overnight/tier3_added/decay_log_%s.txt' % basename, 'w')

    decay_log.write("# Fits are in %s \n" % plot_name)
    for (channel, value) in enumerate(struck_analysis_parameters.charge_channels_to_use):
        
        if not value:
            log_out =  "decay_time_values[%i] =  %f*microsecond # %s  \n" %(channel, 1.0e10, "Not Used")
            decay_log.write(log_out)
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
        if fitter < 0.5:
            #If Gaus try to cut bad fits
            selection = "decay_error[%i]/decay_fit[%i] < 0.015" % (channel, channel)
        print "--> drawing..."
        n_drawn = tree.Draw(draw_cmd, selection)
        print "%i drawn" % n_drawn
        
        mean = -999
        mean_error = -999

        if fitter > 0.5:
            landau.SetParameter(1, hist.GetBinCenter(hist.GetMaximumBin()))
            landau.SetParameter(2, 150)
            landau.SetParameter(0, hist.GetMaximum())
            fit_result = hist.Fit("landau", "QWBRS")
            mean = landau.GetParameter(1)
            mean_error = landau.GetParError(1)
        else:
            mygaus.SetParameter(1, hist.GetBinCenter(hist.GetMaximumBin())) #mean
            mygaus.SetParameter(0, hist.GetMaximum()) #amplitude
            mygaus.SetParameter(2, 150) #sigma
            fit_result = hist.Fit("mygaus", "QWBRS")
            mean = mygaus.GetParameter(1)
            mean_error = mygaus.GetParError(1)
        log_out =  "decay_time_values[%i] =  %f*microsecond # +/- %f  \n" %(channel, mean, mean_error)
        print log_out
        decay_log.write(log_out)

        label = struck_analysis_parameters.channel_map[channel]
        title = "ch %i: %s | %.2e counts | %s | #tau = %f #pm %f" % (channel, label, n_drawn, selection, mean, mean_error)
        hist.SetTitle(title)

        canvas.SetLogy(0)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        if not ROOT.gROOT.IsBatch(): 
            raw_input()

        canvas.SetLogy(1)
        canvas.Update()
        canvas.Print("%s" % plot_name)
        if not ROOT.gROOT.IsBatch(): 
            raw_input()

    canvas.Print("%s]" % plot_name) # close multi-page canvas


if __name__ == "__main__":

    getDecayTimes()


