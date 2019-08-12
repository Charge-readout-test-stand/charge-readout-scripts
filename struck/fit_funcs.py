import numpy as np

def mult_var_gaus((X,Y), *p):
    A,ux,uy,sx,sy,rho = p
    #X,Y = np.meshgrid(x,y)
    assert rho != 1
    a= -1 / (2*(1-rho**2))

    exp =  ((X - ux)/sx)**2
    exp += ((Y - uy)/sy)**2
    exp += -1*(2*rho*(X - ux)*(Y - uy))/(sx*sy)

    Z = A*np.exp(a*exp)
    #return Z.ravel()
    return Z


def ffn(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3
    return gaus + exp

def ffn_sep(x, A1, mu, sig, E1, E2, E3):
    gaus = A1*np.exp(-(x-mu)**2/(2*sig**2))
    exp  = E1*np.exp(-E2*x) + E3
    return gaus , exp

#For the Gaus + Exp Fit
def ffn_gaus_exp(x, A1, mu, sig, E1, E2):
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




