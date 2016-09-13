import os
import sys
import math
import ROOT
ROOT.gROOT.SetBatch(True)
import struck_analysis_parameters

def process_file(filename):

    basename = os.path.basename(filename)
    print "--> processing file", basename
    basename = os.path.splitext(basename)[0]
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    print "%i entries in tree" % tree.GetEntries()

    hists = []
    canvas = ROOT.TCanvas("canvas","")
    canvas.SetGrid(1,1)
    canvas.SetLogy(0)
    #energy_var = "energy1_pz"
    #energy_var = "energy_pz"
    energy_var = "baseline_rms"

    for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
        if val == 0: 
            print "rms_keV[%i] = 0.0 # not in use" % channel
            continue

        label = struck_analysis_parameters.channel_map[channel]

        hist = ROOT.TH1D("hist_ch%i" % channel,label,500,-100,100)
        hist.GetDirectory().cd()
        tree.Draw(
            "%s >> %s" % (energy_var, hist.GetName()),
            "lightEnergy<6&& channel==%i" % channel)
        #print "%i entries in %s" % (hist.GetEntries(), hist.GetTitle())
        
        calibration = struck_analysis_parameters.calibration_values[channel]
        rms = hist.GetRMS()
        mean = hist.GetMean()
        print "ch:", channel, "mean:", mean*calibration, "rms:", rms*calibration
        energy_rms = rms/math.sqrt(2.0/(2.0*struck_analysis_parameters.n_baseline_samples))
        adc_rms = energy_rms/calibration
        print "channel %i %s | energy1_pz noise %.3f keV | new RMS %.3f keV | old RMS %.3f keV " % (
            channel,
            label,
            rms, 
            energy_rms,
            struck_analysis_parameters.rms_keV[channel]
        )

        print "rms_keV[%i] = %.6f*calibration_values[%i]" % (
            channel,
            adc_rms,
            channel,
        )

        canvas.Update()
        if not ROOT.gROOT.IsBatch(): raw_input("Hold Enter")


if __name__ == "__main__":
    
    filename = "/p/lscratchd/alexiss/2016_08_15_8th_LXe/tier3/tier3_SIS3316Raw_20160816180708_8thLXe_126mvDT_cell_full_cath_1700V_HVOn_Noise_100cg__1-ngm.root"
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    process_file(filename)


