import numpy as np
import scipy.optimize as opt
import sys
import fit_funcs as ffs

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import PeakFitter1D, PeakFitter2D

class ScanRotation(PeakFitter1D.PeakFitter1D):

    def __init__(self, xdata, ydata, trueE, name=None):

        PeakFitter1D.PeakFitter1D.__init__(self,np.zeros_like(xdata))
        self.theta_list  = None
        self.res_list    = None
        self.charge      = np.copy(xdata)
        self.scint       = np.copy(ydata)


        self.trueE       = trueE
        self.make_plots  = False
        self.name        = ""
        if name!=None:   self.set_make_plots(name)

    def set_trueE(self, trueE):
        self.trueE=trueE

    def set_make_plots(self, name):
        self.name = name
        self.make_plots = True

    def set_theta_list(self, theta_list):
        self.theta_list = theta_list
        self.res_list   = np.zeros((len(self.theta_list), 2))

    def get_rotated(self, theta, cal=1.0):
        rot_energy = (self.charge*np.cos(theta) + self.scint*np.sin(theta))
        norm = np.cos(theta) + np.sin(theta)
        rot_energy *= 1.0/norm
        self.setData((rot_energy*cal))
        self.makeHist()

    def ScanAngles(self):

        if self.make_plots:
            import matplotlib.backends.backend_pdf as PdfPages
            pdf = PdfPages.PdfPages("./plots/theta_scan/scan_res_theta_%s.pdf" % self.name)
            figtheta = plt.figure(1)
        for ti,theta in enumerate(self.theta_list):

            #Rotate the Energy and re-norm
            self.get_rotated(theta)
            check = self.doFit()
            
            print "check", check
            #Get the resolution and resolution error
            try:
                res     = (self.pf[2]/self.pf[1])*100
                res_err = (np.sqrt(np.abs(self.cov[2,2]))/self.pf[1])*100
                
            except:
                res     = 0
                res_err = 1.e16

            if check<0:
                res     = 0
                res_err = 1.e16
                self.pf  = self.p0

            #print "********************", res_err, self.cov

            self.res_list[ti][0] = res
            self.res_list[ti][1] = res_err

            if self.make_plots:
                figtheta.clf()
                figtheta.set_size_inches((9,6), forward=True)
                self.plotFit()
                plt.xlabel("Rotated Energy [keV]", fontsize=18)
                plt.ylabel("Counts", fontsize=18)
                

                res_string =  (r"$\theta$ = %.2f" % theta) + "\n"
                res_string += "E=%.2f keV \n" % self.pf[1]
                res_string += (r"$\sigma/E$ = %.2f" % (res)) + "%"
                

                ax=plt.gca()
                plt.text(0.8,0.75, res_string, bbox=dict(fc='none', lw=2, pad=15), horizontalalignment='center',
                        size=17, transform=ax.transAxes,)
                plt.xlim(self.win)
                pdf.savefig(figtheta)
                plt.show()
                #raw_input()

        self.FindBestAngle()

        if self.make_plots:
            figtheta.clf()
            figtheta.set_size_inches((9,5), forward=True)
            self.plot_angles()
            pdf.savefig(figtheta)
            pdf.close()


    def get_best_theta(self):
        return -self.poly_fit[1]/(2*self.poly_fit[0])

    def FindBestAngle(self):
        #Fit assuming quadratic
        
        #print "=================================="
        #print self.theta_list
        #print self.res_list[:,0]
        #print self.res_list[:,1]
        #print "=================================="
        
        self.poly_fit       = np.polyfit(self.theta_list, self.res_list[:,0], 2, w=1./self.res_list[:,1])
        
    def plot_angles(self, color='r'):
        plt.errorbar(self.theta_list, self.res_list[:,0], yerr=self.res_list[:,1],marker='o', linestyle='None', ms=6,c=color)
        plt.plot(self.theta_list, np.polyval(self.poly_fit, self.theta_list), linestyle='-', linewidth=3.0, c=color)
        plt.axvline(self.get_best_theta(), linestyle='--', linewidth=4.0, c=color)
        plt.ylim(np.min(self.res_list[:,0])*0.8, np.max(self.res_list[:,0])*1.2)

    def get_cal(self,theta):
        self.get_rotated(theta)
        self.doFit()
        return self.trueE/self.pf[1]

    def norm_hist(self):
        self.norm = 1.0/np.sum(self.hist)

    def plot_theta(self, theta=None, filled=True, color='r', cal=1.0, norm=False):
        
        if theta==None: 
            theta = self.get_best_theta()
            cal   = self.get_cal(theta)

        self.get_rotated(theta,cal=cal)
        self.doFit()
        #self.get_rotated(theta,cal=cal)
        
        if norm:
            self.norm_hist()

        if filled:
            #plt.step(self.cents, self.hist, where='mid',  , linewidth=2.0)
            plt.hist(self.data, bins=self.nbins, range=self.win, color=color,
                     facecolor=color, alpha=0.2,
                     linewidth=3.0, histtype='stepfilled')
            plt.hist(self.data, bins=self.nbins, range=self.win, color=color,
                     facecolor='None',linewidth=3.0, histtype='step')

            plt.errorbar(self.cents, self.hist,   yerr=np.sqrt(self.hist),
                            marker='.', ms=1, linestyle='None', c=color)
        
        else:
            self.plotFit()
            plt.xlabel("Rotated Energy [keV]", fontsize=18)
            plt.ylabel("Counts", fontsize=18)

            res        = (self.pf[2]/self.pf[1])*100
            res_string =  (r"$\theta$ = %.2f" % theta) + "\n"
            res_string += "E=%.2f keV \n" %  self.pf[1]
            res_string += (r"$\sigma/E$ = %.2f" % (res)) + "%"


            ax=plt.gca()
            plt.text(0.8,0.75, res_string, bbox=dict(fc='none', lw=2, pad=15), horizontalalignment='center',
                    size=17, transform=ax.transAxes,)
            plt.xlim(self.win)




    def plot2D(self, cbins, clim, sbins, slim, vmax=100):
        plt.hist2d(self.charge, self.scint, bins=[cbins, sbins], range=[clim,slim], norm=colors.LogNorm(vmin=1,vmax=vmax))
        plt.xlim(clim)
        plt.ylim(slim)




