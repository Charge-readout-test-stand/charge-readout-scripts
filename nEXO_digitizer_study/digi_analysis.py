#!/usr/bin/env python

import os
import sys
import math
from array import array
from optparse import OptionParser

import ROOT
ROOT.gROOT.SetBatch(True)

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

    if not ROOT.gROOT.IsBatch(): #shows a few rise-times to check
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



def process_file(
    filename,
    noise_electrons=200.0,
    digitizer_bits = 11,
):
    noise_electrons = float(noise_electrons)
    digitizer_bits = int(digitizer_bits)

    #-------------------------------------------------------------------------------
    # options:
    #-------------------------------------------------------------------------------

    #pretrigger_delay_microseconds = 50
    skip_short_risetimes = False
    n_baseline_samples = 100

    keV_per_electron = 500.0/20100
    ADCunits_per_keV = 1.0*pow(2, digitizer_bits)/5000 

    n_tiles = 172
    n_channels_per_tile = 60
    n_channels = n_tiles*n_channels_per_tile # max number of channels that could be hit in an event

    #-------------------------------------------------------------------------------


    print "--> processing file:", filename
    print "\t noise_electrons:", noise_electrons
    print "\t digitizer_bits:", digitizer_bits
  
    digi_file = ROOT.TFile(filename)
    waveformTree = digi_file.Get("waveformTree")
    evtTree = digi_file.Get("evtTree")
    try:
        n_entries = evtTree.GetEntries()
        print "%i entries in evtTree" % n_entries
        n_entries = waveformTree.GetEntries()
        print "%i entries in waveformTree" % n_entries
    except:
        print "couldn't read from waveformTree"
        return

    if n_entries == 0: sys.exit()
    evtTree.GetEntry(0)
    sampling_interval_seconds = evtTree.SamplingInterval/second
    sampling_freq_Hz = 1.0/sampling_interval_seconds 
    #n_baseline_samples = pretrigger_delay_microseconds/(evtTree.SamplingInterval/microsecond)
    wfm_len = int(1000.0/(evtTree.SamplingInterval/microsecond)) # 1000 microsecond wfm

    basename = os.path.splitext(os.path.basename(filename))[0]
    basename = "proc_%iMHz_%ibits_%iPT_%ie_%s" % (
        sampling_freq_Hz/1e6,
        digitizer_bits,
        n_baseline_samples, # pre-trigger
        noise_electrons,
        basename,

    )
    out_file_name = "%s.root" % basename
    if os.path.isfile(out_file_name):
        print "%s already exists" % out_file_name
        return
    out_file = ROOT.TFile(out_file_name, "recreate")
    out_tree = ROOT.TTree("tree", "%s processed wfm tree" % basename)
    out_tree.SetLineColor(ROOT.kBlue)
    out_tree.SetLineWidth(2)
    out_tree.SetMarkerColor(ROOT.kRed)
    out_tree.SetMarkerStyle(8)
    out_tree.SetMarkerSize(0.5)

    #-------------------------------------------------------------------------------
    # event-level stuff from MC
    #-------------------------------------------------------------------------------

    # event number
    event = array('I', [0]) # unsigned int
    out_tree.Branch('EventNumber', event, 'EventNumber/i')

    # energy
    energy = array('d', [0]) # double
    out_tree.Branch('Energy', energy, 'Energy/D')

    # Primary event coords: GenX, GenY, GenZ
    GenX = array('d', [0]) # double
    out_tree.Branch('GenX', GenX, 'GenX/D')
    GenY = array('d', [0]) # double
    out_tree.Branch('GenY', GenY, 'GenY/D')
    GenZ = array('d', [0]) # double
    out_tree.Branch('GenZ', GenZ, 'GenZ/D')

    # sum of WFChannelCharge
    ChannelChargeSum = array('d', [0]) # double
    out_tree.Branch('ChannelChargeSum', ChannelChargeSum, 'ChannelChargeSum/D')

    # NumChannels, from MC
    NumChannels = array('I', [0]) # unsigned int
    out_tree.Branch('NumChannels', NumChannels, 'NumChannels/i')


    """
    *** event-level stuff example

    root [2] evtTree->Show(0)
    ======> EVENT:0
     EventNumber     = 0
     Energy          = 2.4578
     GenX            = -138.617
     GenY            = -163.914
     GenZ            = 182.2
     InitNumOP       = 661
     NumChannels     = 7
     xTile           = -144, -144, -144, -144, -144, -144, -144
     yTile           = -144, -144, -144, -144, -144, -144, -144
     XPosition       = -144, -141, -138, -144, -135, -144, -144
     YPosition       = -168, -144, -144, -165, -144, -162, -159
     ChannelLocalId  = 40, 17, 18, 41, 19, 42, 43
     ChannelCharge   = 1, 10729, 50750, 23827, 1, 17402, 4
     ChannelTime     = 26250, 29250, 29250, 28750, 26250, 29250, 29250
     ChannelNTE      = 1, 10729, 50750, 23827, 1, 17402, 4
     ChannelNoiseTag = 0, 0, 0, 0, 0, 0, 0
     SamplingInterval = 500
     NumCC           = 0
     ssEnergy        = 0
     msEnergy        = 0

    *** wfm-level stuff example:

    root [3] waveformTree->Show(0)
    ======> EVENT:0
     EventNumber     = 0
     WFLen           = 57
     WFTileId        = 63
     WFLocalId       = 40
     WFChannelCharge = 1
     WFAmplitude     = 0, 
                      17.7889, 36.3261, 55.6532, 75.813, 96.854, 
                      118.825, 141.781, 165.778, 190.879, 217.151, 
                      244.666, 273.5, 303.737, 335.468, 368.789, 
                      403.811, 440.642, 479.413, 520.257
     WFTime          = 0, 
                      0.5, 1, 1.5, 2, 2.5, 
                      3, 3.5, 4, 4.5, 5, 
                      5.5, 6, 6.5, 7, 7.5, 
                      8, 8.5, 9, 9.5
    """

    #-------------------------------------------------------------------------------
    # processing pars
    #-------------------------------------------------------------------------------

    # noise, in electrons
    noise_electrons_array = array('d', [noise_electrons]) # double
    out_tree.Branch('noise_electrons', noise_electrons_array, 'noise_electrons/D')

    # W value, keV per electron
    W_value = array('d', [keV_per_electron]) # double
    out_tree.Branch('W_value', W_value, 'W_value/D')

    # ADCunits_per_keV
    ADCunits_per_keV_array = array('d', [ADCunits_per_keV]) # double
    out_tree.Branch('ADCunits_per_keV', ADCunits_per_keV_array, 'ADCunits_per_keV/D')

    # sampling_freq_Hz
    sampling_freq_Hz_array = array('d', [sampling_freq_Hz]) # double
    out_tree.Branch('sampling_freq_Hz', sampling_freq_Hz_array, 'sampling_freq_Hz/D')

    # digitizer_bits
    digitizer_bits_array = array('I', [digitizer_bits]) # unsigned int
    out_tree.Branch('digitizer_bits', digitizer_bits_array, 'digitizer_bits/i')

    # n_baseline_samples
    n_baseline_samples_array = array('I', [n_baseline_samples]) # unsigned int
    out_tree.Branch('n_baseline_samples', n_baseline_samples_array, 'n_baseline_samples/i')

    #-------------------------------------------------------------------------------
    # wfm-level stuff from MC
    #-------------------------------------------------------------------------------

    # this is only kind of from MC, since these get incremented if there are noise triggers
    # no noise triggers yet, so this is just NumChannels

    # n channels hit
    # this is the same as NumChannels for now, but should be different later
    # when false triggers are added
    n_channels_hit = array('I', [0]) # unsigned int
    out_tree.Branch('n_channels_hit', n_channels_hit, 'n_channels_hit/i')


    #-------------------------------------------------------------------------------
    # these four wfm-level things are from evtTree:

    # xTile
    xTile = array('d', [0]*n_channels) # double
    out_tree.Branch('xTile', xTile, 'xTile[n_channels_hit]/D')

    # yTile
    yTile = array('d', [0]*n_channels) # double
    out_tree.Branch('yTile', yTile, 'yTile[n_channels_hit]/D')

    # XPosition
    XPosition = array('d', [0]*n_channels) # double
    out_tree.Branch('XPosition', XPosition, 'XPosition[n_channels_hit]/D')

    # YPosition
    YPosition = array('d', [0]*n_channels) # double
    out_tree.Branch('YPosition', YPosition, 'YPosition[n_channels_hit]/D')

    # end of wfm-level stuff in evtTree
    #-------------------------------------------------------------------------------

    # hit channel tile IDs
    WFTileId = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('WFTileId',WFTileId, 'WFTileId[n_channels_hit]/i')

    # hit channel strip IDs
    WFLocalId = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('WFLocalId',WFLocalId, 'WFLocalId[n_channels_hit]/i')

    # hit channel charge
    WFChannelCharge = array('d', [0]*n_channels) # double
    out_tree.Branch('WFChannelCharge', WFChannelCharge, 'WFChannelCharge[n_channels_hit]/D')

    # is_hit_MC: whether channel was truly hit in MC
    is_hit_MC = array('I', [0]*n_channels) # unsigned int
    out_tree.Branch('is_hit_MC', is_hit_MC, 'is_hit_MC[n_channels_hit]/i')


    #-------------------------------------------------------------------------------
    # calculated stuff
    #-------------------------------------------------------------------------------

    # SignalEnergy
    SignalEnergy = array('d', [0]) # double
    out_tree.Branch('SignalEnergy', SignalEnergy, 'SignalEnergy/D')

    # ChEnergy: channel energy, contribution to SignalEnergy
    ChEnergy = array('d', [0]*n_channels) # double
    out_tree.Branch('ChEnergy', ChEnergy, 'ChEnergy[n_channels_hit]/D')

    # whether a channel was found to be hit
    signal_map = array('I', [0]*n_channels) 
    out_tree.Branch('signal_map', signal_map, 'signal_map[n_channels_hit]/i') 
    
    # number of channels hit
    nsignals = array('I', [0])
    out_tree.Branch('nsignals', nsignals, 'nsignals/i') #Total Signals above threshold

    smoothed_max = array('d', [0]) # double
    out_tree.Branch('smoothed_max', smoothed_max, 'smoothed_max/D')

    # rise times -- these are only calculated for sum wfm
    rise_time_stop10 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop10', rise_time_stop10, 'rise_time_stop10/D')

    rise_time_stop20 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop20', rise_time_stop20, 'rise_time_stop20/D')

    rise_time_stop30 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop30', rise_time_stop30, 'rise_time_stop30/D')

    rise_time_stop40 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop40', rise_time_stop40, 'rise_time_stop40/D')

    rise_time_stop50 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop50', rise_time_stop50, 'rise_time_stop50/D')

    rise_time_stop60 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop60', rise_time_stop60, 'rise_time_stop60/D')

    rise_time_stop70 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop70', rise_time_stop70, 'rise_time_stop70/D')

    rise_time_stop80 = array('d', [0]) # double
    if not skip_short_risetimes:
        out_tree.Branch('rise_time_stop80', rise_time_stop80, 'rise_time_stop80/D')

    rise_time_stop90 = array('d', [0]) # double
    out_tree.Branch('rise_time_stop90', rise_time_stop90, 'rise_time_stop90/D')

    rise_time_stop95 = array('d', [0]) # double
    out_tree.Branch('rise_time_stop95', rise_time_stop95, 'rise_time_stop95/D')

    rise_time_stop99 = array('d', [0]) # double
    out_tree.Branch('rise_time_stop99', rise_time_stop99, 'rise_time_stop99/D')


    if not ROOT.gROOT.IsBatch():
        canvas = ROOT.TCanvas("canvas", "")  
        canvas.SetGrid()
        waveformTree.SetLineColor(ROOT.kRed)
        waveformTree.SetMarkerColor(ROOT.kRed)
        waveformTree.SetMarkerSize(0.8)
        waveformTree.SetMarkerStyle(8)

    # wfm for reuse
    wfm = array('d', [0]*wfm_len) # double
    generator = ROOT.TRandom3(0) # random number generator, initialized with TUUID object

    processed_event = None # keep track of which event we have processed

    # waveformTree contains one entry per wfm, and can have many entries per
    # event, evtTree contains one entry per event
    i_entry = 0
    for i_event in xrange(evtTree.GetEntries()):

        evtTree.GetEntry(i_event)
        print "---> event %i, %i channels" % (i_event, evtTree.NumChannels)

        # clear/reset event-level info from MC
        event[0] = evtTree.EventNumber
        energy[0] = evtTree.Energy
        GenX[0] = evtTree.GenX
        GenY[0] = evtTree.GenY
        GenZ[0] = evtTree.GenZ
        NumChannels[0] = evtTree.NumChannels
        SignalEnergy[0] = 0.0
        ChannelChargeSum[0] = 0.0
        nsignals[0] = 0
        sum_wfm = None
        smoothed_max[0] = 0.0
        rise_time_stop10[0] = 0.0
        rise_time_stop20[0] = 0.0
        rise_time_stop30[0] = 0.0
        rise_time_stop40[0] = 0.0
        rise_time_stop50[0] = 0.0
        rise_time_stop60[0] = 0.0
        rise_time_stop70[0] = 0.0
        rise_time_stop80[0] = 0.0
        rise_time_stop90[0] = 0.0
        rise_time_stop95[0] = 0.0
        rise_time_stop99[0] = 0.0

        if not ROOT.gROOT.IsBatch():
            print "GenX: %.2f | GenY: %.2f | GenZ: %.2f" % (
                GenX[0],
                GenY[0],
                GenZ[0],
            )

        # clear wfm-level variables, loop over all possible elements
        n_channels_hit[0] = 0
        for i_ch in xrange(n_channels):

            WFTileId[i_ch] = 0
            WFLocalId[i_ch] = 0
            WFChannelCharge[i_ch] = 0.0
            ChEnergy[i_ch] = 0.0
            signal_map[i_ch] = 0

        # loop over waveformTree
        for i_channel in xrange(NumChannels[0]):

            # fill evtTree info
            xTile[i_channel] = evtTree.xTile[i_channel]
            yTile[i_channel] = evtTree.yTile[i_channel]
            XPosition[i_channel] = evtTree.XPosition[i_channel]
            YPosition[i_channel] = evtTree.YPosition[i_channel]
            is_hit_MC[i_channel] = 1

            #print "event %i, wfm entry %i" % (i_event, i_entry)
            waveformTree.GetEntry(i_entry)

            if waveformTree.EventNumber != evtTree.EventNumber:
                print "events don't match!!"
                sys.exit(1)
            if waveformTree.WFChannelCharge != evtTree.ChannelCharge[n_channels_hit[0]]:
                print "WFChannelCharge doesn't match!!"
                sys.exit(1)

            WFTileId[n_channels_hit[0]] = waveformTree.WFTileId
            WFLocalId[n_channels_hit[0]] = waveformTree.WFLocalId
            WFChannelCharge[n_channels_hit[0]] = waveformTree.WFChannelCharge
            ChannelChargeSum[0] += waveformTree.WFChannelCharge
            n_channels_hit[0] += 1

            nexo_digi_wfm_len = waveformTree.WFLen

            # reset wfm
            for i_wfm in xrange(len(wfm)):
                wfm[i_wfm] = 0.0

            # fill pretrigger with white noise, in ADC units:
            for i_wfm in xrange(n_baseline_samples):
                noise = generator.Gaus()*noise_electrons
                wfm[i_wfm] = int(noise*keV_per_electron*ADCunits_per_keV)*1.0/ADCunits_per_keV 

            # fill middle of wfm with data from nEXOdigi:
            for i_wfm in xrange(waveformTree.WFLen):
                noise = generator.Gaus()*noise_electrons
                val = noise + waveformTree.WFAmplitude[i_wfm]
                wfm[i_wfm+n_baseline_samples] = int(val*keV_per_electron*ADCunits_per_keV)*1.0/ADCunits_per_keV

                #print i_wfm+n_baseline_samples, (i_wfm+n_baseline_samples)/sampling_freq_Hz*second/microsecond, waveformTree.WFAmplitude[i_wfm], val, wfm[i_wfm+n_baseline_samples]

            i_wfm += n_baseline_samples # increment i_wfm


            # grab the final value from the nEXOdigi waveform, in electrons:
            # I don't understand why some wfms are length 0!
            #print nexo_digi_wfm_len
            #print len(waveformTree.WFAmplitude)
            last_val = 0.0
            if nexo_digi_wfm_len > 0:
                last_val = waveformTree.WFAmplitude[nexo_digi_wfm_len-1]

            # fill the end of the wfm with constant values
            while i_wfm < len(wfm):
                val = last_val + generator.Gaus()*noise_electrons
                wfm[i_wfm] = int(val*keV_per_electron*ADCunits_per_keV)*1.0/ADCunits_per_keV
                i_wfm += 1
            
            # create an EXODoubleWaveform
            exo_wfm = ROOT.EXODoubleWaveform(wfm, len(wfm))
            exo_wfm.SetSamplingFreq(sampling_freq_Hz/second)

            # new_wfm, for energy calcs
            new_wfm = ROOT.EXODoubleWaveform(exo_wfm)

            baseline_remover = ROOT.EXOBaselineRemover()
            baseline_remover.SetBaselineSamples(n_baseline_samples)
            baseline_remover.SetStartSample(0)
            baseline_remover.Transform(new_wfm)
            baseline_rms = baseline_remover.GetBaselineRMS()

            baseline_remover.SetStartSample(len(wfm)-n_baseline_samples-1)
            baseline_remover.Transform(new_wfm)
            energy_val = baseline_remover.GetBaselineMean()
            energy_rms = baseline_remover.GetBaselineRMS()

            n_ch = n_channels_hit[0]-1
            ChEnergy[n_ch] = energy_val

            if energy_val > 5.0*energy_rms*math.sqrt(2.0/n_baseline_samples):
                signal_map[n_ch] = 1
                SignalEnergy[0] += energy_val
                nsignals[0] += 1
                if sum_wfm is None:
                    sum_wfm = ROOT.EXODoubleWaveform(exo_wfm)
                else:
                    sum_wfm += exo_wfm


            if not ROOT.gROOT.IsBatch():
                #print "entry %i | Evt %i | WFLen %i | WFTileId %i | WFLocalId %i | WFChannelCharge %i | energy %i" % (
                print "entry %i | WFTileId %i | WFLocalId %i | energy %.1f | %i" % (
                    i_entry, 
                    #waveformTree.EventNumber,
                    #waveformTree.WFLen,
                    waveformTree.WFTileId,
                    waveformTree.WFLocalId,
                    #waveformTree.WFChannelCharge,
                    waveformTree.WFChannelCharge*keV_per_electron,
                    signal_map[n_ch],
                )




            if not ROOT.gROOT.IsBatch():

                # draw the EXODoubleWaveform:
                hist=exo_wfm.GimmeHist("hist%i" % i_channel)
                hist.SetMarkerSize(0.8)
                hist.SetMarkerStyle(8)
                hist.SetLineColor(ROOT.kBlue)
                hist.SetMarkerColor(ROOT.kBlue)
                hist.SetYTitle("Energy [keV]")
                hist.GetYaxis().SetTitleOffset(1.3)
                max_val = evtTree.Energy*1e3
                hist.SetMaximum(max_val*1.05)
                hist.SetTitle("")
                option = "pl"
                if i_channel > 0:
                    option = "pl same"
                hist.Draw(option)

                # draw the nEXO digi wfm also
                #print "pretrigger [microseconds]: ", n_baseline_samples/sampling_freq_Hz*second/microsecond
                if False:
                    selection = "Entry$==%i" % i_entry
                    draw_cmd = "WFAmplitude*%f:WFTime+%f" % (
                        keV_per_electron*ADCunits_per_keV,
                        n_baseline_samples/sampling_freq_Hz*second/microsecond,
                    )
                    print draw_cmd, selection
                    waveformTree.Draw(draw_cmd,selection,"pl same")

                if False:
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

            i_entry += 1
            # end loop over waveformTree

        if not ROOT.gROOT.IsBatch():

            # draw the EXODoubleWaveform:
            hist=sum_wfm.GimmeHist("hist%i" % i_channel)
            hist.SetMarkerSize(0.8)
            hist.SetMarkerStyle(8)
            hist.SetLineColor(ROOT.kRed)
            hist.SetMarkerColor(ROOT.kRed)
            hist.Draw("pl same")
            print "%i strips above threshold" % nsignals[0]

            canvas.Update()
            val = raw_input("press enter (q to quit, p to print) ") 
            if val == 'q': sys.exit()
            if val == 'p': canvas.Print("%s_%i.pdf" % (basename, i_event))


        # calc risetimes from sum_wfm:
        if sum_wfm:
            (
              smoothed_max[0],
              rise_time_stop10[0],
              rise_time_stop20[0],
              rise_time_stop30[0],
              rise_time_stop40[0],
              rise_time_stop50[0],
              rise_time_stop60[0],
              rise_time_stop70[0],
              rise_time_stop80[0],
              rise_time_stop90[0],
              rise_time_stop95[0],
              rise_time_stop99[0],
            ) = get_risetimes(
                exo_wfm=sum_wfm, 
                wfm_length=len(wfm), 
                sampling_freq_Hz=sampling_freq_Hz, 
                skip_short_risetimes=skip_short_risetimes, 
                label="",
            )

        #print "===> filling tree with event %i" % event[0]
        out_tree.Fill()

        # end loop over evtTree

    out_tree.Write()


if __name__ == "__main__":


    parser = OptionParser()

    parser.add_option("-n", dest="noise_electrons", default=200.0,
                      help="noise in electrons")

    parser.add_option("-b", dest="digitizer_bits", default=11,
                      help="digitizer_bits")

    (options, filenames) = parser.parse_args()

    if len(filenames) < 1:
      print "arguments: [nEXO MC digi files]"
      sys.exit(1)


    for i_file, filename in enumerate(filenames):

        print "===> file %i of %i" % (i_file, len(filenames))

        process_file(
            filename=filename,
            noise_electrons=options.noise_electrons,
            digitizer_bits=options.digitizer_bits,
        )

