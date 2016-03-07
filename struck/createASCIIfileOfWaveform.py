

"""
create an ascii file with the contents of one waverorm, from a tier 2 file

for Ralph, 09 Jan 2016

column 1: time (nanoseconds)
column 2: ADC value (14-bit digitizer)
"""


import os
import sys

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TGraph
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TLegend
from ROOT import gStyle

import struck_analysis_parameters

gROOT.SetStyle("Plain")     
gStyle.SetOptStat(0)        
gStyle.SetPalette(1)        
gStyle.SetTitleStyle(0)     
gStyle.SetTitleBorderSize(0)       



def process_file(event, channel, filename):

    print "processing file: ", filename
    print "event:", event

    sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz
    sampling_period_ns = 1e9/sampling_freq_Hz
    print sampling_period_ns
    
    channels = struck_analysis_parameters.channels
    channel_map = struck_analysis_parameters.channel_map
    print "channel:", channel, channel_map[channel]
    channel_index = channels.index(channel)

    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")
    n_entries = tree.GetEntries()
    print "%i entries" % n_entries

    tree.GetEntry(event)
    graph = TGraph()
    color = struck_analysis_parameters.get_colors()[channel]
    graph.SetLineColor(color)
    graph.SetLineWidth(2)

    if channel_index == 0: wfm = tree.wfm0
    if channel_index == 1: wfm = tree.wfm1
    if channel_index == 2: wfm = tree.wfm2
    if channel_index == 3: wfm = tree.wfm3
    if channel_index == 4: wfm = tree.wfm4

    n_samples = len(wfm)

    output_name = "%s_event%i_channel%i" % (
        basename,
        event,
        channel,
    )

    output_file = file("%s.txt" % output_name, 'w')

    for i_sample in xrange(n_samples):

        time_stamp = sampling_period_ns*i_sample
        value = wfm[i_sample]
        print i_sample, "time_stamp: %i | value: %i" % (time_stamp, value)

        graph.SetPoint(
            graph.GetN(),
            time_stamp,
            value,
        )

        output_file.write("%i\t%i\n" % (time_stamp, value))

    output_file.close()

    canvas = TCanvas("canvas","")
    canvas.SetGrid(1,1)
    graph.Draw("al")
    graph.SetTitle("channel %i, event %i" % (channel, event))
    graph.GetXaxis().SetTitle("time [ns]")
    graph.GetYaxis().SetTitle("ADC value")
    graph.GetYaxis().SetTitleOffset(1.2)
    canvas.Update()
    canvas.Print("%s.pdf" % output_name)
    raw_input("--> any key to continue")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [event] [channel] [tier2 root file]"
        sys.exit(1)


    event = int(sys.argv[1])
    channel =int( sys.argv[2])
    filename = sys.argv[3]
    process_file(event, channel, filename)





