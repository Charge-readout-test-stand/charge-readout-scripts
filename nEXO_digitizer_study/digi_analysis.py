#!/usr/bin/env python

import os
import sys
from array import array
import ROOT
#ROOT.gROOT.SetBatch(True)

"""
This script draws waveforms from nEXOdigi and prints info about them. 
"""

# import EXO-200 wfm processing classes from offline
# try to load libEXOROOT
if os.getenv("EXOLIB"):
    try:
        print "loading libEXOROOT"
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
    except:
        print "Couldn't load libEXOROOT!"
        sys.exit(1)
else:
    print "set $EXOLIB"
    sys.exit(1)

microsecond = ROOT.CLHEP.microsecond
second = ROOT.CLHEP.second
#microsecond = 1.0e3
#second = 1.0e9

def do_risetime_calc(rise_time_calculator, threshold_percent, wfm, max_val, period):
    """
    Return rise time, in microseconds
    """
    rise_time_calculator.SetFinalThresholdPercentage(threshold_percent)
    rise_time_calculator.SetInitialScanToPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.01) # must be < smallest final threshold crossing
    rise_time_calculator.SetInitialThresholdPercentage(rise_time_calculator.GetFinalThresholdPercentage()-0.02)
    if max_val > 0.0: # throws an alert if max_val is 0
      rise_time_calculator.Transform(wfm, wfm)
    return rise_time_calculator.GetFinalThresholdCrossing()*period/microsecond

def get_risetimes(exo_wfm, wfm_length, sampling_freq_Hz,skip_short_risetimes=True,label=""):
    exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)
    new_wfm = ROOT.EXODoubleWaveform(exo_wfm)
    maw_wfm = ROOT.EXODoubleWaveform(exo_wfm)

    period = exo_wfm.GetSamplingPeriod()

    # perform some smoothing -- be careful because this changes the rise time
    smoother = ROOT.EXOSmoother()
    smoother.SetSmoothSize(5)
    smoother.Transform(exo_wfm, new_wfm) 

    smoothed_max = new_wfm.GetMaxValue()
    max_val = new_wfm.GetMaxValue() # smoothed max
    print "max_val", max_val

    rise_time_calculator = ROOT.EXORisetimeCalculation()
    rise_time_calculator.SetPulsePeakHeight(max_val)
    
    if skip_short_risetimes:
      rise_time_stop10 = 0.0
    else: 
      rise_time_stop10 = do_risetime_calc(rise_time_calculator, 0.10, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop20 = 0.0
    else:
      rise_time_stop20 = do_risetime_calc(rise_time_calculator, 0.20, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop30 = 0.0
    else:
      rise_time_stop30 = do_risetime_calc(rise_time_calculator, 0.30, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop40 = 0.0
    else:
      rise_time_stop40 = do_risetime_calc(rise_time_calculator, 0.40, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop50 = 0.0
    else:
      rise_time_stop50 = do_risetime_calc(rise_time_calculator, 0.50, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop60 = 0.0
    else:
      rise_time_stop60 = do_risetime_calc(rise_time_calculator, 0.60, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop70 = 0.0
    else:
      rise_time_stop70 = do_risetime_calc(rise_time_calculator, 0.70, exo_wfm, max_val, period)

    if skip_short_risetimes:
      rise_time_stop80 = 0.0
    else:
      rise_time_stop80 = do_risetime_calc(rise_time_calculator, 0.80, exo_wfm, max_val, period)

    rise_time_stop90 = do_risetime_calc(rise_time_calculator, 0.90, exo_wfm, max_val, period)
    rise_time_stop95 = do_risetime_calc(rise_time_calculator, 0.95, exo_wfm, max_val, period)

    rise_time_stop99 = do_risetime_calc(rise_time_calculator, 0.99, exo_wfm, max_val, period)

    if not gROOT.IsBatch(): #shows a few rise-times to check
      print "rise times:"
      print "\tmax_val:", max_val
      print "\trise_time_stop50:", rise_time_stop50
      print "\trise_time_stop90:", rise_time_stop90
      print "\trise_time_stop99:", rise_time_stop99
    
    if max_val > 100 and not "PMT" in label and False: do_draw(exo_wfm, "%s after rise-time calc" % label, new_wfm, maw_wfm, vlines=[
      rise_time_stop10,
      rise_time_stop20,
      rise_time_stop30,
      rise_time_stop40,
      rise_time_stop50,
      rise_time_stop60,
      rise_time_stop70,
      rise_time_stop80,
      rise_time_stop90,
      rise_time_stop95,
      rise_time_stop99,
    ])

    maw_wfm.IsA().Destructor(maw_wfm)
    new_wfm.IsA().Destructor(new_wfm)

    return [smoothed_max, rise_time_stop10, rise_time_stop20, rise_time_stop30, rise_time_stop40, rise_time_stop50, rise_time_stop60, rise_time_stop70, rise_time_stop80, rise_time_stop90, rise_time_stop95, rise_time_stop99]



def process_file(filename):

    #-------------------------------------------------------------------------------
    # options:
    #-------------------------------------------------------------------------------

    sampling_freq_Hz = 2e6 # 2 MHz is default
    noise_electrons = 200
    digitizer_bits = 11
    n_baseline_samples = 100
    skip_short_risetimes = False

    keV_per_electron = 500.0/20100
    ADCunits_per_keV = 1.0*pow(2, 11)/5000 

    n_tiles = 172
    n_channels_per_tile = 60
    n_channels = n_tiles*n_channels_per_tile # max number of channels that could be hit in an event

    #-------------------------------------------------------------------------------


    print "--> processing file:", filename
  
    digi_file = ROOT.TFile(filename)
    waveformTree = digi_file.Get("waveformTree")
    evtTree = digi_file.Get("evtTree")
    try:
        n_entries = waveformTree.GetEntries()
        print "%i entries in waveformTree" % n_entries
    except:
        print "couldn't read from waveformTree"
        sys.exit(1)

    basename = os.path.splitext(os.path.basename(filename))[0]
    out_file = ROOT.TFile("proc_%s.root" % basename, "recreate")
    out_tree = ROOT.TTree("tree", "%s processed wfm tree" % basename)
    out_tree.SetLineColor(ROOT.kBlue)
    out_tree.SetLineWidth(2)
    out_tree.SetMarkerColor(ROOT.kRed)
    out_tree.SetMarkerStyle(8)
    out_tree.SetMarkerSize(0.5)

    # event number
    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    # noise, in electrons
    noise_electrons_array = array('d', [noise_electrons]) # double
    out_tree.Branch('noise_electrons', noise_electrons_array, 'noise_electrons/D')

    # W value, keV per electron
    W_value = array('d', [keV_per_electron]) # double
    out_tree.Branch('W_value', W_value, 'W_value/D')

    # digitizer_bits
    digitizer_bits_array = array('I', [digitizer_bits]) # unsigned int
    out_tree.Branch('digitizer_bits', digitizer_bits_array, 'digitizer_bits/i')

    # n_baseline_samples
    n_baseline_samples_array = array('I', [n_baseline_samples]) # unsigned int
    out_tree.Branch('n_baseline_samples', n_baseline_samples_array, 'n_baseline_samples/i')

    # n channels hit
    n_channels_hit = array('I', [0]) # unsigned int
    out_tree.Branch('n_channels_hit', n_channels_hit, 'n_channels_hit/i')

    # hit channel tile IDs
    WFTileId = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('WFTileId',WFTileId, 'WFTileId[n_channels_hit]/i')

    # hit channel strip IDs
    WFLocalId = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('WFLocalId',WFLocalId, 'WFLocalId[n_channels_hit]/i')

    # hit channel charge
    WFChannelCharge = array('d', [0]*n_channels) # double
    out_tree.Branch('WFChannelCharge', WFChannelCharge, 'WFChannelCharge[n_channels_hit]/D')


    rise_time_stop10 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop10', rise_time_stop10, 'rise_time_stop10[n_channels_hit]/D')

    rise_time_stop20 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop20', rise_time_stop20, 'rise_time_stop20[n_channels_hit]/D')

    rise_time_stop30 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop30', rise_time_stop30, 'rise_time_stop30[n_channels_hit]/D')

    rise_time_stop40 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop40', rise_time_stop40, 'rise_time_stop40[n_channels_hit]/D')

    rise_time_stop50 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop50', rise_time_stop50, 'rise_time_stop50[n_channels_hit]/D')

    rise_time_stop60 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop60', rise_time_stop60, 'rise_time_stop60[n_channels_hit]/D')

    rise_time_stop70 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop70', rise_time_stop70, 'rise_time_stop70[n_channels_hit]/D')

    rise_time_stop80 = array('d', [0]*n_channels) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop80', rise_time_stop80, 'rise_time_stop80[n_channels_hit]/D')

    rise_time_stop90 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop90', rise_time_stop90, 'rise_time_stop90[n_channels_hit]/D')

    rise_time_stop95 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop95', rise_time_stop95, 'rise_time_stop95[n_channels_hit]/D')

    rise_time_stop99 = array('d', [0]*n_channels) # double
    out_tree.Branch('rise_time_stop99', rise_time_stop99, 'rise_time_stop99[n_channels_hit]/D')


    if not ROOT.gROOT.IsBatch():
        canvas = ROOT.TCanvas("canvas", "")  
        canvas.SetGrid()
        waveformTree.SetLineColor(ROOT.kRed)
        waveformTree.SetMarkerColor(ROOT.kRed)
        waveformTree.SetMarkerSize(0.8)
        waveformTree.SetMarkerStyle(8)

    # wfm for reuse
    wfm_len = 2000
    wfm = array('d', [0]*wfm_len) # double
    generator = ROOT.TRandom3(0) # random number generator, initialized with TUUID object

    # waveformTree contains one entry per wfm, and can have many entries per
    # event
    processed_event = None # keep track of which event we have processed
    for i_entry in xrange(n_entries):


        print "---> entry %i, event %i" % (i_entry, waveformTree.EventNumber)

        waveformTree.GetEntry(i_entry)

        # check for the start of a new event
        if waveformTree.EventNumber != event[0]:
            print "===> filling tree with event %i" % event[0]
            out_tree.Fill()
            processed_event = event[0]

            # clear variables
            n_channels_hit[0] = 0
            for i_ch in xrange(n_channels):
                WFTileId[i_ch] = 0
                WFLocalId[i_ch] = 0
                WFChannelCharge[i_ch] = 0

        event[0] = waveformTree.EventNumber
        WFTileId[n_channels_hit[0]] = waveformTree.WFTileId
        WFLocalId[n_channels_hit[0]] = waveformTree.WFLocalId
        WFChannelCharge[n_channels_hit[0]] = waveformTree.WFChannelCharge
        n_channels_hit[0] += 1

        nexo_digi_wfm_len = waveformTree.WFLen

        print "entry %i | Evt %i | WFLen %i | WFTileId %i | WFLocalId %i | WFChannelCharge %i" % (
            i_entry, 
            waveformTree.EventNumber,
            waveformTree.WFLen,
            waveformTree.WFTileId,
            waveformTree.WFLocalId,
            waveformTree.WFChannelCharge,
        )

        # reset wfm
        for i_wfm in xrange(len(wfm)):
            wfm[i_wfm] = 0.0

        # fill pretrigger with white noise, in ADC units:
        for i_wfm in xrange(n_baseline_samples):
            noise = generator.Gaus()*noise_electrons
            wfm[i_wfm] = int(noise*keV_per_electron*ADCunits_per_keV) 

        # fill middle of wfm with data from nEXOdigi:
        for i_wfm in xrange(waveformTree.WFLen):
            noise = generator.Gaus()*noise_electrons
            val = noise + waveformTree.WFAmplitude[i_wfm]
            wfm[i_wfm+n_baseline_samples] = int(val*keV_per_electron*ADCunits_per_keV)

            print i_wfm+n_baseline_samples, (i_wfm+n_baseline_samples)/sampling_freq_Hz*second/microsecond, waveformTree.WFAmplitude[i_wfm], val, wfm[i_wfm+n_baseline_samples]

        i_wfm += n_baseline_samples # increment i_wfm


        # grab the final value from the nEXOdigi waveform, in electrons:
        last_val = waveformTree.WFAmplitude[nexo_digi_wfm_len-1]

        # fill the end of the wfm with constant values
        while i_wfm < len(wfm):
            val = last_val + generator.Gaus()*noise_electrons
            wfm[i_wfm] = int(val*keV_per_electron*ADCunits_per_keV) 
            i_wfm += 1
        
        # create an EXODoubleWaveform
        exo_wfm = ROOT.EXODoubleWaveform(wfm, len(wfm))
        exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)

        if not ROOT.gROOT.IsBatch():

            # draw the EXODoubleWaveform:
            hist=exo_wfm.GimmeHist()
            hist.SetMarkerSize(0.8)
            hist.SetMarkerStyle(8)
            hist.SetLineColor(ROOT.kBlue)
            hist.SetMarkerColor(ROOT.kBlue)
            hist.Draw("PL")

            # draw the nEXO digi wfm also
            print "pretrigger [microseconds]: ", n_baseline_samples/sampling_freq_Hz*second/microsecond
            if True:
                selection = "Entry$==%i" % i_entry
                draw_cmd = "WFAmplitude*%f:WFTime+%f" % (
                    keV_per_electron*ADCunits_per_keV,
                    n_baseline_samples/sampling_freq_Hz*second/microsecond,
                )
                print draw_cmd, selection
                waveformTree.Draw(draw_cmd,selection,"pl same")

            canvas.Update()
            val = raw_input("press enter (q to quit) ") 
            if val == 'q': sys.exit()

            # draw the nEXO digi wfm, alone
            if False:
                waveformTree.Draw(draw_cmd,selection,"pl")
                canvas.Update()
                val = raw_input("press enter (q to quit) ") 
                if val == 'q': sys.exit()

            # end test of gROOT.IsBatch()

        # end loop over entries

    if processed_event != event[0]:
        out_tree.Fill()

    out_tree.Write()



if __name__ == "__main__":

    if len(sys.argv) < 2:
      print "arguments: [nEXO MC digi files]"
      sys.exit(1)

    for filename in sys.argv[1:]:
      process_file(filename)
