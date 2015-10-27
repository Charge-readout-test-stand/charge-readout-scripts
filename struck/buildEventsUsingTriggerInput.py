#!/usr/bin/env python

"""
This script builds events, assuming that the trigger input is used. These are
the channels we used for 5th LXe:

0: X26
1: X27
2: X29
3: Y23
4: Y24
8: PMT

argument(s): [sis tier 1 root file(s)]
"""

import os
import sys
import glob
import time
import math
from array import array

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TTree
from ROOT import TLegend
from ROOT import gStyle


gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       

# a placeholder to get different colors in the legend
hists = []
for i in xrange(16):
    hist = TH1D("hist%i" % i,"", 1, 0, 1)
    hist.SetLineWidth(2)
    hists.append(hist)


def get_entry_number(i_event, buffer_lengths, i_channel, n_channels):
      """
      This function calculates which ttree entry corresponds to a given event
      and channel
      """
      #print "--> finding buffer for event %i, ch %i" % (i_event, i_channel)

      # find which buffer spill this event is in:
      remainder = i_event
      prev_buffer_lengths = 0
      for (n_buffer, buffer_length)  in enumerate(buffer_lengths):
          new_remainder = remainder - buffer_length
          #print "\t\t event %i | buffer %i (%i events) " % (i_event, n_buffer, buffer_length)
          if new_remainder < 0: break
          prev_buffer_lengths += buffer_length
          remainder = new_remainder
          
          
      i_entry = remainder + buffer_length*i_channel + prev_buffer_lengths*n_channels
      #print "\t event %i | entry %i | buffer %i" % (i_event, i_entry, n_buffer)
      return int(i_entry)


def draw_event(tree, i_event, buffer_lengths, n_channels):
    """
    draw the event, for debugging
    """

    print "==> drawing event ", i_event

    # set up a canvas
    canvas = TCanvas("c1","")
    canvas.SetLogy(0)
    canvas.SetGrid(1,1)

    legend = TLegend(0.1, 0.91, 0.9, 0.97)
    legend.SetNColumns(6)

    # find the min and max adc values in this event
    event_max = 0
    event_min = pow(2, 14) # 14-bit digitizer

    # set up a "frame hist" to define the axes for drawing wfms
    tree.SetLineWidth(2)
    frame_hist = TH1D("frame_hist", "", 100, 0, 1000)
    frame_hist.SetLineWidth(2)
    frame_hist.SetXTitle("time [clock ticks]")
    #frame_hist.SetYTitle("ADC value")
    frame_hist.SetMinimum(tree.GetMinimum("adc_min")-10)
    frame_hist.SetMaximum(tree.GetMaximum("adc_max")+10) 
    #frame_hist.SetMinimum(0)
    #frame_hist.SetMaximum(16384) # 2^14
    frame_hist.Draw()

    colors = [TColor.kRed, TColor.kBlue+1, TColor.kGreen+2, TColor.kViolet,
    TColor.kOrange, TColor.kBlack] 

    # loop over all tree entries for this timestamp
    for i in xrange(5):
        i_entry =get_entry_number(i_event, buffer_lengths, i, n_channels)
        tree.GetEntry(i_entry)
        channel = tree.channel

        print "\t stamp %s | entry %i | channel %i" % ( tree.timestamp, i_entry, channel)

        color = colors[i % len(colors)]
        tree.SetLineColor(color)
        hists[i].SetLineColor(color)
        hists[i].SetFillColor(color)
        legend.AddEntry(hists[channel], "ch %i" % (channel), "f")
        tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry,"l same")
        #tree.Draw("wfm:Iteration$+%i" % tsl,"Entry$==%i" % i_entry,"l same")
        if tree.adc_max > event_max: event_max = tree.adc_max
        if tree.adc_min < event_min: event_min = tree.adc_min


    frame_hist.SetMinimum(event_min-100)
    frame_hist.SetMaximum(event_max+100) 
    legend.Draw()
    canvas.Update()

    # pause
    val = raw_input("enter to continue (q=quit, b=batch, p=print) ")
    #print val
    if (val == 'q' or val == 'Q'): sys.exit(1) 
    if val == 'b': return False
    if val == 'p': canvas.Print("event_%i_%s.png" % (i_event, basename,))
    return True
    # end of drawing


def process_file(filename):
    """
    process a tier 1 root file to produce a new (reduced) file with event info. 
    """

    freq_Hz = 25.0*1e6 # clock frequency
    n_channels = 6 # from 5th LXs

    do_draw = True
    #do_draw = False
    if gROOT.IsBatch(): do_draw = False

    print "---> processing file: ", filename
    # construct a basename to form output file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]


    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    n_events = n_entries / n_channels
    print "%i entries, %i events" % (n_entries, n_events)

    # loop over tree to determine length of buffer spills
    # note that this changed throughout the runs during 5th LXe...
    print "--> finding lengths of buffer spills"
    buffer_length = 0
    tree.GetEntry(0)
    first_channel = tree.channel
    i_entry = 0
    buffer_lengths = []
    sum_of_previous_buffers = 0
    while i_entry < n_entries:
        tree.GetEntry(i_entry)
        if tree.channel != first_channel:
            buffer_length = i_entry - sum_of_previous_buffers
            print "\t spill %i: %i" % (len(buffer_lengths),  buffer_length)
            buffer_lengths.append(buffer_length)
            sum_of_previous_buffers += buffer_length*n_channels
            i_entry = sum_of_previous_buffers
        i_entry += 1
    print "... done"


    # open a new file for output
    out_file = TFile("%s_events.root" % basename, "recreate")
    out_tree = TTree("tree","events from Struck 3316-DT")

    # make branches in the output tree, using horrible python syntax
    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    time_stamp = array('d', [0]) # double
    out_tree.Branch('time_stamp', time_stamp, 'time_stamp/D')

    totalEnergy = array('d', [0]) # double
    out_tree.Branch('totalEnergy', totalEnergy, 'totalEnergy/D')

    chargeEnergy = array('d', [0]) # double
    out_tree.Branch('chargeEnergy', chargeEnergy, 'chargeEnergy/D')

    lightEnergy = array('d', [0]) # double
    out_tree.Branch('lightEnergy', lightEnergy, 'lightEnergy/D')

    energy = array('d', [0]*6) # double
    out_tree.Branch('energy', energy, 'energy[6]/D')

    channel = array('d', [0]*6) # double
    out_tree.Branch('channel', channel, 'channel[6]/D')


    # keep track of start time, since this script takes forever
    last_time = time.clock()
    reporting_period = 500

    # find & build events
    for i_event in xrange(n_events):

        # periodic progress output
        if i_event % reporting_period == 0:
            now = time.clock()
            print "==> event %i of %i (%.2f percent, %i events in %.1f seconds)" % (
                i_event,
                n_events, 
                100.0*i_event/n_events,
                reporting_period,
                now - last_time,
            )
            last_time = now

        # check that this event doesn't extend past the end of the tree
        if get_entry_number(i_event, buffer_lengths, 5, n_channels) > n_entries:
            print "event %i with (entry %i) is beyond end of tree (%i entries)" % (
                i_event, i_event + buffer_length*n_channels, n_entries)
            break 

        # initialize values
        totalEnergy[0] = 0.0
        chargeEnergy[0] = 0.0
        event[0] = i_event

        # loop over all channels in this event:
        for i in xrange(n_channels):
            i_entry = get_entry_number(i_event, buffer_lengths, i, n_channels)

            tree.GetEntry(i_entry)

            #print "\t stamp %i | entry %i | channel %i" % ( tree.timestampDouble, i_entry, tree.channel)

            if i == 0: time_stamp[0] = tree.timestampDouble

            # check that all wfms in this event have the same timestamp
            if tree.timestampDouble != time_stamp[0]:
                print "==> event %i | entry %i | channel %i timestamp doesn't match!! (%i vs %i)" % (
                i_event, i_entry, tree.channel, time_stamp[0], tree.timestampDouble)
                return

            # get values that are written to tree
            channel[i] = tree.channel
            energy[i] = tree.adc_max - tree.wfm[0]
            totalEnergy[0] += energy[i]
            if i < 5:
                chargeEnergy[0] += energy[i]

        lightEnergy[0] = energy[5]
        out_tree.Fill()

        # draw the event, if needed:
        if do_draw:
            do_draw = draw_event(tree, i_event, buffer_lengths, n_channels)


    print "writing file..."
    out_file.Write()
    out_file.Close()
    print "\t done"

    
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)

