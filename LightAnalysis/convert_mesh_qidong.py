"""
Convert COMSOL output from Qidong's detailed simulation of cathode. 

Modified from Mike's script. 

still to do:
* use "linear" method for more accuracy?
* choose appropriate step size -- same in x, y, z?

notes:
* excluded points at z>=18.16mm. Also exclude z=0?
* 0.1mm step size gives memory error
* "nearest" method: 0.15-mm grid takes ~5 minutes 
* "nearest" method: 0.2-mm grid takes 2.5 minutes 
* "linear" method: 0.2-mm grid takes ~2 minutes 
* "nearest" method: takes 5s for 1-mm spacing

"""

import os
import math
import numpy as np
from scipy.interpolate import griddata

import ROOT
ROOT.gROOT.SetBatch(True)

# dimensions
step_size = 0.15/1e3 # mm
half_width = 46.0/1e3 # mm
height = 18.15/1e3 # mm
z_offset = 3.81/1e3

method = "nearest"
#method = "linear"

nbinsx = int(half_width/step_size*2)+1
nbinsz = int(height/step_size)+1

print "nbinsx:", nbinsx, "nbinsz:", nbinsz


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
print "Loading text file..."
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
n_out_of_r_range = 0
n_out_of_z_range = 0
for i in xrange(len(old_x1)):

    # points where E is zero are in the solid
    if Ex[i] == 0 and Ey[i] == 0 and Ez[i] == 0:
        n_cut += 1

    #elif math.sqrt(old_x1[i]**2 + old_y1[i]**2) > math.sqrt(2)*half_width:
    #    n_out_of_r_range += 1

    # points above the anode and below the cathode shouldn't be used
    elif old_z1[i] < z_offset or old_z1[i] >= 18.15/1e3+z_offset:
        n_out_of_z_range += 1
    else:
        x1.append(old_x1[i])
        y1.append(-old_y1[i]) # I don't think it matters, but since z -> y
        z1.append(old_z1[i])
        EValues.append(math.sqrt(Ex[i]**2 + Ey[i]**2 +  Ez[i]**2))
print "\t%i cut points" % n_cut
print "\t%i points out of r range" % n_out_of_r_range
print "\t%i points out of z range" % n_out_of_z_range

x1 = np.array(x1)
y1 = np.array(y1)
z1 = np.array(z1)
EValues = np.array(EValues)

print "Inverting..."
#Need a Array of (n,D) but have (D,n) so just swap indexing
points_inverted = np.array([x1,y1,z1])
points = np.swapaxes(points_inverted, 0, 1)
print "\tDone Invert"
print "N points (should be %i): %i" % (len(old_x1)-n_out_of_z_range-n_out_of_r_range-n_cut, len(points))
print "Dimensions (should be 3):", len(points[0])
print "points[0]:", points[0]

print "Gridding it up..."
#Function to get values on the grid
grid_E = griddata(points, EValues, (grid_x, grid_y, grid_z), method=method)
print "\tGrid Made"

print "grid size:"
print "\t x: %i | y: %i | z: %i" % (len(grid_E), len(grid_E[0]), len(grid_E[0,0]))

basename = os.path.basename(file_name)
tfile = ROOT.TFile("%s_%s_%imicron.root" % (basename, method, step_size*1e6), "recreate")

# introduce an offset so that hist bin centers are at grid points
offset = step_size*1e3/2.0

# the 3d field map hist
hist = ROOT.TH3F("hist",
    "3D field map, %i-micron step size, method=%s" % (step_size*1e6, method),
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    nbinsz, -offset, height*1e3+offset)

# a y slice hist
slice_hist = ROOT.TH2F("slice_hist",
    "2D projection of E-field at y=0, %.2f-mm step size" % (step_size*1e3), 
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    #nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    nbinsz, -offset, height*1e3+offset)
slice_hist.SetXTitle("x [mm]")
slice_hist.SetYTitle("z [mm]")

# a z slice hist
slice_histz = ROOT.TH2F("slice_histz",
    "2D projection of E-field at z=%.2fmm, %.2f-mm step size" % (step_size*1e3, step_size*1e3), 
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset, 
    nbinsx, -half_width*1e3-offset, half_width*1e3+offset) 
slice_histz.SetXTitle("x [mm]")
slice_histz.SetYTitle("y [mm]")

print "filling hist..."
#print "\n\nx | y | z | E"
for nx in np.arange(len(grid_E)):
    for ny in np.arange(len(grid_E[nx])):
        for nz in np.arange(len(grid_E[nx,ny])):
            xpos = grid_x[nx,ny,nz]
            ypos = grid_y[nx,ny,nz]
            zpos = grid_z[nx,ny,nz]
            EField = grid_E[nx, ny, nz]/100.0 # V/cm
            #print xpos*1e3, ypos*1e3, zpos*1e3, EField

            # find the right bin
            ibin = hist.FindBin(xpos*1e3, ypos*1e3, zpos*1e3-z_offset*1e3)
            content = hist.GetBinContent(ibin) # check for existing content

            if content != 0.0: # warn, if needed
                print "WARNING: hist bin %i already has content %i !!" % (ibin, content)

            hist.SetBinContent(ibin, EField) # Set hist bin content

            if math.fabs(ypos-0.0)<step_size*0.5: # fill slice_hist
                slice_hist.Fill(xpos*1e3, zpos*1e3-z_offset*1e3, EField)

            if math.fabs(zpos-z_offset-step_size)<step_size*0.5: # fill z slice_hist
                slice_histz.Fill(xpos*1e3, ypos*1e3, EField)
            # end loop over z coords
        # end loop over y coords
    # end loop over x coords

# write hists to file
hist.Write()
slice_hist.Write()
slice_histz.Write()

# make a plot
canvas = ROOT.TCanvas("canvas","")
canvas.SetRightMargin(0.15)
canvas.SetGrid()

# draw y slice
plot_name = "%s_EField_%s_%imicron" % (basename, method, step_size*1e6)
print "entries in slice_hist:", slice_hist.GetEntries()
slice_hist.Draw("colz")
canvas.Update()
canvas.Print("%s.pdf" % plot_name)
if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

# draw y slice zoom
slice_hist.SetAxisRange(-15, 15)
slice_hist.SetAxisRange(0, 5, "Y")
slice_hist.Draw("colz")
canvas.Update()
canvas.Print("%s_zoom.pdf" % plot_name)
if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

# draw z slice
plot_name = "%sz_EField_%s_%imicron" % (basename, method, step_size*1e6)
slice_histz.Draw("colz")
canvas.Update()
canvas.Print("%s.pdf" % plot_name)
if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

# draw z slice zoom
print "entries in slice_histz:", slice_histz.GetEntries()
slice_histz.SetAxisRange(-5, 15)
slice_histz.SetAxisRange(-5, 15, "Y")
slice_histz.Draw("colz")
canvas.Update()
canvas.Print("%s_zoom.pdf" % plot_name)
if not ROOT.gROOT.IsBatch():
    raw_input("enter to continue ")

