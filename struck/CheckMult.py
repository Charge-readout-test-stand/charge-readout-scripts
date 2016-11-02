import ROOT


tier3_file = "/nfs/slac/g/exo_data4/users/mjewell//../alexis4/test-stand/2016_03_07_7thLXe/tier3_external/overnight.root"

tfile = ROOT.TFile(tier3_file)

tree= tfile.Get("tree")


c1 = ROOT.TCanvas()


legend = ROOT.TLegend(0.1, 0.86, 0.9, 0.99)
legend.SetNColumns(3)
color_list = [ROOT.kRed, ROOT.kOrange, ROOT.kBlue, ROOT.kGreen, ROOT.kMagenta, ROOT.kBlack, ROOT.kCyan]

hist_list = []
thresh_holds = [0,20,100, 200, 300, 400, 500]
for i,thresh in enumerate(thresh_holds):
    cut = "((energy1_pz[0] >%f) + (energy1_pz[1] >%f) + (energy1_pz[2] >%f) + (energy1_pz[3] >%f) + (energy1_pz[4] >%f) + (energy1_pz[5] >%f) + (energy1_pz[6] >%f) + (energy1_pz[7] >%f)) > 1" % (thresh, thresh,thresh, thresh, thresh, thresh,thresh, thresh)

    draw_cmd = "chargeEnergy>>h%i(1000,0,4000)" % thresh
    tree.Draw(draw_cmd,cut,"goff")
    hist = ROOT.gDirectory.Get("h"+str(thresh))
    hist.SetDirectory(0)
    hist.SetLineColor(color_list[i])
    hist_list.append(hist)
    legend.AddEntry(hist, ("thresh%i" % thresh))
    if i == 0: 
        hist.SetTitle("")
        hist.GetXaxis().SetTitle("chargeEnergy")
        hist.Draw()
    else: hist.Draw("same")

legend.Draw()
#c1.SetLogy()
c1.Update()
raw_input()

legend2 = ROOT.TLegend(0.1, 0.86, 0.9, 0.99)
legend2.SetNColumns(3)
nhits = [1,2,3,4,5]
thresh = 200
for i,hit in enumerate(nhits):
    cut = "((energy1_pz[0] >%f) + (energy1_pz[1] >%f) + (energy1_pz[2] >%f) + (energy1_pz[3] >%f) + (energy1_pz[4] >%f) + (energy1_pz[5] >%f) + (energy1_pz[6] >%f) + (energy1_pz[7] >%f)) > %i" % (thresh, thresh, thresh, thresh, thresh, thresh, thresh, thresh, hit)

    draw_cmd = "chargeEnergy>>n%i(1000,0,4000)" % hit
    
    tree.Draw(draw_cmd, cut,"goff")
    hist = ROOT.gDirectory.Get("n"+str(hit))
    
    print "nhits = ", hit, "entries = ", hist.GetEntries()
    
    hist.SetDirectory(0)
    hist.SetLineColor(color_list[i])
    legend2.AddEntry(hist, ("hits%i" % hit))
    if i == 0:
        hist.SetTitle("")
        hist.GetXaxis().SetTitle("chargeEnergy")
        hist.Draw()
    else: hist.Draw("same")
legend2.Draw()
c1.SetLogy()
c1.Update()

raw_input()

