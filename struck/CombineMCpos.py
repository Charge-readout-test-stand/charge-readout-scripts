import ROOT
import struck_analysis_cuts as scuts
import struck_analysis_parameters as sparams

ROOT.gStyle.SetOptStat(0)

pos1_file = ROOT.TFile("/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/MCData/Bi207MC_realnoise_pos1_10_24_16.root")
pos1_tree = pos1_file.Get("tree")
events_pos1 = pos1_tree.GetEntries()

pos2_file = ROOT.TFile("/nfs/slac/g/exo_data4/users/mjewell/nEXO_MC/MCData/Bi207MC_realnoise_pos2_11_1_16.root")
pos2_tree = pos2_file.Get("tree")
events_pos2 = pos2_tree.GetEntries()

scale=(events_pos1*1.0)/events_pos2
print "Scale=", scale

cut = scuts.get_drift_time_selection(drift_time_high=9.0)
#No isMC means we think there are 50 channels
#print scuts.get_drift_time_selection(isMC=True)
cut = "nsignals==1 && " + cut
print cut

draw_cmd = "SignalEnergy"
bins = 200
Elow = 200
Ehigh = 2000

print "Draw pos1"
hpos1 = ROOT.TH1D("hpos1","hpos1", bins, Elow, Ehigh)
pos1_tree.Draw(draw_cmd+">>hpos1", cut, "goff")
print hpos1.GetEntries()

print "Draw pos2"
hpos2 = ROOT.TH1D("hpos2","hpos2", bins, Elow, Ehigh)
pos2_tree.Draw(draw_cmd+">>hpos2", cut, "goff")
#scale = hpos1.Integral()/hpos2.Integral()
hpos2.Scale(scale)
print hpos2.GetEntries()

print "Sum"
htotal = hpos1.Clone()
htotal.Scale(0.5)
htotal.Add(hpos2,0.5)
htotal.SetLineColor(ROOT.kBlack)
htotal.SetLineWidth(2)

leg = ROOT.TLegend(0.7, 0.7, 0.98, 0.9)
c1=ROOT.TCanvas("c1")
hpos1.SetLineColor(ROOT.kRed)
hpos2.SetLineColor(ROOT.kBlue)
hpos1.SetLineWidth(2)
hpos2.SetLineWidth(2)
leg.AddEntry(hpos1, "Pos1 MC")
leg.AddEntry(hpos2, "Pos2 MC")
leg.AddEntry(htotal, "Summed")
hpos2.Draw()
hpos1.Draw("same")
htotal.Draw("same")
leg.Draw()
c1.Update()

output = ROOT.TFile("CurrentHists.root", "recreate")
hpos1.Write("hpos1")
hpos2.Write("hpos2")
htotal.Write("htotal")
output.Close()

c1.Print("Pos1_vs_Pos2.pdf")
raw_input()



