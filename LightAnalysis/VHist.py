"""
Draw potential hist from Qidong / COMSOL. 
"""


import os
import sys
#from scipy.interpolate import griddata 
from ROOT import gROOT
from ROOT import TTree
from ROOT import TFile
from ROOT import TCanvas
c1 = TCanvas()
from ROOT import TH2D

def main(EfieldHist):
	print "Processing file:", EfieldHist

	#to find number of columns in file
	TPC_Efield_RegGrid_no_Nan = file(EfieldHist)

	branchList = [
		"x",
		"y",
		"V",
		]

	branchDescriptor = ":".join(branchList)

	basename = os.path.basename(EfieldHist)
	basename = os.path.splitext(basename)[0]

	output_file = TFile("%s.root" % basename, "recreate")

	tree = TTree("tree", "tree created from TPC E field data")
	print "reading in TPC E field data file with root..."
	tree.ReadFile(EfieldHist, branchDescriptor)
	print "...done"

	Efieldhist = TH2D("Efieldhist", "Ey vs. Ex", 2900, -145.475, 144.525, 1800, -80, 100)
	tree.Draw("y:x-125.475>>Efieldhist", "V", "goff")
	Efieldhist.SetXTitle("x")
	Efieldhist.SetYTitle("y")
	Efieldhist.Draw("colz")
#interpolation method:	T = griddata((xi, yi), (x, y), method='cubic')
	c1.SetGrid()	
	c1.Print("EfieldHist.png")
	c1.Update()
	raw_input("press enter")
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [*.dat files]"
        sys.exit(1)

    filename = sys.argv[1]

    main(filename)
