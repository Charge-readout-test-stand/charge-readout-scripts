"""
Reduce tier3 file size by cutting:
  * most branches
  * events with too small SignalEnergy

https://root.cern.ch/root/html600/tutorials/tree/copytree2.C.html

"""

import os
import sys
import ROOT

import struck_analysis_cuts
import struck_analysis_parameters



if len(sys.argv) < 2:
    print "provide arguments: names of tier3 root files"
    sys.exit(1)

filenames = sys.argv[1:]

for filename in filenames:

    print "--> processing", filename

    # open file, grab tree:
    tfile = ROOT.TFile(filename)
    oldtree = tfile.Get("tree")
    oldruntree = tfile.Get("runtree")
    print "\t %i entries in old tree" % oldtree.GetEntries()
    isMC = struck_analysis_parameters.is_tree_MC(oldtree)
    print "\t isMC:", isMC

    drift_time_low = struck_analysis_parameters.drift_time_threshold
    drift_time_high = 9.0

    # construct some cuts...
    selections = []
    #selections.append("(nsignals==1)") # single-channel cut
    selections.append("(nsignals>0 || is_pulser)") 
    selections.append("((nsignals>0  && SignalEnergy>100)|| is_pulser)") 
    #selections.append("(nXsignals==1 && nYsignals==1)") # for twoSignals
    #selections.append("(!is_pulser || !is_bad)") 
    #selections.append("(nsignals>0)") 
    #selections.append("(SignalEnergy>50)")
    #selections.append("(SignalEnergy>100)")
    #selections.append("(SignalEnergy>200)")
    selections.append("(rise_time_stop95_sum-trigger_time>%.6f)" % drift_time_low)
    selections.append("(rise_time_stop95_sum-trigger_time<%.6f)" % drift_time_high)
    #selections.append(struck_analysis_cuts.get_drift_time_cut(isMC=isMC))
    selections = "&&".join(selections)
    print "selections:"
    print selections[:150] # first ~line

    # make new tree
    basename = os.path.basename(filename)
    newfile = ROOT.TFile("red_%s" % basename, "recreate")
    #newfile = ROOT.TFile("twoSignals_%s" % basename, "recreate")
    newtree = oldtree.CloneTree(0) # the zero prepares branches but doesn't copy anything yet
    newruntree = oldtree.CloneTree()
    newtree.SetTitle(selections)

    # event list
    oldtree.Draw(">>elist", selections)
    elist = ROOT.gDirectory.Get("elist")
    print "\t %i entries to copy" % elist.GetN()

    reporting_percent = 1
    reporting_period = elist.GetN() * reporting_percent / 100
    print "\t reporting_period", reporting_period

    # loop over event list
    oldtree.SetEventList(elist)
    print "\t copying entries..."
    for i in xrange(elist.GetN()):

        if i % reporting_period == 0:
            print "\t\t entry %i | %.1f percent" % (i, i*100.0/elist.GetN())

        oldtree.GetEvent(elist.GetEntry(i))
        newtree.Fill()

    print "\t done copying."

    #newfile.Write()
    print "\t %i entries in new tree" % newtree.GetEntries()

