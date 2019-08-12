import numpy as np
import scipy.optimize as opt
import sys
import fit_funcs as ffs

import matplotlib.pyplot as plt
import matplotlib.colors as colors

class PeakFitter2D(object):

        def __init__(self, xdata, ydata):
            self.xdata = np.copy(xdata)
            self.ydata = np.copy(ydata)
            self.xwin  = [0,2000]
            self.ywin  = [0,2000]
            self.nbins = [50,50]
            
            self.hist   = None
            self.xcents = None
            self.ycents = None

            self.fit1d   = None
            self.guess1d = None
            self.p0      = None
            self.pf      = None

        #Set the X and Y data arrays
        def setData(self, xdata, ydata):
            self.setXdata(xdata)
            self.setYdata(ydata)
        def setXdata(self, data): 
            self.xdata = np.copy(data)
        def setYdata(self, data): 
            self.ydata = np.copy(data)

        #Set the window for the fitter
        def setWin(self, xwin, ywin):
            self.setXWin(xwin)
            self.setYWin(ywin)
        def setXWin(self, win):
            self.xwin = win
        def setYWin(self, win):
            self.ywin = win

        def setBins(self,nbins):
            self.nbins = nbins

        def setGuess(self, A, ux, uy, sigx, sigy, rho):
            #self.p0 = [100., 570., 570., 550*0.055, 100., -0.4]
            self.p0  = [A, ux, uy, sigx, sigy, rho]

        def makeHist(self):
            if len(self.xdata) != len(self.ydata):
                print "Error in building 2D hist arrays not equal sized", len(self.xdata), len(self.ydata)
                sys.exit()

            print self.nbins
            print self.xwin,self.ywin
            hist,xedges,yedges=np.histogram2d(self.xdata, self.ydata, bins=self.nbins, 
                                                    range = [self.xwin,self.ywin])
            
            xcents = (xedges[:-1] + xedges[1:])/2.
            ycents = (yedges[:-1] + yedges[1:])/2.

            self.hist   = hist
            self.xcents = xcents
            self.ycents = ycents
        
        def doFit(self, remake=False, min_cut=10):

            if remake==True or self.hist==None: self.makeHist()

            X,Y = np.meshgrid(self.xcents, self.ycents, indexing='ij')
            x1d, y1d = X.ravel(), Y.ravel()
            hist1d   = self.hist.ravel()
            err      = np.sqrt(hist1d)

            print "**************** min cut", np.max(hist1d)*0.005
            print np.max(hist1d)
        
            fpts = (hist1d > min_cut)

            print "passed and sum", np.sum(fpts), np.sum(hist1d)
            if np.sum(fpts) < len(self.p0) or np.sum(fpts)<100: 
                print self.p0
                print "skipped", np.sum(fpts) , len(self.p0)
                return -1

            self.guess1d = ffs.mult_var_gaus((x1d,y1d), *self.p0)
            try:
                coeff, var_matrix = opt.curve_fit(ffs.mult_var_gaus, (x1d[fpts], y1d[fpts]), hist1d[fpts],
                                                    p0=self.p0,
                                                    sigma=err[fpts])
            except:
                print "Fail"
                return -1

            
            self.pf = coeff

            fit1d   = ffs.mult_var_gaus((x1d,y1d), *coeff)
            fit1d.reshape(np.shape(X)).T
            self.fit1d = fit1d
            return 1

        def plotFit(self, fignum=1):
            #plt.figure(fignum, figsize=(11,7))
            #plt.clf()

            X,Y = np.meshgrid(self.xcents, self.ycents, indexing='ij')

            plt.imshow(self.hist.T, interpolation='nearest', origin='low', aspect='auto', cmap='CMRmap',
                                    extent=[self.xwin[0], self.xwin[1], self.ywin[0], self.ywin[1]],
                                    norm=colors.LogNorm(vmin=1, vmax=300))
            plt.colorbar()

            plt.contour(X,Y, self.fit1d.reshape(np.shape(X)),   3,   colors='k', linewidths=5, linestyles='--')
            plt.plot(self.pf[1], self.pf[2], marker='x', ms=30, mew=4, color='k')
            #plt.colorbar()
            plt.show()

        
        def plotGuess(self, fignum=1):
            #plt.figure(fignum, figsize=(11,7))
            #plt.clf()

            X,Y = np.meshgrid(self.xcents, self.ycents, indexing='ij')
            x1d, y1d = X.ravel(), Y.ravel()

            plt.imshow(self.hist.T, interpolation='nearest', origin='low', aspect='auto', cmap='CMRmap',
                                    extent=[self.xwin[0], self.xwin[1], self.ywin[0], self.ywin[1]],
                                    norm=colors.LogNorm(vmin=1, vmax=300))

            plt.colorbar()
            if self.guess1d==None:
                self.guess1d = ffs.mult_var_gaus((x1d,y1d), *self.p0)
            plt.contour(X,Y, self.guess1d.reshape(np.shape(X)),   3,   colors='k', linewidths=5)
            plt.show()


        def getMaxBin(self):
            X,Y = np.meshgrid(self.xcents, self.ycents, indexing='ij')
            mi = np.unravel_index(self.hist.argmax(), self.hist.shape)
            return X[mi], Y[mi]





