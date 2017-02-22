#!/usr/bin/env python

import os
import sys
from array import array
import ROOT
ROOT.gROOT.SetBatch(True)

"""
This script draws waveforms from nEXOdigi and prints info about them. 
"""

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


def process_file(filename):

    #-------------------------------------------------------------------------------
    # options:
    #-------------------------------------------------------------------------------

    noise_electrons = 200
    W_value = 40.0
    digitizer_bits = 11
    n_baseline_samples = 100

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
    noise_electrons = array('d', [noise_electrons]) # double
    out_tree.Branch('noise_electrons', noise_electrons, 'noise_electrons/D')

    # W value, keV per electron
    W_value = array('d', [W_value]) # double
    out_tree.Branch('W_value', W_value, 'W_value/D')

    # digitizer_bits
    digitizer_bits = array('I', [digitizer_bits]) # unsigned int
    out_tree.Branch('digitizer_bits', digitizer_bits, 'digitizer_bits/i')

    # n_baseline_samples
    n_baseline_samples = array('I', [n_baseline_samples]) # unsigned int
    out_tree.Branch('n_baseline_samples', n_baseline_samples, 'n_baseline_samples/i')

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


    if not ROOT.gROOT.IsBatch():
        canvas = ROOT.TCanvas("canvas", "")  
        canvas.SetGrid()
        waveformTree.SetLineColor(ROOT.kBlue)
        waveformTree.SetMarkerColor(ROOT.kBlue)
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

        print "entry %i | Evt %i | WFLen %i | WFTileId %i | WFLocalId %i | WFChannelCharge %i" % (
            i_entry, 
            waveformTree.EventNumber,
            waveformTree.WFLen,
            waveformTree.WFTileId,
            waveformTree.WFLocalId,
            waveformTree.WFChannelCharge,
        )

        # reset wfm
        for i_wfm in len(wfm):
            wfm[i_wfm] = 0.0

        # add noise to pretrigger:
        for i_wfm in xrange(n_baseline_samples[0]):
            wfm[i_wfm] = generator.Gaus()*noise_electrons
            

        if not ROOT.gROOT.IsBatch():

            selection = "Entry$==%i" % i_entry
            waveformTree.Draw("WFAmplitude:WFTime",selection,"pl")
            canvas.Update()

            val = raw_input("press enter (q to quit) ") 
            if val == 'q':
                sys.exit()

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
