"""
this script converts COMSOL E-Field data to a tree. Takes ~ 5s on DAQ. 
"""

import os
import sys
import ROOT
ROOT.gROOT.SetBatch(True)


def get_output_filename(filename):
    """
    make an output root filename from the input filename
    """
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    output_filename = "%s_tree.root" % basename
    print output_filename
    return output_filename


def make_tree(filename):
    """
    Make a TTree from COMSOL output; x, y, z in m, E-field components in V/m. 
    """
    print "making tree from file:", filename

    branchList = [
        "x",
        "y",
        "z",
        "Ex",
        "Ey",
        "Ez",
        "V",
        ]

    branchDescriptor = ":".join(branchList)

    output_filename = get_output_filename(filename)
    output_file = ROOT.TFile(output_filename, "recreate")

    tree = ROOT.TTree("tree", "tree created from %s" % filename)
    print "reading in TPC E field data file with root..."
    tree.ReadFile(filename, branchDescriptor)
    print "...done reading E-field data into tree"

    tree.Write()
    output_file.Close()


if __name__ == "__main__":

    # Qidong's file on Ubuntu DAQ:
    filename = "/home/teststand/20161103_cathode_simulation/ExEyEz_V_large_simp"

    if len(sys.argv) > 1:
        filename = sys.argv[1]

    make_tree(filename)

