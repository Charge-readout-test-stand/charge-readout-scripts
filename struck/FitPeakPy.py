import scipy.optimize as opt
import numpy as np


#For the Gaus + Exp Fit
def ffn(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3
    return gaus + exp

def ffn_sep(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3
    return gaus , exp

#For the Gaus + Exp Fit
def ffn_test(x, A1, mu, sig, E1, E2):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) 
    return gaus + exp

def ffn_sep_test(x, A1, mu, sig, E1, E2):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) 
    return gaus , exp


#For the Linear Fit
def ffn_lin(x, A1, mu, sig, L1, L2):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    lin  = L1*x + L2
    return gaus + lin

def ffn_lin_sep(x, A1, mu, sig, L1, L2):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    lin  = L1*x + L2
    return gaus ,lin

def FitPeakTest(hist_counts, hist_errors, bin_centers, peak_guess=570.0, fit_width=200):

    de = fit_width # Fit width
    peak_pos = peak_guess #bin_centers[np.argmax(hist_counts)]

    print "Peak Guess", peak_pos

    #Only fit the bins within a range de of the peak
    fit_min = peak_pos-de
    fit_max = peak_pos+de
    fpts = np.logical_and( bin_centers > peak_pos-de, bin_centers < peak_pos+de )

    print (hist_counts[fpts])[0], (hist_counts[fpts])[-1], fit_min, fit_max
    start_height = (hist_counts[fpts])[0]
    end_height   = (hist_counts[fpts])[-1]
    if end_height == 0: end_height = 1e-16
    if start_height == 0: start_height = 1.0
    #exp_decay_guess  = np.log(fit_max/fit_min)/(2*de)
    exp_decay_guess   = np.log(1.0*start_height/end_height)*(1/(2.0*de))
    exp_height_guess = (hist_counts[fpts])[0]*np.exp(fit_min*exp_decay_guess)
    sigma_guess  = 35.0
    height_guess = hist_counts[np.argmin(np.abs(bin_centers - peak_pos))] - exp_height_guess*np.exp(-exp_decay_guess*peak_pos)
    spars = [height_guess, peak_pos, sigma_guess, exp_height_guess, exp_decay_guess] #Initial guess for fitter

    print "Height Guess:", height_guess
    print "Sigma  Guess:", sigma_guess
    print "Peak Pos:", peak_pos
    print "Exp Height Guess:", exp_height_guess
    print "EXP Decay Guess", exp_decay_guess
    print abs((hist_counts[fpts])[0] - (hist_counts[fpts])[-1]), (2*de)
    print -1*np.log(abs((hist_counts[fpts])[0] - (hist_counts[fpts])[-1])/(2.0*de))

    fail = False

    #Perform the fit
    try:
        bp, bcov = opt.curve_fit(ffn_test, bin_centers[fpts], hist_counts[fpts], p0=spars, sigma=hist_errors[fpts])
    except RuntimeError:
        print "**********************Did not work*******************************"
        fail = True
        bp = spars
        bcov = np.eye(len(bp))

    #Get the x values for evaluating the function
    xx = np.linspace( bin_centers[fpts][0], bin_centers[fpts][-1], 1e3 )

    print ""
    print "-------Fit Results----------"
    print "Mean:  %.2f" % bp[1]
    print "Sigma: %.2f" % bp[2]
    print "EXP Decay Final", bp[4]
    print "----------------------------"
    print

    full_fit = ffn_test(xx, bp[0], bp[1], bp[2], bp[3], bp[4])
    gaus,exp = ffn_sep_test(xx, bp[0], bp[1], bp[2], bp[3], bp[4])

    return xx, bp, bcov, fail, full_fit, gaus, exp


def FitPeak(hist_counts, hist_errors, bin_centers, peak_guess=570.0, fit_width=200, sigma_guess=35):
    
    de = fit_width # Fit width
    peak_pos = peak_guess #bin_centers[np.argmax(hist_counts)]

    print "Peak Guess", peak_pos

    #Only fit the bins within a range de of the peak
    fit_min = peak_pos-de
    fit_max = peak_pos+de
    fpts = np.logical_and( bin_centers > peak_pos-de, bin_centers < peak_pos+de )

    print (hist_counts[fpts])[0], (hist_counts[fpts])[-1], fit_min, fit_max
    start_height = (hist_counts[fpts])[0]
    end_height   = (hist_counts[fpts])[-1]
    if end_height == 0: end_height = 1e-16
    if start_height == 0: start_height = 1.0
    #exp_decay_guess  = np.log(fit_max/fit_min)/(2*de)
    exp_decay_guess   = np.log(1.0*start_height/end_height)*(1/(2.0*de))
    exp_height_guess = (hist_counts[fpts])[0]*np.exp(fit_min*exp_decay_guess)
    height_guess = hist_counts[np.argmin(np.abs(bin_centers - peak_pos))] - exp_height_guess*np.exp(-exp_decay_guess*peak_pos)
    spars = [height_guess, peak_pos, sigma_guess, exp_height_guess, exp_decay_guess, 0.] #Initial guess for fitter

    print "Height Guess:", height_guess
    print "Sigma  Guess:", sigma_guess
    print "Peak Pos:", peak_pos
    print "Exp Height Guess:", exp_height_guess
    print "EXP Decay Guess", exp_decay_guess
    print abs((hist_counts[fpts])[0] - (hist_counts[fpts])[-1]), (2*de)
    print -1*np.log(abs((hist_counts[fpts])[0] - (hist_counts[fpts])[-1])/(2.0*de))

    fail = False

    #Perform the fit
    try:
        bp, bcov = opt.curve_fit(ffn, bin_centers[fpts], hist_counts[fpts], p0=spars, sigma=hist_errors[fpts])
        #bp, bcov = opt.curve_fit(ffn, bin_centers[fpts], hist_counts[fpts], p0=spars, sigma=hist_errors[fpts], 
        #                         bounds=([-np.inf, peak_pos-50, sigma_guess-5, -np.inf, -np.inf, -np.inf],
        #                                 [ np.inf, peak_pos+50, sigma_guess+5,  np.inf,  np.inf,  np.inf]))
    except RuntimeError:
        print "**********************Did not work*******************************"
        fail = True
        bp = spars
        bcov = np.eye(len(bp))

    #Get the x values for evaluating the function
    xx = np.linspace( bin_centers[fpts][0], bin_centers[fpts][-1], 1e3 )

    print ""
    print "-------Fit Results----------"
    print "Mean:  %.2f" % bp[1]
    print "Sigma: %.2f" % bp[2]
    print "EXP Decay Final", bp[4]
    print "----------------------------"
    print
    
    full_fit = ffn(xx, bp[0], bp[1], bp[2], bp[3], bp[4], bp[5])
    gaus,exp = ffn_sep(xx, bp[0], bp[1], bp[2], bp[3], bp[4], bp[5])    

    return xx, bp, bcov, fail, full_fit, gaus, exp
    

def FitPeakLinear(hist_counts, hist_errors, bin_centers,fit_width=190, peak_guess=570):
    de = fit_width # Fit width
    #peak_pos = 570.0 #bin_centers[np.argmax(hist_counts)]
    peak_pos = bin_centers[np.argmax(hist_counts)]
    if abs(peak_pos - peak_guess) > de: peak_pos = peak_guess
    
    hist_errors += 1.e-16

    print "Peak Guess", peak_pos

    #Only fit the bins within a range de of the peak
    fit_min = peak_pos-de
    fit_max = peak_pos+de
    fpts = np.logical_and( bin_centers > peak_pos-de, bin_centers < peak_pos+de )

    start_height = (hist_counts[fpts])[0]
    end_height   = (hist_counts[fpts])[-1]
    if end_height == 0: end_height = 1e-16
    if start_height == 0: start_height = 1.0
    sigma_guess  = 35.0

    slope_guess  = (1.0*(start_height-end_height))/(2*de)
    b_guess      = start_height - slope_guess*fit_min
    height_guess = hist_counts[np.argmin(np.abs(bin_centers - peak_pos))] - (slope_guess*peak_pos - b_guess)

    spars = [height_guess, peak_pos, sigma_guess, slope_guess, b_guess] #Initial guess for fitter

    print "Height Guess:", height_guess
    print "Sigma  Guess:", sigma_guess
    print "Peak Pos:", peak_pos
    print "Exp Height Guess:", slope_guess
    print "EXP Decay Guess", b_guess

    fail = False

    #Perform the fit
    try:
        bp, bcov = opt.curve_fit(ffn_lin, bin_centers[fpts], hist_counts[fpts], p0=spars, sigma=hist_errors[fpts])
    except RuntimeError:
        print "**********************Did not work*******************************"
        fail = True
        bp = spars
        bcov = np.eye(len(bp))
    
    #Get the x values for evaluating the function
    xx = np.linspace( bin_centers[fpts][0], bin_centers[fpts][-1], 1e3 )

    print ""
    print "-------Fit Results----------"
    print "Fail: %i" % fail
    print "Mean:  %.2f" % bp[1]
    print "Sigma: %.2f" % bp[2]
    print "----------------------------"
    print

    full_fit    = ffn_lin(xx, bp[0], bp[1], bp[2], bp[3], bp[4])
    gaus,linear = ffn_lin_sep(xx, bp[0], bp[1], bp[2], bp[3], bp[4])


    return xx, bp, bcov, fail, full_fit, gaus, linear






