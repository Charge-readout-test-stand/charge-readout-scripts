"""
Draw slow controls data and struck data, aligned in time. 

sample commands from ROOT session
root [2] TTree* tree0 = (TTree*) _file0->Get("tree"); tree0->SetLineColor(kRed)
root [3] TTree* tree1 = (TTree*) _file1->Get("tree"); tree0->SetLineColor(kBlue)
root [4] tree0->Draw("tCuTop:(timeStamp-2082844800)/60.0/60.0-409527.38","","l")
root [5] tree1->Draw("168:(file_start_time+time_stampDouble/sampling_freq_Hz)*1.0/60/60-409527.38","Entry$<12850","same")
"""

import datetime
import ROOT
ROOT.gROOT.SetBatch(True) # debugging

# options, files on Ubuntu DAQ
slow_controls_file_name = "~/Dropbox/022temp/9thLXePlots/test_20160919_082321.root"
#struck_file_name = "~/9th_LXe/overnight_9thLXe_v0.root"
struck_file_name = "~/9th_LXe/no_comp_overnight_9thLXe_v1.root"
channel = 1
struck_variable = "baseline_rms*calibration" # variable to draw from Stuck file

last_struck_entry = 128500 # ~ 15 minutes
#last_struck_entry = 12850 


sc_file = ROOT.TFile(slow_controls_file_name)
sc_tree = sc_file.Get("tree")
print "---> slow controls file:", slow_controls_file_name
print "\t%i entries in slow-controls tree" % sc_tree.GetEntries()

struck_file = ROOT.TFile(struck_file_name)
struck_tree = struck_file.Get("tree")
print "---> struck file:", struck_file_name
print "\t%i entries in struck tree" % struck_tree.GetEntries()


# make a string for drawing LabView slow controls time
labviewTimeOffset = 2082844800 # time, in seconds, to produce posix time stamp
sc_tree.GetEntry(0)
first_time = sc_tree.timeStamp - labviewTimeOffset  # first time in LV file
print "LV first_time:", first_time
start_time = datetime.datetime.fromtimestamp(first_time)
print "\t", start_time.strftime("%m-%d-%y %I:%M:%p")
sc_time_string = "(timeStamp-%i)/60.0/60.0" % (first_time + labviewTimeOffset)
print "sc_time_string:", sc_time_string

# make a string for drawing Struck time
gmt_offset = 7.0 # hours, to PDT
struck_time_string = "(file_start_time+time_stampDouble/sampling_freq_Hz - %i)*1.0/60/60 - %i" % (first_time, gmt_offset)
struck_tree.GetEntry(0)
first_struck_time = struck_tree.file_start_time
struck_tree.GetEntry(last_struck_entry) # ~ 15 minutes
last_struck_time = struck_tree.file_start_time
struck_start_time = datetime.datetime.fromtimestamp(first_struck_time - gmt_offset*60.0*60.0)
print "\t", struck_start_time.strftime("%m-%d-%y %I:%M:%p")
print "struck_time_string:", struck_time_string
print "first_struck_time - first_time - gmt_offset:", (first_struck_time - first_time)/60.0/60.0 - gmt_offset
print "struck time [minutes]:", (last_struck_time - first_struck_time)/60.0

# draw some stuff
canvas = ROOT.TCanvas("canvas","")
canvas.Divide(1,2)

hist_min = (first_struck_time - first_time)/60.0/60.0 - gmt_offset 
hist_max = (last_struck_time - first_time)/60.0/60.0 - gmt_offset

print hist_min, hist_max

pad = canvas.cd(1)
pad.SetGrid()
frame_hist = ROOT.TH1D("frame_hist","",100,hist_min, hist_max)
frame_hist.SetXTitle("Time [hours]")
frame_hist.SetYTitle("Temperature [K]")
frame_hist.SetMinimum(110)
frame_hist.SetMaximum(210)
frame_hist.SetLineWidth(4)
frame_hist.Draw("axis")
frame_hist.Draw("axig same")

legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
legend.SetNColumns(3)

sc_tree.SetLineColor(ROOT.kBlue)
print "slow controls entries: %i" % sc_tree.Draw("(tCuTop-165)*10+165:%s" % sc_time_string, "", "l same")
hist1 = frame_hist.Clone("hist1") 
hist1.SetLineColor(sc_tree.GetLineColor())
legend.AddEntry(hist1, "(tCuTop-165)*10+165")

sc_tree.SetLineColor(ROOT.kRed)
print "slow controls entries: %i" % sc_tree.Draw("tLnFtIn:%s" % sc_time_string, "", "l same")
hist2 = frame_hist.Clone("hist2") 
hist2.SetLineColor(sc_tree.GetLineColor())
legend.AddEntry(hist2, "tLnFtIn")

sc_tree.SetLineColor(ROOT.kViolet)
print "slow controls entries: %i" % sc_tree.Draw("tLnFtOut:%s" % sc_time_string, "", "l same")
hist3 = frame_hist.Clone("hist3") 
hist3.SetLineColor(sc_tree.GetLineColor())
legend.AddEntry(hist3, "tLnFtOut")

legend.Draw()

# just to show which struck times we are using:
#print "struck entries: %i" % struck_tree.Draw("164:%s" % struck_time_string, 
#"Entry$<%i" % last_struck_entry, "same")

pad = canvas.cd(2)
pad.SetGrid()
pad.SetLogz(1)
hist = ROOT.TH2D("hist","",100,hist_min, hist_max, 100, 14, 24)
hist.SetXTitle("Time [hours]")
hist.SetYTitle("Channel %i %s" % (channel, struck_variable))
hist.GetDirectory().cd()
struck_tree.SetLineColor(ROOT.kGreen+3)
struck_tree.SetMarkerColor(ROOT.kGreen+3)
print "struck entries: %i" % struck_tree.Draw(
"%s:%s >> hist" % (struck_variable, struck_time_string), 
"Entry$<%i && channel==%i" % (last_struck_entry, channel), 
"colz")

canvas.Update()
canvas.Print("test.png")
if not ROOT.gROOT.IsBatch(): raw_input("enter to continue ")

