"""
Reduce tier3 file size by cutting most branches, events with too small
SignalEnergy
"""

import os
import sys
import ROOT

# https://root.cern.ch/root/html600/tutorials/tree/copytree2.C.html


if len(sys.argv) < 2:
    print "provide arguments: names of tier3 root files"
    sys.exit(1)

filenames = sys.argv[1:]

for filename in filenames:

    print "--> processing", filename
    basename = os.path.basename(filename)
    print basename

    #continue # debugging


    tfile = ROOT.TFile(filename)
    oldtree = tfile.Get("tree")
    print "\t %i entries in old tree" % oldtree.GetEntries()

    # turn on selected branches
    oldtree.SetBranchStatus("*",0) # first turn off all branches
    oldtree.SetBranchStatus("SignalEnergy",1)
    oldtree.SetBranchStatus("nsignals",1)
    oldtree.SetBranchStatus("nXsignals",1)
    oldtree.SetBranchStatus("nYsignals",1)
    oldtree.SetBranchStatus("energy1_pz",1)
    oldtree.SetBranchStatus("channel",1)
    oldtree.SetBranchStatus("noise",1) # MC only 
    oldtree.SetBranchStatus("rise_time_stop95",1)

    # new tree
    newfile = ROOT.TFile("red_%s" % basename, "recreate")
    newtree = oldtree.CloneTree(0) # the zero prepares branches but doesn't copy anything yet

    # event list
    oldtree.Draw(">>elist", "nsignals>0 && SignalEnergy>100")
    elist = ROOT.gDirectory.Get("elist")
    print "\t %i entries to copy" % elist.GetN()

    # loop over event list
    oldtree.SetEventList(elist)

    reporting_percent = 5
    reporting_period = elist.GetN() * reporting_percent / 100
    print "\t reporting_period", reporting_period
    print "\t copying entries..."
    for i in xrange(elist.GetN()):

        if i % reporting_period == 0:
            print "\t\t entry %i | %.1f percent" % (i, i*100.0/elist.GetN())

        oldtree.GetEvent(elist.GetEntry(i))
        newtree.Fill()

    print "\t done copying."

    newfile.Write()
    print "\t %i entries in new tree" % newtree.GetEntries()

