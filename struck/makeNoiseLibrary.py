import ROOT
import os
import sys
#import struck_analysis_cuts

reporting_period = 1

def process_file(filename):

    tier3_tree = ROOT.TChain("tree")
    tier3_tree.Add(filename)

    #newfile = ROOT.TFile("noiselibrary.root", "recreate")
    #newtree = ROOT.TTree("tree", "%s processed wfm tree" % basename)

    selection = "is_pulser && nsignals==0 && lightEnergy < 20"
    print selection
    tier3_tree.Draw(">>elist",selection)
    elist = ROOT.gDirectory.Get("elist")
    tier3_tree.SetEventList(elist)
    
    for i in xrange(elist.GetN()):

        if i % reporting_period == 0:
            print "\t\t entry %i | %.1f percent" % (i, i*100.0/elist.GetN())

        tier3_tree.GetEvent(elist.GetEntry(i))
        tier1_name = str(tier3_tree.filename)

        print tier1_name
        
        tier1_file = ROOT.TFile(tier1_name)
        tier1_tree = tier1_file.Get("HitTree")
        tier1_tree.GetEvent(elist.GetEntry(i))
        wfm = type(tier1_tree._waveform)
        print dir(wfm)
        print wfm.size
        raw_input("Pause")
        #newtree.Fill()

    #print "Found Noise Events %i out of %i total" % (newtree.GetEntries(),
    #                                                 tree.GetEntries())
    #newfile.Write()
    #newfile.Close()

if __name__ == "__main__":
    
    #if len(sys.argv) > 1:
    #    filename = sys.argv[1]
    #else:
    #    print "Using Default file for testing"
        filename = "/g/g19/jewell6/alexiss/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_20160922135450_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root"

    process_file(filename)
