
import sys
import ROOT

# relative paths from this directory:
conti_filename = "ContiIonization.root"
#struck_filename = "../llnl/overnight8thLXe_v6.root"
struck_filename = "~/scratch/mc_slac/red_overnight8thLXe_v6.root" # alexis
if len(sys.argv) > 1:
    struck_filename = sys.argv[1]

# convert Conti TE to keV:
conti_calibration = 1.0/22.004*0.74
conti_draw_cmd = "counts:TE*%.6f" % conti_calibration

integral_start = 450.0
integral_stop = 700.0
integral2_start = 950.0
integral2_stop = 1250.0

# grab Conti tree
conti_file = ROOT.TFile(conti_filename)
conti_tree = conti_file.Get("tree")
print "%i entries in conti tree" % conti_tree.GetEntries()

# conti data is two branches: TE(thermal electrons), counts
# find counts in 570-keV peak:
conti_integral = 0.0
n_points = 0
conti_integral2 = 0.0
n_points2 = 0
for i_entry in xrange(conti_tree.GetEntries()):
    conti_tree.GetEntry(i_entry)
    energy = conti_tree.TE*conti_calibration
    conti_counts = conti_tree.counts
    if energy >= integral_start and energy <= integral_stop:
        conti_integral += conti_counts
        n_points += 1
    if energy >= integral2_start and energy <= integral2_stop:
        conti_integral2 += conti_counts
        n_points2 += 1
conti_integral = conti_integral/n_points*(integral_stop-integral_start) 
conti_integral2 = conti_integral2/n_points2*(integral2_stop-integral2_start) 

# get struck tree
struck_file = ROOT.TFile(struck_filename)
struck_tree = struck_file.Get("tree")
print struck_filename
print "%i entries in struck tree" % struck_tree.GetEntries()

# set up canvas
canvas = ROOT.TCanvas("canvas","")
canvas.SetGrid()

# draw only the conti spectrum first:
#conti_tree.Draw(conti_draw_cmd,"","pl")
#canvas.Update()
#raw_input("enter to continue... ")

# make a selection for cuts to Struck data
selection = [] 
selection.append("rise_time_stop95_sum-8>8.0")
selection.append("rise_time_stop95_sum-8<9.0")
#selection.append("rise_time_stop50_sum-8>7.5")
selection = "&&".join(selection)

# make & fill struck hist
struck_hist = ROOT.TH1D("data","",280, 0, 1400)
struck_hist.GetDirectory().cd()
struck_hist.SetLineColor(ROOT.kBlue)
struck_hist.GetXaxis().SetTitle("Energy [keV]")
struck_hist.GetYaxis().SetTitle("Counts / %.1f keV" % struck_hist.GetBinWidth(1))
struck_hist.GetYaxis().SetTitleOffset(1.3)
struck_hist.SetLineWidth(2)
print "reduced struck_tree cuts:", struck_tree.GetTitle()
print "\nhist selection:", selection
print "filling hist..."
struck_tree.Draw(
    "SignalEnergy >> %s" % struck_hist.GetName(), 
    selection,
    "goff")
print "done filling hist."
print "%i entries in hist" % struck_hist.GetEntries()


struck_integral = struck_hist.Integral(
    struck_hist.FindBin(integral_start),
    struck_hist.FindBin(integral_stop))
struck_integral2 = struck_hist.Integral(
    struck_hist.FindBin(integral2_start),
    struck_hist.FindBin(integral2_stop))
struck_counts = struck_hist.GetBinContent(struck_hist.FindBin(570))
#scale_factor = conti_counts*1.0/struck_counts # for normalizing struck to conti
#hist.Scale(scale_factor)
#scale_factor = struck_counts*1.0/conti_counts # for normalizing conti 

print "struck_integral:", struck_integral
print "conti_integral:", conti_integral

scale_factor = struck_integral*1.0/conti_integral*struck_hist.GetBinWidth(1)
scale_factor = struck_integral2*1.0/conti_integral2*struck_hist.GetBinWidth(1)

legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
legend.SetNColumns(2)
legend.AddEntry(conti_tree, "Conti paper", "lp")
legend.AddEntry(struck_hist, "8th LXe", "l")

y_max = struck_hist.GetMaximum()
struck_hist.SetMaximum(y_max*1.1)

struck_hist.Draw("hist")
conti_tree.Draw("counts*%.6f:TE*%.6f" % (scale_factor, conti_calibration),"","same lp")
legend.Draw()
canvas.Update()
canvas.Print("8thLXe_vs_Conti.pdf")

box = ROOT.TBox(integral_start, 0.0, integral_stop, struck_hist.GetMaximum())
box.SetLineWidth(1)
box.SetLineColor(ROOT.kViolet+1)
box.SetFillColor(ROOT.kViolet+1)
box.SetFillStyle(3004)
legend.AddEntry(box, "Struck/Conti: %.2f" % (struck_integral/(conti_integral*scale_factor/struck_hist.GetBinWidth(1))),"f")


box2 = ROOT.TBox(integral2_start, 0.0, integral2_stop, struck_hist.GetMaximum())
box2.SetLineWidth(1)
box2.SetLineColor(ROOT.kViolet)
box2.SetFillColor(ROOT.kViolet)
box2.SetFillStyle(3004)
legend.AddEntry(box2, "Struck/Conti: %.2f" % (struck_integral2/(conti_integral2*scale_factor/struck_hist.GetBinWidth(1))),"f")


struck_hist.Draw("hist")
legend.Draw()
box.Draw("lf")
box2.Draw("lf")
conti_tree.Draw("counts*%.6f:TE*%.6f" % (scale_factor, conti_calibration),"","same lp")
struck_hist.Draw("same")
canvas.Update()
canvas.Print("8thLXe_vs_Conti_with_integrals.pdf")
raw_input("enter to continue... ")
