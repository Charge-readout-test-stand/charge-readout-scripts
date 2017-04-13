"""
email from Angelo Dragone, 12 April 2017: transfer functions

Here are the transfer functions you should use to model the circuit response in
the simulations:

SG complex poles:
Htc(s,tau) = 10.954/(0.83*tau*s+1.477)/((0.83* tau*s+1.417)^2+0.598^2)/((0.83*
tau*s+1.204)^2+1.299^2);

Bessel:
Htbes(s,tau) = 1/(0.61* tau*s+0.9264)/((0.61* tau*s)^2 + 0.61*1.703* tau*s +
0.9211)/((0.61* tau*s)^2 + 0.61*1.181* tau*s + 1.172);

Where tau=1/(2*pi*fbw) and fbw is the max frequency content of the signal you
want to preserve

I have normalize them to a constant tau which is the inverse of the filter
bandwidth so that you can compare directly the two functions.
"""

import numpy as np
from scipy.fftpack import fft
from digi import RalphWF

def simple_gaus(s, tau):
    return 10.954/(0.83*tau*s+1.477)/(pow(0.83* tau*s+1.417, 2.0)+pow(0.598,2))/(pow(0.83* tau*s+1.204, 2)+pow(1.299,2))


def bessel(s, tau):
    return 1.0/(0.61* tau*s+0.9264)/(pow(0.61* tau*s,2) + 0.61*1.703*tau*s + 0.9211)/(pow(0.61* tau*s, 2) + 0.61*1.181*tau*s + 1.172)

tau = 1.0
s = 0



print "simple_gaus(%s, %s): %f" % (s, tau, simple_gaus(s, tau))
print "bessel(%s, %s): %f" % (s, tau, bessel(s, tau))


# a sample waveform:
pcdx= 1.5
pcdy = 0.0
pcdz = 0.0

sample_times = np.arange(800)*40*1e-3
plt.figure(1)
#Collection signal on channel X16
plt.title("Collection signal X16")
plt.xlabel("Time[$\mu$s]")
plt.ylabel("Q/Qtotal")
ralph_WF = RalphWF.make_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz, Epcd=1, chID=15)
plt.plot(sample_times, ralph_WF)
plt.ylim([-np.max(WF)*0.1, np.max(WF)*1.1])
#plt.savefig("collect_X16.png")



