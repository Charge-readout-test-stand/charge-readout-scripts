"""
this script converts 2-D COMSOL E-field E(rho, z) data to a tree. 
"""

import os
import sys

from ROOT import gROOT
gROOT.SetBatch(True)
from ROOT import TTree
from ROOT import TFile
from ROOT import TCanvas
from ROOT import TH2D
from ROOT import gStyle

gStyle.SetOptStat(0)

def main(filename):

	print "Processing file:", filename
        is_chas = False # flag to ID comsol from Jan/March 2017

	basename = os.path.basename(filename)
	basename = os.path.splitext(basename)[0]

	branchList = [
		"x",
		"y",
		"Ex",
		"Ey",
                "V"
		]

        # COMSOL file generated by Chas:
        if "LXe_chamber_field_20160119" in basename: is_chas = True
        if "2017_01_19_comsol" in basename: is_chas = True
        if "2017_03_24_33mm_3110V_NoNan" in basename: is_chas = True
        if is_chas:
            print "Chas COMSOL model"
            branchList = [
                    "r",
                    "z",
                    "E",
                    "V"
                    ]

	branchDescriptor = ":".join(branchList)

	output_file = TFile("%s.root" % basename, "recreate")

	tree = TTree("tree", "tree created from TPC E field data")
	print "reading in TPC E field data file with root..."
	tree.ReadFile(filename, branchDescriptor)
	print "...done"
        print "%i entries in tree" % tree.GetEntries()

        tree.Show(0)
        tree.Show(tree.GetEntries()-1)

        c1 = TCanvas()
        c1.SetRightMargin(0.12)
        c1.SetGrid()
        c1.SetLogz(0)	

        if is_chas:
            step_size = 0.5 # 0.5-mm bins
            max_r = 255.0/2
            n_bins_r = int(max_r/step_size)
            min_z = -20
            max_z = 70
            n_bins_z = int((max_z-min_z)/step_size)
            hist = TH2D("Efieldhist", "", 
                n_bins_r, 0, max_r, 
                n_bins_z, min_z, max_z,
            )

            hist.GetDirectory().cd()

            cathodeToCellBottom = 10.54 # mm

            draw_cmd = "z*1e3-%f-%f:r*1e3+%f>>Efieldhist" % (
                step_size/2.0, cathodeToCellBottom, step_size/2.0)

            n_drawn = tree.Draw(draw_cmd, "", "goff") # unweighted, for testing hist binning
	    hist.Draw("colz")
            c1.Update()
            c1.Print("EfieldHist_bins_%s.png" % basename)

            n_drawn = tree.Draw(draw_cmd, "E/100", "goff")

        else:
            hist = TH2D("Efieldhist", "", 2900, -145.475, 144.525, 1800, -80, 100)
            #hist = TH2D("Efieldhist", "", 2100, -105, 105, 250, -5, 20)
            #tree.Draw("y-10.54:x-125.475>>Efieldhist", "(sqrt(Ex*Ex + Ey*Ey)/100)*((sqrt(Ex*Ex + Ey*Ey)/100)>950)", "goff")
            hist.GetDirectory().cd()
            tree.Draw("y-10.64:x-125.475>>Efieldhist", "(sqrt(Ex*Ex + Ey*Ey)/100)", "goff")

        print "%i entries drawn" % n_drawn
	hist.SetXTitle("Rho (mm)")
	hist.SetYTitle("Z (mm)")
        tree.Write()
        hist.Write()
        hist.GetXaxis().CenterTitle()
        hist.GetYaxis().CenterTitle()
        #hist.SetMinimum(950)


	hist.Draw("colz")
        iBin = hist.FindBin(0, 5)
	print "E field at (0,5) mm [V/cm]:", hist.GetBinContent(iBin)
        iBin = hist.FindBin(0, -5)
	print "E field at (0,-5) mm [V/cm]:", hist.GetBinContent(iBin)
        iBin = hist.FindBin(0, 1)
	print "E field at (0,1) mm [V/cm]:", hist.GetBinContent(iBin)

	c1.Update()
	c1.Print("EfieldHist_lin_%s.png" % basename)
        if not gROOT.IsBatch():
	    raw_input("press enter ")

	c1.SetLogz(1)	
	c1.Update()
	c1.Print("EfieldHist_log_%s.png" % basename)
        if not gROOT.IsBatch():
	    raw_input("press enter ")


        # don't do this while making the root file this way; the hist axes need
        # to be reset
        if False: 

            c1.SetLogz(1)	
            hist.SetAxisRange(0,5)
            hist.SetAxisRange(-15,10,"Y")
            c1.Update()
            c1.Print("EfieldHist_log_zoom_%s.png" % basename)
            raw_input("press enter ")

            c1.SetLogz(0)	
            c1.Update()
            c1.Print("EfieldHist_lin_zoom_%s.png" % basename)
            raw_input("press enter ")



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [*.dat files]"
        sys.exit(1)

    filename = sys.argv[1]

    main(filename)

