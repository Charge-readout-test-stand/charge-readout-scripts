"""
plot results from noiseTests.py
"""

import os
import sys
import glob
import ROOT

import struck_analysis_parameters


canvas = ROOT.TCanvas("my_canvas","")
canvas.SetGrid(1,1)



def get_graph(energy_var, selection, filenames, color):
    graph = ROOT.TGraphErrors()
    graph.SetMarkerColor(color)
    graph.SetMarkerStyle(8)
    graph.SetMarkerSize(1.0)
    graph.SetTitle(energy_var)
    print "--> making %s graph" % energy_var
    #print selection

    for i_file, filename in enumerate(results):
        print "--> processing file",i_file, filename
        tfile = ROOT.TFile(filename)
        tree = tfile.Get("tree")
        try:
            tree.GetEntries()
        except:
            print "skipping file"
            continue
        #n_entries = tree.GetEntries()
        #print "\t %i entries in tree" % n_entries
        tree.GetEntry(0)
        n_baseline_samples = tree.n_baseline_samples
        #if "1" in energy_var: n_baseline_samples *= 2
        # energy measurements with 1 in them, like energy1_pz, use 2x n_baseline_samples
        baseline_average_time = n_baseline_samples*2/tree.sampling_freq_Hz*1e6

        if baseline_average_time > 14.0:
            print "only times < 14 make sense for the usual wfm length and gap time"
            continue

        # make and fill hist:
        hist = ROOT.TH1D("hist_%i" % i_file,"%s: %.1f #mus" % (energy_var, baseline_average_time), 10000,-2000,2000)
        hist.GetDirectory().cd()
        n_drawn = tree.Draw("%s >> %s" % (energy_var, hist.GetName()), selection,) # "goff")
        mean = hist.GetMean()
        rms = hist.GetRMS()
        i_point = graph.GetN()
        val = hist.GetRMS()
        if energy_var == "energy_rms1":
            print "SPECIAL CASE!"
            val = hist.GetMean()
        graph.SetPoint(i_point, baseline_average_time, val)
        #graph.SetPointError(i_point, 0.0, hist.GetMean())
        print "\t baseline_average_time:", baseline_average_time, "RMS:", rms, "mean:", mean
        title = "%s: %.1f #mus | mean: %.3f | RMS: %.3f" % (
            energy_var, 
            baseline_average_time,
            mean,
            rms
        )
        hist.SetTitle(title)
        if False  and not ROOT.gROOT.IsBatch(): 
            print mean -5*rms
            print mean +5*rms
            hist.SetAxisRange(mean -5*rms, mean +5*rms)
            hist.Draw()
            canvas.Update()
            raw_input("enter to continue")
    return graph


def plot_results(results):
    print "----> plotting results..."
    results.sort()

    #selection = "channel != %i" % struck_analysis_parameters.pmt_channel
    selection = "channel==2 && lightEnergy/calibration<20"

    graphs = []
    #graphs.append(get_graph("energy_rms1", results, ROOT.kRed)) # just a test
    graphs.append(get_graph("energy", selection, results, ROOT.kViolet+1))
    graphs.append(get_graph("energy_pz", selection, results, ROOT.kRed))
    graphs.append(get_graph("energy1_pz", selection, results, ROOT.kBlue))
    graphs.append(get_graph("energy1", selection, results, ROOT.kGreen+1))

    # our simple approximation:
    filename = results[len(results)-1]
    #filename = results[0]
    print filename
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    hist = ROOT.TH1D("hist","White noise approx",200,0,100)
    hist.GetDirectory().cd()
    #n_drawn = tree.Draw("baseline_rms*calibration >> %s" % hist.GetName(), selection,) # "goff")
    n_drawn = tree.Draw("energy_rms1 >> %s" % hist.GetName(), selection,) # "goff")
    print "%i drawn, %i in hist" % (n_drawn, hist.GetEntries())
    baseline_rms = hist.GetMean()
    print "simple approx: baseline_rms", baseline_rms
    hist.Draw()
    canvas.Update()
    #if not ROOT.gROOT.IsBatch(): raw_input("enter to continue")

    fcn = ROOT.TF1("fcn","%s*sqrt(2.0/(x*1000/40))" % baseline_rms, 1, 100)
    print "fcn at 8:", fcn.Eval(8)
    fcn.SetLineColor(ROOT.kBlack)


    graphs[0].Draw("alp")
    frame_hist = graphs[0].GetHistogram()
    frame_hist.GetXaxis().SetTitle("baseline_average_time [#mus]")
    frame_hist.GetYaxis().SetTitle("Energy [keV]")
    frame_hist.GetYaxis().SetTitleOffset(1.2)
    frame_hist.SetMinimum(0)
    frame_hist.SetTitle("")

    legend = ROOT.TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
 
    for graph in graphs:
        graph.Draw("pl same")
        legend.AddEntry(graph, graph.GetTitle(), "p")
    fcn.Draw("same")
    legend.AddEntry(fcn, "white noise RMS approx", "l")

    legend.Draw()
    canvas.Update()
    canvas.Print("%s_n_baseline_samples_tests.pdf" % os.path.commonprefix(results) )

    if not ROOT.gROOT.IsBatch():
        raw_input("enter to continue")



if __name__ == "__main__":

    filename = "/g/g17/alexiss/scratch/2016_09_13_pulser_tests/tier1_SIS3316Raw_20160914184725_digitizer_noise_tests__1-ngm.root"
    filename = "/g/g17/alexiss/scratch/2016_08_15_8th_LXe/tier1/tier1_SIS3316Raw_20160816180708_8thLXe_126mvDT_cell_full_cath_1700V_HVOn_Noise_100cg__1-ngm.root"

    results = glob.glob("*baseline*.root") # find old results
    if len(sys.argv) > 1:
        results = sys.argv[1:] 
    plot_results(results)



