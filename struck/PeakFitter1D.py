import numpy as np
import scipy.optimize as opt
import sys
import fit_funcs as ffs

import matplotlib.pyplot as plt
import matplotlib.colors as colors

class PeakFitter1D(object):

    def __init__(self, xdata):
        self.data  = np.copy(xdata)
        self.win   = [0,2000]
        self.nbins = 100
        self.de    = 200

        self.hist   = None
        self.cents = None

        self.fit   = None
        self.guess = None
        self.p0      = None
        self.pf      = None
        self.cov     = None

        self.xfit     = None
        self.full_fit = None
        self.gaus     = None
        self.back     = None


    def setData(self, data): self.data = np.copy(data)
    def setXWin(self, win):  self.win = win
    def setBins(self,nbins): self.nbins = nbins
    def setWidth(self, width): self.de=width
    
    def setGuess(self, ux, sigx):
        self.peak_guess = ux
        self.sig_guess  = sigx

    def makeHist(self):
        counts,edges=np.histogram(self.data, bins=self.nbins, range=self.win)
        cents = edges[:-1] + np.diff(edges)/2.0
        
        self.cents = cents
        self.hist  = counts
    
    def doFit(self, remake=False, min_cut=10):
        peak_pos = self.peak_guess

        fit_min = peak_pos-self.de
        fit_max = peak_pos+self.de
        fpts = np.logical_and( self.cents > fit_min, self.cents < fit_max )
        
        start_height =  (self.hist[fpts])[0]
        end_height   =  (self.hist[fpts])[-1]
    
        if end_height == 0: end_height = 1e-16
        if start_height == 0: start_height = 1.0
        
        exp_decay_guess   = np.log(1.0*start_height/end_height)*(1/(2.0*self.de))
        exp_height_guess  = start_height*np.exp(fit_min*exp_decay_guess)
        height_guess      = self.hist[np.argmin(np.abs(self.cents - peak_pos))] -  exp_height_guess*np.exp(-exp_decay_guess*peak_pos)
        self.p0           = [height_guess, peak_pos, self.sig_guess, exp_height_guess, exp_decay_guess]        

        hist_errors = np.sqrt(self.hist)
        fail = False
        try:
            bp, bcov = opt.curve_fit(ffs.ffn_gaus_exp, self.cents[fpts], self.hist[fpts], p0=self.p0, 
                                            sigma=hist_errors[fpts])
            self.pf  = bp
            self.cov = bcov
        except RuntimeError:
            print "**********************Did not work*******************************"
            fail = True
            bp   = self.p0
            bcov = np.eye(len(bp))
            self.cov = bcov
            self.pf  = bp
            return -1
        
        self.xfit = np.linspace( self.cents[fpts][0], self.cents[fpts][-1], 1e3 )
        
        self.full_fit       = ffs.ffn_gaus_exp(self.xfit, *bp)
        self.gaus,self.back = ffs.ffn_sep_test(self.xfit, *bp)
        return 1

    
    def plotFit(self, fignum=1):
        #plt.figure(fignum)
        #plt.clf()

        plt.errorbar(self.cents, self.hist,   yerr=np.sqrt(self.hist), 
                            marker='o', linestyle='None', c='k')
        
        plt.plot(self.xfit, self.full_fit, color='r', linewidth=3, linestyle='-')
        plt.plot(self.xfit, self.gaus, color='c', linewidth=3, linestyle='-', label='gaus')
        plt.plot(self.xfit, self.back, color='g', linewidth=3, linestyle='-', label='back')
        
        plt.show()

        return

    def plotGuess(self, fignum=1):    
        return 



