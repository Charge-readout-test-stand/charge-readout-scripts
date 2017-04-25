"""
Analyze info in pulsed-cathode runs. 
"""

import os
import sys
import glob
import ROOT
ROOT.gROOT.SetBatch(True)

from struck import struck_analysis_parameters

tree = ROOT.TChain("tree")

#filenames = sys.argv[1:]
filenames = glob.glob("/p/lscratchd/alexiss/11th_LXe/2017_02_01_vme_digi/tier3/tier3_SIS3316Raw_2017020*recovery_cathode_pulser*.root")
print filenames.sort()

print "%i files" % len(filenames)

for filename in filenames:
    tree.Add(filename)

n_entries = tree.GetEntries()
print "%i entries in tree" % n_entries
if n_entries == 0: sys.exit(1)

pulser_channel = struck_analysis_parameters.pulser_channel
print "pulser_channel:", pulser_channel

tree.GetEntry(0)
first_time = tree.file_start_time
print "first_time: ", first_time

tree.GetEntry(n_entries-1)
last_time = tree.file_start_time + tree.time_stampDouble*40/1e9
print "last_time: ", last_time

run_duration_hours = (last_time - first_time)/60/60
print "run_duration_hours:", run_duration_hours

draw_string = "energy:(file_start_time-%i+time_stampDouble*40/1e9)/60/60" % (
    first_time,
)

canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid()
canvas.SetLogz(1)


graphs = []


basename = os.path.commonprefix(filenames)
basename = os.path.basename(basename)
print "basename:", basename

plot_name = basename

canvas.Print("%s.pdf[" % plot_name)

calibration_hist = ROOT.TH1D(
    "calibration_hist",
    "pulser response vs. channel",
    64,0,32)

for channel, val  in enumerate(struck_analysis_parameters.charge_channels_to_use):
    
    if val == 0: 
        if channel != pulser_channel: continue
    
    label = struck_analysis_parameters.channel_map[channel]

    print "----> channel %i, %s" % (channel, label)
    selection = "energy[%i]>100 && channel==%i && lightEnergy < 50" % (pulser_channel, channel)

    # find the max -- if this is recovery it happens at the start
    hist = ROOT.TH1D("hist1D_%i" % channel, "", 1000,0,3000)

    tree.Draw(
        "energy[%i] >> %s" % (channel, hist.GetName()),
        selection,
    )
    mean = hist.GetMean() 

    n_x_bins = int(run_duration_hours*10)
    
    hist = ROOT.TH2D("hist_%i" % channel, 
        "%s: channel %i" % (label, channel),
        n_x_bins, 0, run_duration_hours+0.01,
        100, 0, hist.GetMean()*2.0
    )
    hist.SetXTitle("time [hours]")
    hist.SetYTitle("amplitude [keV]")
    hist.GetYaxis().SetTitleOffset(1.3)

    n_drawn = tree.Draw(
        "%s >> %s" % (draw_string, hist.GetName()),
        selection,
        "colz"
    )
    print "\t %i entries drawn" % n_drawn


    x_bin_width = hist.GetXaxis().GetBinWidth(1)
    graph = ROOT.TGraphErrors()
    graph.SetMarkerSize(0.4)
    graph.SetMarkerStyle(20)
    for i_bin in xrange(n_x_bins):
        y_hist = hist.ProjectionY("y_hist", i_bin+1, i_bin+1)
        mean = y_hist.GetMean()
        rms = y_hist.GetRMS()
        bin_center = hist.GetXaxis().GetBinCenter(i_bin+1)
        #print "\t\t mean in %.2f to %.2f: %.2f" % (
        #    bin_center-x_bin_width/2,
        #    bin_center+x_bin_width/2, 
        #    mean)
        graph.SetPoint(i_bin, bin_center, mean)
        graph.SetPointError(i_bin, 0, rms)
    calibration_hist.SetBinContent(calibration_hist.FindBin(channel), mean)
    calibration_hist.SetBinError(calibration_hist.FindBin(channel), rms)

    graph.Draw("pl same")
    graphs.append(graph)
        
    canvas.Update()
    canvas.Print("%s.pdf" % plot_name)

    #if not ROOT.gROOT.IsBatch(): raw_input("any key to continue ")

for i_graph, graph in enumerate(graphs):
    color = struck_analysis_parameters.colors[i_graph]
    graph.SetLineColor(color)
    graph.SetMarkerColor(color)
    graph.SetLineWidth(2)

    # set first point to 1.0
    x = graph.GetX()
    y = graph.GetY()
    y_0 = y[0]
    for i_point in xrange(graph.GetN()):
        #print i_point, x[i_point]
        graph.SetPointError(i_point, 0, graph.GetErrorY(i_point)/y_0)
        graph.SetPoint(i_point, x[i_point], y[i_point]/y_0)

# draw all graphs
frame_hist = graphs[0].GetHistogram()
frame_hist.SetMaximum(1.6)
frame_hist.SetMinimum(0.0)
frame_hist.Draw()
frame_hist.SetTitle("Channel response vs. time")
frame_hist.SetTitle("Amplitude [keV]")
frame_hist.SetTitle("Time [hours]")

for i_graph, graph in enumerate(graphs):
    graph.Draw("pl")

canvas.Update()
canvas.Print("%s.pdf" % plot_name)
if not ROOT.gROOT.IsBatch(): raw_input("any key to continue ")

# plot last points vs. channel
calibration_hist.SetXTitle("channel")
calibration_hist.SetYTitle("amplitude [keV]")
calibration_hist.SetMarkerStyle(20)
calibration_hist.SetMarkerSize(0.8)
calibration_hist.Draw("p")
canvas.Print("%s.pdf" % plot_name)
if not ROOT.gROOT.IsBatch(): raw_input("any key to continue ")

canvas.SetLogy(1)
canvas.Update()
canvas.Print("%s.pdf" % plot_name)

canvas.Print("%s.pdf]" % plot_name)
