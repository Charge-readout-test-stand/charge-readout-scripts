
import sys
import os
import ROOT
ROOT.gROOT.SetBatch(True)

filenames = sys.argv[1:]

basename = os.path.commonprefix(filenames)
basename = os.path.basename(basename)
basename = os.path.splitext(basename)[0]
print basename


max_bin = 600
peak_loc = 150
selection = "wfm_max_time>675 && wfm_max_time<685" # direct to shaper
if "sig_chain" in basename:
    print "this is the usual sig_chain!"
    selection = "wfm_max_time>630 && wfm_max_time<638" # full sig chain
    max_bin = 16000
    peak_loc = 1000 # ~ location of spe


# pulser is ch1 in Struck gui data
tree = ROOT.TChain("tree1")

print "--> adding files to chain"
for filename in filenames:
    print "\t %s" % filename
    tree.Add(filename)
    #break # debugging
print "--> added %i files \n" % len(filenames)

# turn off most branches
tree.SetBranchStatus("*",0)
tree.SetBranchStatus("wfm_max",1)
tree.SetBranchStatus("wfm_max_time",1)
tree.SetBranchStatus("wfm",1)

out_file = ROOT.TFile("hists_%s.root" % basename,"recreate")

# make a hist
hist = ROOT.TH1D("hist","",200,0,max_bin)
hist.SetLineColor(ROOT.kBlue)
if "no_sig" in basename:
    hist.SetLineColor(ROOT.kRed)
hist.SetLineWidth(2)
hist.SetYTitle("Counts / %.1f" % hist.GetBinWidth(1))
hist.SetXTitle("ADC units")
#hist.SetXTitle("mV at digitizer input")

adc_range = pow(2,14)-1 # 14-bit ADC
#draw_cmd = "(wfm_max-Sum$(wfm*(Iteration$<550))/550.0)*2500/%i >> hist" % adc_range
draw_cmd = "(wfm_max-Sum$(wfm*(Iteration$<550))/550.0) >> hist"

print "Drawing hist..."
tree.Draw(draw_cmd, selection, "goff")

title = "%i files, %.2e entries | %s {%s}" % (
    len(filenames), 
    hist.GetEntries(),
    draw_cmd,
    selection,
)
hist.SetTitle(title)
print title


#-------------------------------------------------------------------------------
# wfm max times
#-------------------------------------------------------------------------------


wfm_len = 1060
max_time_hist = ROOT.TH1D("max_time_hist","",wfm_len,0,wfm_len)
max_time_hist.SetLineColor(ROOT.kGreen+2)
max_time_hist.SetLineWidth(2)

n_drawn = tree.Draw("wfm_max_time >> max_time_hist","", "goff")
print "%i drawn into max_time_hist" % n_drawn


#-------------------------------------------------------------------------------
# canvas
#-------------------------------------------------------------------------------

canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid()
canvas.SetLogy(1)

#-------------------------------------------------------------------------------
# draw max_time_hist
#-------------------------------------------------------------------------------

max_time_hist.Draw()
canvas.Update()
canvas.Print("%s_max_time_log.pdf" % basename)
canvas.SetLogy(0)
canvas.Print("%s_max_time_lin.pdf" % basename)
max_time_hist.SetAxisRange(580,680)
canvas.Print("%s_max_time_zoom.pdf" % basename)
max_time_hist.SetAxisRange(0,wfm_len) # reset axis

#-------------------------------------------------------------------------------
# draw SPE hist
#-------------------------------------------------------------------------------

hist.Draw()
canvas.SetLogy(1)
canvas.Print("%s_log.pdf" % basename)

peak_val = hist.GetBinContent(hist.FindBin(peak_loc))
print "peak loc:", peak_loc
print "peak val:", peak_val

canvas.SetLogy(0)
canvas.Update()
canvas.Print("%s_lin.pdf" % basename)
old_max = hist.GetMaximum()
hist.SetMaximum(peak_val*1.1)
hist.Draw()
canvas.Update()
canvas.Print("%s_lin_zoom.pdf" % basename)
hist.SetMaximum(old_max)

hist.Write()
max_time_hist.Write()

