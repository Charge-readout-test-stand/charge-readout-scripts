
import os
import sys
import ROOT

struck_name = "~/9th_LXe/red_red_overnight_9thLXe_v1.root"
mc_name = ""
energy_var_name = "SignalEnergy"

struck_file = ROOT.TFile(struck_name)
struck_tree = struck_file.Get("tree")
print "%i entries in struck tree" % struck_tree.GetEntries()

struck_data = ROOT.RooFit.RooDataSet(
    energy_var_name,
    "Struck SignalEnergy",
    ROOT.RooFit.RooArgSet(energy_var_name),
    RooFit.Import(struck_tree),
)



