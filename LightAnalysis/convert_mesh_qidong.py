"""
Convert COMSOL output from Qidong's detailed simulation of cathode. 

Modified from Mike's script. 

still to do:
    * use "nearest" option for more accuracy
    * get rid of points where field is 0 -- these are inside the solids
    * choose appropriate step size -- same in x, y, z?

notes:
* "nearest" option: takes 5s for 1-mm spacing

"""

import os
import math
import numpy as np
from scipy.interpolate import griddata

import ROOT
ROOT.gROOT.SetBatch(True)

# dimensions
step_size = 0.1/1e3 # mm
half_width = 50.0/1e3 # mm
#height = 18.2/1e3 # mm
height = 20.0/1e3 # mm
z_offset = 3.81/1e3

nbinsx = int(half_width/step_size*2)+1
nbinsz = int(height/step_size)+1

print nbinsx, nbinsz


# Qidong's sim on ubuntu DAQ
file_name = "/home/teststand/20161103_cathode_simulation/ExEyEz_V_large_simp"

# x, y, z are in meters. E-field components are in V/m. 

# complex j means use 100 bins
#grid_x, grid_y, grid_z = np.mgrid[-half_width:half_width:step_size,-half_width:half_width:step_size,0:height:step_size]
grid_x, grid_y, grid_z = np.mgrid[
    -half_width:half_width:nbinsx*1j,
    -half_width:half_width:nbinsx*1j,
    z_offset:height+z_offset:nbinsz*1j]

#Qidong's z is our y
print "Loading..."
old_x1,old_z1,old_y1,Ex,Ey,Ez,V = np.loadtxt(file_name, unpack = True, comments = "%")
print "\tLoaded"
print "nPoints = ", len(old_x1)

# make arrays to hold values after cuts
x1 = []
y1 = []
z1 = []
EValues = []

# exclude some points
n_cut = 0
n_out_of_range = 0
for i in xrange(len(old_x1)):

    # points where E is zero are in the solid
    if Ex[i] == 0 and Ey[i] == 0 and Ez[i] == 0:
        n_cut += 1

    # points above the anode and below the cathode shouldn't be used
    elif old_z1[i] < z_offset or old_z1[i] >= 18.15/1e3+z_offset:
        n_out_of_range += 1
    else:
        x1.append(old_x1[i])
        y1.append(-old_y1[i]) # I don't think it matters, but since z -> y
        z1.append(old_z1[i])
        EValues.append(math.sqrt(Ex[i]**2 + Ey[i]**2 +  Ez[i]**2))
print "%i cut points" % n_cut
print "%i points out of z range" % n_out_of_range

x1 = np.array(x1)
y1 = np.array(y1)
z1 = np.array(z1)
EValues = np.array(EValues)

print "Inverting..."
#Need a Array of (n,D) but have (D,n) so just swap indexing
points_inverted = np.array([x1,y1,z1])
points = np.swapaxes(points_inverted, 0, 1)
print "\tDone Invert"
print "N points (should be ~1 million):", len(points)
print "Dimensions (should be 3):", len(points[0])
print points[0]

print "Gridding it up..."
#Function to get values on the grid
#grid_E = griddata(points, EValues, (grid_x, grid_y, grid_z), method='linear')
grid_E = griddata(points, EValues, (grid_x, grid_y, grid_z), method='nearest') # faster
print "\tGrid Made"

print "grid size:"
print len(grid_E), len(grid_E[0]), len(grid_E[0,0])

basename = os.path.basename(file_name)
tfile = ROOT.TFile("%s.root" % basename, "recreate")

# introduce an offset so that hist bin centers are at grid points
offset = step_size*1e3/2.0

hist = ROOT.TH3F("hist","", 
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    nbinsz, -offset, height*1e3+offset)

slice_hist = ROOT.TH2F("slice_hist","2D projection of E-field", 
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    #nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    nbinsz, -offset, height*1e3+offset)
slice_hist.SetXTitle("x [mm]")
slice_hist.SetYTitle("z [mm]")


print "\n\nx | y | z | E"
for nx in np.arange(len(grid_E)):
    for ny in np.arange(len(grid_E[nx])):
        for nz in np.arange(len(grid_E[nx,ny])):
            xpos = grid_x[nx,ny,nz]
            ypos = grid_y[nx,ny,nz]
            zpos = grid_z[nx,ny,nz]
            EField = grid_E[nx, ny, nz]/100.0 # extra factor of 100?!
            #print xpos*1e3, ypos*1e3, zpos*1e3, EField

            # find the right bin
            ibin = hist.FindBin(xpos*1e3, ypos*1e3, zpos*1e3-z_offset*1e3)
            content = hist.GetBinContent(ibin) # check for existing content

            if content != 0.0: # warn, if needed
                print "WARNING: hist bin %i already has content %i !!" % (ibin, content)

            hist.SetBinContent(ibin, EField) # Set hist bin content

            if ypos == 0.0: # fill slice_hist
                slice_hist.Fill(xpos*1e3, zpos*1e3-z_offset*1e3, EField)

# write hists to file
hist.Write()
slice_hist.Write()

# make a plot
canvas = ROOT.TCanvas("canvas","")
canvas.SetRightMargin(0.15)
canvas.SetGrid()
slice_hist.Draw("colz")
canvas.Update()
canvas.Print("%s_EField.pdf" % basename)

if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

