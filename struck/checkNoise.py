import ROOT

rgb_json = \
    [[255,122,158],
    [224,0,81],
    [156,37,45],
    [255,175,155],
    [248,91,48],
    [143,71,0],
    [216,112,0],
    [247,186,123],
    [255,179,87],
    [109,76,36],
    [130,100,0],
    [191,165,0],
    [180,172,116],
    [141,138,0],
    [202,205,59],
    [165,214,79],
    [91,141,0],
    [65,90,28],
    [114,215,74],
    [71,216,93],
    [153,212,156],
    [0,146,57],
    [1,196,172],
    [1,86,157],
    [2,119,235],
    [107,109,248],
    [150,72,207],
    [215,147,255],
    [146,15,146],
    [118,64,104],
    [255,143,203],
    [194,0,116]]

colors = []
color = ROOT.TColor()
for i_color, rgb in enumerate(rgb_json):
    val =  color.GetColor(rgb[0], rgb[1], rgb[2])
    #print i_color, rgb, val
    colors.append(val)


#tfile = ROOT.TFile("tier3_SIS3316Raw_20160921080244_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root")

tfile = ROOT.TFile("/p/lscratchd/jewell6/MCData_9thLXe/NoiseFiles/noiselib/NoiseLib_9thLXe.root")

c1 = ROOT.TCanvas("c1")

tree = tfile.Get("tree")

events = tree.GetEntries()

print "Events in File = ", events

for evi in xrange(events):
    tree.GetEntry(evi)
    evn = tree.event
    holder = ROOT.TH1D('holder','holder',2,0,800)
    holder.SetBinContent(1,9000)
    holder.SetBinContent(2,3000)
    holder.SetTitle("Event=%i"%evn)
    holder.Draw("p")
    

    for ich in xrange(32):
        draw_cmd = "wfm%i+%i:Iteration$" % (ich, ich*0)
        selection = "event==%i"%evn
        #print selection
        tree.SetLineColor(colors[ich])
        tree.SetMarkerStyle(colors[ich])
        tree.SetLineWidth(2)
        tree.SetLineStyle(1)
        #print "Channel", ich, draw_cmd
        tree.Draw(draw_cmd, selection,"same l")
   
    c1.Update()
    raw_input()


