import ROOT
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

tier1_fname = "../tier1/tier1_SIS3316Raw_20171130141701_overnight_SiPMs_305bias_with_Charge_3110V_scope_trigger_8mV_trig11_1-ngm.root"
tfile = ROOT.TFile(tier1_fname)
tree = tfile.Get("HitTree")
n_entries = tree.GetEntries()

plt.figure(1)
for event_index in xrange(n_entries):

    tree.GetEntry(event_index)
    graph = tree.HitTree.GetGraph()
    
    wfm = np.array([graph.GetY()[isamp] for isamp in xrange(graph.GetN())])

    plt.clf()
    plt.plot(wfm)

    raw_input()

