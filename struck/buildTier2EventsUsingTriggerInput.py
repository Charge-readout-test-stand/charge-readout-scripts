#!/usr/bin/env python

"""

FIXME to rely on struck analysis parameters!!!

This script builds events, assuming that the trigger input is used. 

argument(s): [sis tier 1 root file(s)]

These are the channels we used for 5th LXe:

0: X26
1: X27
2: X29
3: Y23
4: Y24
8: PMT

processed 5th LXe files w/o the buffer method. Some runs took a long time :

tier2_LXe_Run1_0VC_SupplyOff_1200VPMT_1039AM_X26_X27_Y23_Shaped_Amplified_1670mVDT_0
still not done after 13 hours

tier2_LXe_Run1_1700VC_1200VPMT_0134AM_NotShaped_Amplified_403mVDT_1
still not done after 13 hours

tier2_LXe_Run1_0VC_SupplyOff_1200VPMT_1015AM_X26_X27_Y23_Shaped_Amplified_1670mVDT_0
47617 seconds = 13.2 hours


"""

import os
import sys
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

import struck_analysis_parameters


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
      #print "\t event %i | ch %i | entry %i | buffer %i" % (i_event, i_channel, i_entry, n_buffer)
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
    frame_hist.SetMinimum(tree.GetMinimum("wfm_min")-10)
    frame_hist.SetMaximum(tree.GetMaximum("wfm_max")+10) 
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
        if tree.wfm_max > event_max: event_max = tree.wfm_max
        if tree.wfm_min < event_min: event_min = tree.wfm_min


    frame_hist.SetMinimum(event_min-100)
    frame_hist.SetMaximum(event_max+100) 
    legend.Draw()
    canvas.Update()

    # pause
    val = raw_input("enter to continue (q=quit, b=batch, p=print) ")
    #print val
    if (val == 'q' or val == 'Q'): sys.exit(1) 
    if val == 'b': gROOT.SetBatch(True)
    if val == 'p': canvas.Print("event_%i_%s.png" % (i_event, basename,))
    # end of drawing


def get_basename(filename):

    # construct a basename to form output file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    basename = "tier2_" + "_".join(basename.split("_")[1:])
    return basename




def process_file(filename):
    """
    process a tier 1 root file to produce a new (reduced) file with event info. 
    """

    # whether to use method that assumes channels write out info in same-length
    # buffer spills
    use_buffer_method = False # 3 5th LXe files take a long time; ~400MB memory used
    #use_buffer_method = True

    # keep track of start time, since this script takes forever
    start_time = time.clock()

    freq_Hz = struck_analysis_parameters.sampling_freq_Hz
    #n_channels = 6 # from 5th LXs
    channels = struck_analysis_parameters.channels
    n_channels = len(channels)

    print "---> processing file: ", filename
    basename = get_basename(filename)


    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    n_events = n_entries / n_channels
    print "%i entries, %i events" % (n_entries, n_events)


    if not use_buffer_method:
        # some objects to find time since last and coincident events
        entries_of_timestamp = {} # a dictionary mapping timestamps to lists of tree entries

        # loop over all tree entries to find timestamps, save a dict of timestamps
        # to tree entry numbers
        print "collecting time stamps from %i entries..." % n_entries
        for i_entry in xrange(n_entries):
            
            #if i_entry > 1000: break # debugging
            
            tree.GetEntry(i_entry)

            timestamp = tree.timestamp

            channel = tree.channel

            try:
                entries_of_timestamp[timestamp]
                #print "timestamp already exists!!"
            except KeyError:
                entries_of_timestamp[timestamp] = []
            entries_of_timestamp[timestamp].append(i_entry)
            if len(entries_of_timestamp[timestamp]) > len(channels):
                print "WARNING: more than %i entries with timestamp" % (
                    len(channels), 
                    timestamp,
                )

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

        timestamps = entries_of_timestamp.keys()
        print "sorting %i timestamps..." % len(timestamps)
        timestamps.sort() # sort in place
        print "\t done sorting"



    if use_buffer_method:
        # loop over tree to determine length of buffer spills
        # note that this changed throughout the runs during 5th LXe...
        print "--> finding lengths of buffer spills"
        buffer_length = 0
        tree.GetEntry(0)
        first_channel = tree.channel
        i_entry = 0
        buffer_lengths = []
        #buffer_starts = {}
        #buffer_ends = {}
        #prev_channel =-1
        sum_of_previous_buffers = 0
        while i_entry < n_entries:
            tree.GetEntry(i_entry)

            # identify start/end of buffer spill
            #if tree.channel != prev_channel:

                # buffer start and stop method
                #if i_entry > 0:
                #    print "ch %i end at entry %i (%i entries)" % (
                #        prev_channel, i_entry-1,
                #        i_entry -buffer_starts[prev_channel][-1],
                #        )
                #    try:
                #        buffer_ends[tree.channel].append(i_entry-1)
                #    except KeyError:
                #        buffer_ends[tree.channel] = []
                #        buffer_ends[tree.channel].append(i_entry-1)

                #print "ch %i start at entry %i" % (tree.channel, i_entry)
                #try:
                #    buffer_starts[tree.channel].append(i_entry)
                #except KeyError:
                #    buffer_starts[tree.channel] = []
                #    buffer_starts[tree.channel].append(i_entry)
                #prev_channel = tree.channel
                    
            # fill list of buffer lengths 
            if tree.channel != first_channel:
                buffer_length = i_entry - sum_of_previous_buffers
                print "\t spill %i: %i events, entries %i to %i" % (
                    len(buffer_lengths),  
                    buffer_length,
                    sum_of_previous_buffers,
                    sum_of_previous_buffers + buffer_length*n_channels,
                )
                buffer_lengths.append(buffer_length)
                sum_of_previous_buffers += buffer_length*n_channels
                i_entry = sum_of_previous_buffers

            i_entry += 1
        #print "ch %i end at entry %i" % (prev_channel, i_entry-1)
        buffer_ends[tree.channel].append(i_entry-1)
        print "... done"


    # open a new file for output
    out_file = TFile("%s.root" % basename, "recreate")
    out_tree = TTree("tree","events from Struck 3316-DT")

    # make branches in the output tree, using horrible python syntax
    event = array('I', [0]) # unsigned int
    out_tree.Branch('event', event, 'event/i')
 
    entry = array('I', [0]) # unsigned int
    out_tree.Branch('entry', entry, 'entry/i')
 
    channel = array('I', [0]*6) # unsigned int
    out_tree.Branch('channel', channel, 'channel[6]/i')

    time_stamp = array('L', [0]) # unsigned long
    out_tree.Branch('time_stamp', time_stamp, 'time_stamp/l')

    time_stampDouble = array('d', [0]) # double
    out_tree.Branch('time_stampDouble', time_stampDouble, 'time_stampDouble/D')

    totalEnergy = array('d', [0]) # double
    out_tree.Branch('totalEnergy', totalEnergy, 'totalEnergy/D')

    chargeEnergy = array('d', [0]) # double
    out_tree.Branch('chargeEnergy', chargeEnergy, 'chargeEnergy/D')

    lightEnergy = array('d', [0]) # double
    out_tree.Branch('lightEnergy', lightEnergy, 'lightEnergy/D')

    energy = array('d', [0]*6) # double
    out_tree.Branch('energy', energy, 'energy[6]/D')

    maw_max = array('I', [0]*6) # unsigned int
    out_tree.Branch('maw_max', maw_max, 'maw_max[6]/i')

    wfm_max_time = array('I', [0]*6) # unsigned int
    out_tree.Branch('wfm_max_time', wfm_max_time, 'wfm_max_time[6]/i')

    wfm_max = array('I', [0]*6) # unsigned int
    out_tree.Branch('wfm_max', wfm_max, 'wfm_max[6]/i')

    wfm_length = array('I', [0]) # unsigned int
    out_tree.Branch('wfm_length', wfm_length, 'wfm_length/i')

    maw_length = array('I', [0]) # unsigned int
    out_tree.Branch('maw_length', maw_length, 'maw_length/i')

    channels = [0,1,2,3,4,8]
    waveforms = []
    maws = []

    for i_channel in channels:

        wfm = array('I', [0]*2048) # unsigned int
        out_tree.Branch('wfm%i' % i_channel, wfm, 'wfm%i[wfm_length]/i' % i_channel)
        waveforms.append(wfm)

        maw = array('i', [0]*2048) # signed int
        out_tree.Branch('maw%i' % i_channel, maw, 'maw%i[maw_length]/I' % i_channel)
        maws.append(maw)


    do_debug = False
    #do_debug = True
    
    reporting_period = 500 
    if do_debug:
        reporting_period = 1

    cache_size = 200*1024*1024 # 200 MB
    tree.SetCacheSize(cache_size)
    print "cache size: %.2e (%.2e MB)" % (
        tree.GetCacheSize(),
        tree.GetCacheSize()/1024/1024,
    )

    now = time.clock()
    print "%.1f seconds spent preprocessing" % (now - start_time)
    last_time = now


    # find & build events
    # -------------------------------------------------------

    # buffer spill method

    entry[0] = 0 
    # timestamp sorted list method
    for i_event in xrange(n_events):

        if do_debug:
            if i_event > 1000: break

        # periodic progress output
        if i_event % reporting_period == 0:
            now = time.clock()
            print "==> event %i of %i (%.2f percent, %i events in %.1f seconds, %.2f seconds elapsed)" % (
                i_event,
                n_events, 
                100.0*i_event/n_events,
                reporting_period,
                now - last_time,
                now - start_time,
            )
            last_time = now

        if not use_buffer_method:
            i_timestamp = timestamps[i_event]

        # initialize values
        totalEnergy[0] = 0.0
        chargeEnergy[0] = 0.0
        event[0] = i_event

        is_data_missing = False

        # loop over all channels in this event:
        for i in xrange(n_channels):

            if use_buffer_method:
                i_entry = get_entry_number(i_event, buffer_lengths, i, n_channels)

            else:
                # use big list of timestamps:
                try:
                    i_entry = entries_of_timestamp[i_timestamp][i]
                except IndexError:
                    print "WARNING: entry %i | missing data from timestamp %i (only info from %i channels)" % (
                      i_entry, i_timestamp, len(entries_of_timestamp[i_timestamp]))
                    is_data_missing = True
                    break

            tree.GetEntry(i_entry)

            #print "\t stamp %i | entry %i | channel %i" % ( tree.timestampDouble, i_entry, tree.channel)

            # fill out some values for the output tree
            if i == 0: 
                time_stamp[0] = tree.timestamp
                time_stampDouble[0] = tree.timestampDouble
                wfm_length[0] = tree.wfm_length
                maw_length[0] = tree.maw_length

            if tree.timestamp != time_stamp[0]:
                print "WARNING: Problem with timestamps!! "


            if use_buffer_method:
                # check that all wfms in this event have the same timestamp
                search_limit = 10 # maximum number of different entries to test...
                i_search = 0
                while tree.timestamp != time_stamp[0]:

                    print "==> event %i | entry %i | channel %i timestamp doesn't match!! (%i vs %i)" % (
                    i_event, i_entry, tree.channel, time_stamp[0], tree.timestamp)
                    difference = tree.timestamp - time_stamp[0]
                    print "difference (this ch timestamp - 0th ch timestamp): ", tree.timestamp - time_stamp[0]
                    if difference > 0:
                        i_entry -= 1
                    else:
                        i_entry += 1
                    print "trying new entry:", i_entry
                    val = tree.GetEntry(i_entry)
                    print val

                    i_search += 1
                    if i_search > search_limit: 
                        print "WARNING: tried %i new events -- giving up!!" % i_search
                        return

            # fill out values that are written to tree
            channel[i] = tree.channel
            wfm_max_time[i] = tree.wfm_max_time
            wfm_max[i] = tree.wfm_max
            energy[i] = tree.wfm_max - tree.wfm[0]
            maw_max[i] = tree.maw_max
            totalEnergy[0] += energy[i]

            # fill the wfm for this channel:
            wfm = waveforms[i]
            for i_sample in xrange(tree.wfm_length):
                wfm[i_sample] = tree.wfm[i_sample]
                #print i_sample, wfm[i_sample]

            maw = maws[i]
            for i_sample in xrange(tree.maw_length):
                maw[i_sample] = tree.maw[i_sample]

            # add up charge channels, skip PMT
            if tree.channel != 8:
                chargeEnergy[0] += energy[i]

        lightEnergy[0] = energy[5]

        # draw the event, if needed:
        if not gROOT.IsBatch():
            draw_event(tree, i_event, buffer_lengths, n_channels)

        if not is_data_missing:
            out_tree.Fill()
            entry[0] += 1


    print "writing file %s.root..." % basename
    out_file.Write()
    out_file.Close()
    print "\t done"

    
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)


    for filename in sys.argv[1:]:
        process_file(filename)

