"""
script for comparing cold cathode pressure, before and after circulating argon

first use makeRootFile.py to convert .dat files to .root

then, usage:
python comparePumpDownData.py test_20151117_181009.root test_20151118_183455.root 

"""

import os
import sys

from ROOT import gROOT
#gROOT.SetBatch(True)
from ROOT import TTree
from ROOT import TFile
from ROOT import TColor
from ROOT import TCanvas
from ROOT import TH1D
from ROOT import TLegend

def main(filenames):

    print "--> processing files:"

# some start time offsets to use for specific files:
#t_offset_hours = [0, 17.0]


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [*.dat files]"
        sys.exit(1)

    filenames = sys.argv[1:]

    main(filenames)

    t_files = []
    trees = []
    t_offset = []

    legend = TLegend(0.1, 0.86, 0.9, 0.99)
    legend.SetNColumns(2)

    good_colors = [
        TColor.kBlack,
        TColor.kRed,
        TColor.kGreen+2,
        TColor.kBlue,
        TColor.kOrange+1,
        TColor.kViolet,
    ]

    for i, filename in enumerate(filenames):
        t_file = TFile(filename)
        tree = t_file.Get("tree")
        n_entries = tree.GetEntries()
        print "\t", filename
        print "\t %i entries" % n_entries

        tree.SetLineColor(good_colors[i])

        t_files.append(t_file)
        trees.append(tree)

        entry = ""
        
        # before angle valve swap:
        if filename == "test_20151117_181009.root":
            entry = "before Ar, before valve swap"
        if filename == "test_20151118_183455.root":
            entry = "after Ar, before valve swap"

        if filename == "test_20151123_184116.root":
            entry = "after valve swap, no LXe cell"

        # after angle valve swap:
        if filename == "test_20151124_105350.root":
            entry = "before Ar, after valve swap"
        if filename == "test_20151130_164223.root":
            entry = "after Ar, after valve swap"

        # xenon purge
        if filename == "test_20151204_135813.root":
            entry = "after Xe"

        basename = os.path.splitext(filename)[0]
        basename = basename.split("_")[1:]
        basename = "_".join(basename)
        print basename
        entry += " " + basename
        legend.AddEntry(trees[-1], entry, "l")

        # find first instance where ccg pressure > 0:
        for i_entry in xrange(n_entries):
            tree.GetEntry(i_entry)
            if tree.pCCG > 0:
                break
        t_offset.append(tree.timeStamp)


frame_hist = TH1D("hist","",100,0,15)
frame_hist.SetMaximum(1e-3)
frame_hist.SetMinimum(1e-7)
frame_hist.SetXTitle("time [hours]")
frame_hist.SetYTitle("cold cathode gauge pressure [torr]")


canvas = TCanvas("canvas","")
canvas.SetTopMargin(0.15)
canvas.SetLogy(1)
canvas.SetGrid(1,1)

draw_cmd = "pCCG/1e6:(timeStamp-%s)/60/60" 
selection = "pCCG>0"

frame_hist.Draw()

#trees[0].Draw(draw_cmd % t_offset[0], selection, "l")

for i, tree in enumerate(trees):
    tree.Draw(draw_cmd % t_offset[i], selection, "l same")

legend.Draw()
canvas.Update()
canvas.Print("pump_down_comparison.png")
canvas.Print("pump_down_comparison.pdf")
canvas.Print("pump_down_comparison.jpg")

val = raw_input("press any key to continue\n")






