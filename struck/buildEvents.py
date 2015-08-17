#!/usr/bin/env python

"""
This script builds events. The following branches are
assumed to exist:
* adc_max
* channel

** this script takes ~30 min to run over a 400MB file!! Check the algorithm -- AGS 16 Aug 2015 

arguments [sis root files]
"""

import os
import sys
import glob
import time
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
    hist.SetLineColor(i+1)
    hist.SetFillColor(i+1)
    hist.SetLineWidth(2)
    hists.append(hist)

def draw_event(tree, entries):

    legend = TLegend(0.1, 0.91, 0.9, 0.97)
    legend.SetNColumns(3)

    # find the min and max adc values in this event
    event_max = 0
    event_min = pow(2, 14) # 14-bit digitizer


    # loop over all timestamps in this event to find max & min
    for stamp in event_time_stamps:
        stamp_entries = entries_of_timestamp[stamp]

        # loop over all tree entries for this timestamp
        for i_entry in stamp_entries:
            tree.GetEntry(i_entry)

            if tree.adc_max > event_max: event_max = tree.adc_max
            if tree.adc_min < event_min: event_min = tree.adc_min

    frame_hist.SetMinimum(event_min-10)
    frame_hist.SetMaximum(event_max+10)
    frame_hist.Draw()


    # loop over all timestamps in this event
    for stamp in event_time_stamps:
        stamp_entries = entries_of_timestamp[stamp]

        # loop over all tree entries for this timestamp
        for i_entry in stamp_entries:
            tree.GetEntry(i_entry)
            channel = tree.channel
            print "\t stamp %s | tsl %i | entry %i | channel %i" % (
                event_time_stamps[0] + tsl,
                tsl,
                i_entry, 
                channel
            )

            tree.SetLineColor(channel+1)
            legend.AddEntry(hists[channel], "ch %i, tsl=%i" % (channel, tsl), "f")
            tree.Draw("wfm:Iteration$","Entry$==%i" % i_entry,"l same")
            #tree.Draw("wfm:Iteration$+%i" % tsl,"Entry$==%i" % i_entry,"l same")
    legend.Draw()
    canvas.Update()

    # pause
    val = raw_input("enter to continue (q=quit, b=batch, p=print) ")
    print val
    if (val == 'q' or val == 'Q'): return 0 
    if val == 'b': do_draw = False
    if val == 'p': canvas.Print("event_%i_%s.png" % (i_event, basename,))
    # end of drawing


def process_file(filename):

    # clock frequency
    freq_Hz = 25.0*1e6

    coincidence_window = 2048 # clock ticks
    coincidence_window = 500 # clock ticks
    coincidence_time = coincidence_window/freq_Hz*1e6
    print "coincidence_time [microseconds]: %.2f" % coincidence_time
    # 2048 is the wfm length?

    calibration = array('d', 3*[0]) # double
    calibration[0] = 570.0/3800.0
    calibration[1] = 570.0/1900.0
    calibration[2] = 570.0/2800.0

    do_draw = True
    #do_draw = False

    print "---> processing file: ", filename
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # keep track of start time, since this script takes forever
    last_time = time.clock()

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()

    # some objects to find time since last and coincident events
    timestamps = []
    entries_of_timestamp = {} # a dictionary of lists of tree entries

    # loop over all tree entries to find timestamps, save a dict of timestamps
    # to tree entry numbers
    print "collecting time stamps from %i entries..." % n_entries
    for i_entry in xrange(n_entries):
    #for i_entry in xrange(20000): # debugging
        
        tree.GetEntry(i_entry)
        energy = (tree.adc_max - 1600)*calibration[tree.channel]

        if energy > 100: # threshold, keV
        #if energy > 0: # threshold, keV

            timestamp = tree.timestamp
            timestamps.append(timestamp)
            try:
                entries_of_timestamp[timestamp]
                #print "timestamp already exists!!"
            except KeyError:
                entries_of_timestamp[timestamp] = []
            entries_of_timestamp[timestamp].append(i_entry)
            #print "timestamp", timestamp, ", entries", entries_of_timestamp[timestamp]

            if False: # debugging
                channel =  tree.channel
                print "entry %i | ch %i | timestamp %i | buffer_no %i | event %i" % (
                    i_entry, 
                    channel, 
                    timestamp,
                    tree.buffer_no,
                    tree.event,
                )

    print "\t done collecting timestamps"

    print "sorting %i timestamps..." % len(timestamps)
    timestamps.sort() # sort in place
    print "\t done sorting"

    # find min and max tsl
    max_tsl = 0
    min_tsl = 1e12
    for i in xrange(len(timestamps)-1):
        tsl = timestamps[i+1] - timestamps[i] 
        if tsl > 1e8: print "big tsl [s]:", tsl/freq_Hz
        if tsl > max_tsl: max_tsl = tsl
        if tsl < min_tsl: min_tsl = tsl
    print "min_tsl [micros]:", min_tsl/freq_Hz*1e6
    print "max_tsl [micros]:", max_tsl/freq_Hz*1e6

    # set up parameters for tsl hist
    n_bins = 160 
    min_bin = 0
    #max_bin = max_tsl/freq_Hz*1e6
    max_bin = 200
    #print "max_tsl = %.3f seconds = %.2f clock ticks" % (max_tsl, max_tsl*freq_Hz)

    # set up hist
    hist = TH1D("hist", "", n_bins, min_bin, max_bin)
    hist.SetLineWidth(2)
    hist.SetLineColor(TColor.kBlue)
    hist.SetFillColor(TColor.kBlue)
    #hist.SetFillStyle(3004)
    hist.SetXTitle("time [microseconds]")

    # fill tsl hist
    for i in xrange(len(timestamps)-1):
        tsl = timestamps[i+1] - timestamps[i] 
        hist.Fill(tsl/freq_Hz*1e6)  

    hist.SetTitle("%i entries" % hist.GetEntries())

    # set up a canvas
    canvas = TCanvas("canvas","")
    canvas.SetLogy(1)
    canvas.SetGrid(1,1)

    # draw
    hist.Draw()
    canvas.Update()
    canvas.Print("tsl_%s.png" % basename)
    #return # debugging

    # set up a "frame hist" to define the axes for drawing wfms
    tree.SetLineWidth(2)
    frame_hist = TH1D("frame_hist", "", 100, 0, 2048)
    frame_hist.SetLineWidth(2)
    frame_hist.SetXTitle("time [clock ticks]")
    #frame_hist.SetYTitle("ADC value")
    frame_hist.SetMinimum(tree.GetMinimum("adc_min")-10)
    frame_hist.SetMaximum(tree.GetMaximum("adc_max")+10) 
    #frame_hist.SetMinimum(0)
    #frame_hist.SetMaximum(16384) # 2^14

    #if len(timestamps) > 1000: return # debugging

    # a new file for output
    out_file = TFile("%s_events.root" % basename, "recreate")
    out_tree = TTree("tree","events from Struck 3316-DT, window=%i" % coincidence_window)

    # make branches in the output tree, using horrible python syntax
    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')

    nHits = array('I', [0]) # unsigned int
    out_tree.Branch('nHits', nHits, 'nHits/i')

    totalEnergy = array('d', [0]) # double
    out_tree.Branch('totalEnergy', totalEnergy, 'totalEnergy/D')

    energy = array('d', 3*[0]) # double
    out_tree.Branch('energy', energy, 'energy[3]/D')

    tsl_val = array('d', 3*[0]) # double
    out_tree.Branch('tsl', tsl_val, 'tsl[3]/D')


    canvas.SetLogy(0)
    tree.SetLineWidth(2)

    # search for any timestamps within the coincidence window
    print "building events..."
    first_time_in_event = timestamps[0]
    event_time_stamps = []
    i_event = 0
    for timestamp in timestamps: 
        tsl = timestamp - first_time_in_event
        #print "timestamp [s]", timestamp/freq_Hz, "tsl [s]:", tsl/freq_Hz
        #print "--> timestamp", timestamp, "tsl:", tsl

        # check whether this is the end of an event:
        if (tsl > coincidence_window):
            #print "==> %i entries in event %i" %  (len(event_time_stamps), i_event)
            if i_event % 1000 == 0: 
                now = time.clock()
                print "this is event %i (1000 events in %.1f seconds)" % (i_event, 
                now - last_time)
                last_time = now

            event[0] = i_event
            energy[0] = 0.0
            energy[1] = 0.0
            energy[2] = 0.0
            totalEnergy[0] = 0.0
            nHits[0] = 0

            event_entry_to_tsl_map = {}

            # loop over all timestamps in this event
            for stamp in event_time_stamps:
                stamp_entries = entries_of_timestamp[stamp]
                #print "\t entries_of_timestamp[", stamp, "]: ", entries_of_timestamp[stamp]


                # if there are duplicate timestamps, we will loop over the ttree
                # entries multiple times!! go back to the map or something

                # loop over all tree entries for this timestamp
                for i_entry in stamp_entries:
                    tsl = stamp - event_time_stamps[0]
                    event_entry_to_tsl_map[i_entry] = tsl

            # now iterate over ttree entries, counting each one once
            for (i_entry, tsl) in event_entry_to_tsl_map.iteritems():
                tree.GetEntry(i_entry)
                channel = tree.channel
                energy[channel] = (tree.adc_max - 1600)*calibration[channel]
                tsl_val[channel] = stamp - event_time_stamps[0]
                totalEnergy[0] = totalEnergy[0] + energy[channel]
                nHits[0] = nHits[0] + 1

            out_tree.Fill()

            if do_draw:
                draw_event(tree, event_time_stamps)
            # get ready for a new event:
            event_time_stamps = [timestamp]
            first_time_in_event = timestamp
            i_event += 1
        else:
            event_time_stamps.append(timestamp)
            #print "\t appended"
        

    print "writing file..."
    out_file.Write()
    print "\t done"

    
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)

    for filename in sys.argv[1:]:
        process_file(filename)

