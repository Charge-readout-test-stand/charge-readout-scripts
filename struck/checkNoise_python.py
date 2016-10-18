import ROOT
import numpy as np
import matplotlib.pyplot as plt

tfile = ROOT.TFile("tier3_SIS3316Raw_20160921080244_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root")

tree = tfile.Get("tree")
events = tree.GetEntries()
print "Events in File = ", events

plt.ion()

for evi in xrange(events):
    tree.GetEntry(evi)
    evn = tree.event

    for ich in xrange(32):
        wfm_array = getattr(tree, "wfm%i"%ich)
        wfm_current = np.array([wfm_array[wfmi] for wfmi in xrange(800)])
        plt.plot(wfm_current)

    plt.show()
    raw_input()
    plt.clf()


