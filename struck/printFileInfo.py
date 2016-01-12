
import os
import sys
import glob

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TH1D
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TColor
from ROOT import TPad
from ROOT import TLegend
from ROOT import TPaveText
from ROOT import gSystem
from ROOT import gStyle
from ROOT import TH1D
from ROOT import TH2D


def process_file(filename):

    #print "processing file: ", filename
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    #basename = "_".join(basename.split("_")[1:])
    #print basename

    # open the root file and grab the tree
    root_file = TFile(filename)
    tree = root_file.Get("tree")

    n_entries = tree.GetEntries()
    tree.GetEntry(0)
    mean = tree.baseline_mean_file
    rms = tree.baseline_rms_file
    #print mean[0]
    #print rms[0]
    
    n_entries_per_ch = {}
    channels = [0,1,2,3,4,8]
    for channel in channels:
        n_entries_per_ch[channel] = tree.Draw(
            "channel",
            "channel==%i" % channel,
            "goff"
        )
        #print channel, n_entries_per_ch[channel]

    print "%s | %i | %i | %i | %i | %i | %i | %i | %.2f | %.2f " % (
        basename,
        n_entries,
        n_entries_per_ch[0],
        n_entries_per_ch[1],
        n_entries_per_ch[2],
        n_entries_per_ch[3],
        n_entries_per_ch[4],
        n_entries_per_ch[8],
        mean[0],
        rms[0],
    )



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [sis root files]"
        sys.exit(1)

    print "name | n | 0 | 1 | 2 | 3 | 4 | 8 | base_mean | base_rms"

    for filename in sys.argv[1:]:
        process_file(filename)


