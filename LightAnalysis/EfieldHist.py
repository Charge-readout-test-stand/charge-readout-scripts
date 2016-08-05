import os
import sys
#from scipy.interpolate import griddata 
from ROOT import gROOT
from ROOT import TTree
from ROOT import TFile
from ROOT import TCanvas
c1 = TCanvas()
from ROOT import TH2D
from ROOT import gStyle
gStyle.SetOptStat(0)

def main(EfieldHist):
	print "Processing file:", EfieldHist

	#to find number of columns in file
        TPC_E_RegGrid_20160718_v2_noNaN = file(EfieldHist)

	branchList = [
		"x",
		"y",
		"Ex",
		"Ey",
                "V"
		]

	branchDescriptor = ":".join(branchList)

	basename = os.path.basename(EfieldHist)
	basename = os.path.splitext(basename)[0]

	output_file = TFile("%s.root" % basename, "recreate")

	tree = TTree("tree", "tree created from TPC E field data")
	print "reading in TPC E field data file with root..."
	tree.ReadFile(EfieldHist, branchDescriptor)
	print "...done"

	Efieldhist = TH2D("Efieldhist", "", 2900, -145.475, 144.525, 1800, -80, 100)
        #Efieldhist = TH2D("Efieldhist", "", 2100, -105, 105, 250, -5, 20)
        #tree.Draw("y-10.54:x-125.475>>Efieldhist", "(sqrt(Ex*Ex + Ey*Ey)/100)*((sqrt(Ex*Ex + Ey*Ey)/100)>950)", "goff")
        tree.Draw("y-10.54:x-125.475>>Efieldhist", "(sqrt(Ex*Ex + Ey*Ey)/100)", "goff")
        tree.Write()
        Efieldhist.Write()
	Efieldhist.SetXTitle("Rho (mm)")
	Efieldhist.SetYTitle("Z (mm)")
        Efieldhist.GetXaxis().CenterTitle()
        Efieldhist.GetYaxis().CenterTitle()
        #Efieldhist.SetMinimum(950)


	Efieldhist.Draw("colz")
        iBin = Efieldhist.FindBin(0, 18)
        #int pause
        #print pause
#interpolation method:	T = griddata((xi, yi), (x, y), method='cubic')
	c1.SetGrid()
	c1.SetLogz(0)	
	c1.Print("EfieldHist.png")
	c1.Update()
	print Efieldhist.GetBinContent(iBin)
	raw_input("press enter")
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [*.dat files]"
        sys.exit(1)

    filename = sys.argv[1]

    main(filename)

