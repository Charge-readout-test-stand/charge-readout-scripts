import matplotlib.pyplot as plt
import scipy.optimize as opt
import numpy as np


def resFunc(x,A):
    return A/np.sqrt(x)

Elist = [570, 1060]
res_list     = [3.74, 2.70]
res_err_list = [0.12, 0.13]

res_list2     = [4.83, 3.34] 
res_err_list2 = [0.1, 0.1]

plt.ion()
plt.figure(1)

plt.errorbar(Elist, res_list, yerr=res_err_list, marker='o', ms = 10, 
            linestyle='None', color='b', label='Data(1kV/cm)')

plt.errorbar(Elist, res_list2, yerr=res_err_list2, marker='o', ms = 10, 
                    linestyle='None', color='r', label='Data(400V/cm)')

bp, bcov = opt.curve_fit(resFunc, Elist, res_list, p0=[1.0], sigma=res_err_list)
bp2, bcov2 = opt.curve_fit(resFunc, Elist, res_list2, p0=[1.0], sigma=res_err_list2)

efit = np.arange(0,3000,10)

plt.plot(efit, resFunc(efit, *bp), color='b')
plt.plot(efit, resFunc(efit, *bp2), color='r')

plt.plot([2457], [1.4], marker='*', ms=20, color='b', label='pCDR (CE:1%, E:1kV/cm)')
plt.plot([2457], [1.6], marker='*', ms=20, color='r', label='pCDR (CE:1%, E:400V/cm)')


plt.ylim(0.5, 6.0)
plt.xlim(100, 3000)

plt.legend(loc='upper right', numpoints=1)

plt.grid(True)

plt.xlabel("Energy [keV]", fontsize=17)
plt.ylabel("Resolution [%]", fontsize=17)

plt.savefig("plots/res_func.png")

plt.show()
raw_input()




