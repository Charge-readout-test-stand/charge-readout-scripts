import ROOT
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

tier1_fname = "~/2017_11_13_SiPM_Run/overnight_new_bias//tier1/tier1_SIS3316Raw_20171130141701_overnight_SiPMs_305bias_with_Charge_3110V_scope_trigger_8mV_trig11_1-ngm.root"
tfile = ROOT.TFile(tier1_fname)
tree = tfile.Get("HitTree")
n_entries = tree.GetEntries()

plt.figure(1)
for event_index in xrange(n_entries):

    tree.GetEntry(event_index)
    graph = tree.HitTree.GetGraph()
 
    slot = tree.HitTree.GetSlot()
    card_channel = tree.HitTree.GetChannel() # 0 to 16 for each card
    channel = card_channel + 16*slot # 0 to 31

    print "Channel is", channel

    wfm = np.array([graph.GetY()[isamp] for isamp in xrange(graph.GetN())])

    plt.clf()
    plt.plot(wfm)

    raw_input()

