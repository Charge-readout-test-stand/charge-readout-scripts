import os
import sys
import ROOT


def draw_wfms(filename):
    print "---> drawing wfms..."
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("HitTree")

    canvas = ROOT.TCanvas("canvas","")
    canvas.SetGrid()
    canvas.SetLeftMargin(0.15)

    #tree.Scan( "_waveform:Iteration$",
    #    "_waveform==Max$(_waveform) && _slot==1 && _channel==15"),

    tree.SetLineWidth(2)
    tree.SetMarkerStyle(8)
    tree.SetMarkerSize(0.5)

    for i_entry in xrange(tree.GetEntries()):
        
        tree.GetEntry(i_entry)
        slot = tree.HitTree.GetSlot()
        channel = tree.HitTree.GetChannel()
        if channel != 15: continue
        if slot != 1: continue
        print "Entry %i | channel %i | slot %i" % (i_entry, channel, slot)
        #selection = "Entry$==%i && Iteration$>150 && Iteration$<300" % i_entry # zoom
        selection = "Entry$==%i" % i_entry
        tree.Draw(
            "_waveform:Iteration$",
            selection,
            "lp")
        canvas.Update()

        val = raw_input("enter to continue (q to quit) ")
        if val =='q': break
        if val == 'p': canvas.Print("wfm%i.pdf" % i_entry)


def draw_spectrum(filenames):
    print "---> drawing spectrum..."

    basename = os.path.commonprefix(filenames)

    out_file = ROOT.TFile("hist_%s.root" % basename, "recreate")
    hist = ROOT.TH1D("hist","", 9000,0,9000)
    #hist = ROOT.TH1D("hist","", 1000,0,3000)
    hist.SetXTitle("wfm max - baseline [ADC units]")
    hist.SetYTitle("Counts / %i ADC units" % hist.GetBinWidth(1))
    hist.SetLineColor(ROOT.kBlue+1)

    # form the draw command:
    n_points = 100
    baseline = []
    for i_point in xrange(n_points):
        baseline.append("_waveform[%i]" % i_point)
    baseline = "+".join(baseline)
    baseline = "(%s)/%.1f" % (baseline, n_points)
    #print baseline
        
    for i, filename in enumerate(filenames):
        print "--> processing file %i of %i" % (i+1, len(filenames))
        tfile = ROOT.TFile(filename)
        try:
            tree = tfile.Get("HitTree")
            n_entries = tree.GetEntries()

            hist.GetDirectory().cd()
            n_drawn = tree.Draw(
                "Max$(_waveform)-%s >> +hist" % baseline,
                "_channel==15 && _slot==1",
                "goff"
            )
            print "\t %i entries | %i drawn | %i in hist" % (tree.GetEntries(), n_drawn, hist.GetEntries())
        except:
            print "\t skipping this tree"


    rebinned_hist = hist.Clone("rebinned_hist")
    rebinned_hist.Rebin(10) # rebin
    rebinned_hist.SetYTitle("Counts / %i ADC units" % rebinned_hist.GetBinWidth(1))

    canvas = ROOT.TCanvas("canvas","")
    canvas.SetGrid()
    canvas.SetLogy(0)
    rebinned_hist.Draw()
    canvas.Update()

    canvas.Print("lin_spectrum_%s.pdf" % basename)
    canvas.SetLogy(1)
    canvas.Print("log_spectrum_%s.pdf" % basename)

    canvas.SetLogy(0)
    rebinned_hist.SetAxisRange(0, 2000)
    canvas.Print("lin_zoom_spectrum_%s.pdf" % basename)
    canvas.SetLogy(1)
    canvas.Print("log_zoom_spectrum_%s.pdf" % basename)

    hist.Write()
    rebinned_hist.Write()

    if not ROOT.gROOT.IsBatch():
        val = raw_input("enter to continue (p to print) ")
        if val == 'p': canvas.Print("spectrumi_%s.pdf" % basename)

filenames = sys.argv[1:]


#draw_spectrum(filenames[:2]) # only a few files
draw_spectrum(filenames)

#draw_wfms(filenames[0])
