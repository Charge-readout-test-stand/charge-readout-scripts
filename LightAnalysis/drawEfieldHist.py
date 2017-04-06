"""
Draw 2D field hist
"""

import os
import sys
import math

import ROOT
ROOT.gROOT.SetBatch(True)

ROOT.gStyle.SetOptStat(0)

from struck import struck_analysis_parameters 


def main(filename):

	print "Processing file:", filename
	tfile = ROOT.TFile(filename)
        hist = tfile.Get("Efieldhist")
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]

        drift_length = struck_analysis_parameters.drift_length  # mm
        print "drift_length [mm]:", drift_length

        canvas = ROOT.TCanvas()
        canvas.SetRightMargin(0.12)
        canvas.SetGrid()
        canvas.SetLogz(0)	

        hist.GetXaxis().SetTitle("#rho [mm]")
        hist.GetYaxis().SetTitle("y [mm]")
        hist.SetTitle("Electric field [V/cm]")

        z = -5.0
        delta_z = hist.GetYaxis().GetBinWidth(1)
        print "data: z [mm] | E [V/cm]"
        while z < drift_length + 1.0:
            iBin = hist.FindBin(0, z)
            val = hist.GetBinContent(iBin)
            bin_low_edge = hist.GetYaxis().GetBinLowEdge(
              hist.GetYaxis().FindBin(z))
            print "\t  %.1f to %.1f | %.2f" % (
                bin_low_edge, 
                bin_low_edge + hist.GetYaxis().GetBinWidth(1), 
                val,
            ) 
            z += delta_z

        max_x = math.sqrt(2)*100/2.0 # radius to diagonal of tile
        print "\n"
        print "field data in drift region:"
        print "data: rho, z [mm] | E [V/cm]"

        rho = 0.0
        z = 0.0
        iBin = hist.FindBin(rho, z)
        val = hist.GetBinContent(iBin)
        print "\t %.1f, %.1f | %.1f" % (rho, z, val)

        rho = 0.0
        z = drift_length
        iBin = hist.FindBin(rho, z)
        val = hist.GetBinContent(iBin)
        print "\t %.1f, %.1f | %.1f" % (rho, z, val)

        rho = max_x
        z = 0.0
        iBin = hist.FindBin(rho, z)
        val = hist.GetBinContent(iBin)
        print "\t %.1f, %.1f | %.1f" % (rho, z, val)

        rho = max_x
        z = drift_length
        iBin = hist.FindBin(rho, z)
        val = hist.GetBinContent(iBin)
        print "\t %.1f, %.1f | %.1f" % (rho, z, val)

        rho = 0.0
        z = drift_length - 0.5
        iBin = hist.FindBin(rho, z)
        val = hist.GetBinContent(iBin)
        print "\t %.1f, %.1f | %.1f" % (rho, z, val)

        rho = max_x
        z = drift_length - 0.5
        iBin = hist.FindBin(rho, z)
        val = hist.GetBinContent(iBin)
        print "\t %.1f, %.1f | %.1f" % (rho, z, val)

	hist.Draw("colz")
	canvas.Update()
	canvas.Print("EfieldHist_lin_%s.png" % basename)
        if not ROOT.gROOT.IsBatch():
	    raw_input("press enter ")

	canvas.SetLogz(1)	
	canvas.Update()
	canvas.Print("EfieldHist_log_%s.png" % basename)
        if not ROOT.gROOT.IsBatch():
	    raw_input("press enter ")

        print "max E: ", hist.GetMaximum()
        print "min E: ", hist.GetMinimum()

        # zoom in on drift region
        canvas.SetLogz(1)	
        print "max_x:", max_x
        hist.SetAxisRange(0,max_x, "X") # rho
        hist.SetAxisRange(0,drift_length,"Y") # Z
        canvas.Update()
        canvas.Print("EfieldHist_log_zoom_%s.png" % basename)
        if not ROOT.gROOT.IsBatch():
            raw_input("press enter ")

        canvas.SetLogz(0)	
        canvas.Update()
        canvas.Print("EfieldHist_lin_zoom_%s.png" % basename)
        if not ROOT.gROOT.IsBatch():
            raw_input("press enter ")
        print "max E: ", hist.GetMaximum()
        print "min E: ", hist.GetMinimum()


        # cut troublesome points near anode:
        hist.SetAxisRange(0,drift_length-0.5,"Y") # Z
        canvas.Update()
        canvas.Print("EfieldHist_lin_zoom2_%s.png" % basename)
        print "max E: ", hist.GetMaximum()
        print "min E: ", hist.GetMinimum()




if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: [*.dat files]"
        sys.exit(1)

    filename = sys.argv[1]

    main(filename)

