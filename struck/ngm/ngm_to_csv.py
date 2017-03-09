"""
Convert NGM root output to csv file for Angelo Dragone.
02 March 2017 
"""


import os
import sys

import ROOT
ROOT.gROOT.SetBatch(True) # uncomment to draw multi-page PDF

from struck import struck_analysis_parameters


def process_file(filename):
    print "--> processing file", filename
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]

    # open the root file and grab the tree
    root_file = ROOT.TFile(filename)
    tree = root_file.Get("HitTree")
    n_entries = tree.GetEntries()

    # get NGM system config
    sys_config = root_file.Get("NGMSystemConfiguration")
    card0 = sys_config.GetSlotParameters().GetParValueO("card",0)
    card1 = sys_config.GetSlotParameters().GetParValueO("card",1)

    sampling_freq_Hz = struck_analysis_parameters.get_clock_frequency_Hz_ngm(card0.clock_source_choice)
    print "sampling_freq_Hz: %.1f MHz" % (sampling_freq_Hz/1e6)

    trigger_time = card0.pretriggerdelay_block[0]/sampling_freq_Hz*1e6
    print "trigger time: [microseconds]", trigger_time

    # set up a canvas
    canvas = ROOT.TCanvas("canvas","", 1000, 800)
    canvas.SetGrid(1,1)
    canvas.SetLeftMargin(0.12)
    canvas.SetTopMargin(0.15)
    canvas.SetBottomMargin(0.12)

    n_channels = len(struck_analysis_parameters.channel_map)
    print "%i channels" % n_channels

    # loop over tree:
    for i_entry in xrange(n_entries):
        tree.GetEntry(i_entry)

        event = i_entry/n_channels

        # decided on some events using drawNGM:
        if event != 5 and event != 61: continue

        slot = tree.HitTree.GetSlot()
        card_channel = tree.HitTree.GetChannel() # 0 to 16 for each card
        channel = card_channel + 16*slot # 0 to 31
        calibration = struck_analysis_parameters.calibration_values[channel]

        graph = tree.HitTree.GetGraph()
        n_points = graph.GetN()
        energy = 0
        n_samples = 100
        for i in xrange(n_samples):
            point1 = graph.GetY()[i]
            point2 = graph.GetY()[n_points-1-i]
            energy += point2-point1
        energy /= n_samples
        energy *= calibration

        print "--> event %i, entry %i: channel %i, energy: %.1f" % (
            i_entry/32,
            i_entry,
            channel,
            energy,
        )

        if energy < 15: continue

        label = struck_analysis_parameters.channel_map[channel]
        graph.SetTitle("entry %i: event %i, ch %i, %s, %i keV" % (i_entry, event, channel, label, energy))
        graph.SetLineColor(ROOT.kBlue+1)
        graph.GetXaxis().SetTitle("sample (at %i MS/s)" % (sampling_freq_Hz/1e6))
        graph.GetYaxis().SetTitleOffset(1.3)
        graph.GetYaxis().SetTitle("ADC units")
        graph.Draw("al")
        canvas.Update()

        csv_file_name = "event%i_channel%i.txt" % (event, channel)
        print "csv_file_name:", csv_file_name
        
        val = 'p'
        if not ROOT.gROOT.IsBatch():
            val = raw_input("enter to continue (q: quit, p: draw & write) ")
            if val == "q": sys.exit()
        if val == 'p':
            canvas.Print("%s_entry%i_ch%i.pdf" % (basename, i_entry, channel))
            csv_file = open(csv_file_name, 'w')
            for i in xrange(graph.GetN()):
                x = graph.GetX()[i]
                y = graph.GetY()[i]
                line = "%i, %i" % (x, y)
                print line
                csv_file.write(line + '\n')
            csv_file.close()
            # end loop over graph points



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [NGM tier 1 root files]"
        sys.exit()

    for filename in sys.argv[1:]:
        process_file(filename)


