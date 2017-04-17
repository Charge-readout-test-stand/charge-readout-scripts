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
import matplotlib.pyplot as plt
from mc.digi import RalphWF
from mc import digi

def simple_gaus(s, tau):
    return 10.954/(0.83*tau*s+1.477)/(pow(0.83* tau*s+1.417, 2.0)+pow(0.598,2))/(pow(0.83* tau*s+1.204, 2)+pow(1.299,2))


def bessel(s, tau):
    return 1.0/(0.61* tau*s+0.9264)/(pow(0.61* tau*s,2) + 0.61*1.703*tau*s + 0.9211)/(pow(0.61* tau*s, 2) + 0.61*1.181*tau*s + 1.172)

tau = 1.0
s = 0

# physical constants
cathodeToAnodeDistance = 1e3 # mm
drift_velocity = 1.71 # mm/microsecond

# PCD coords
pcdx= 1.5 # mm
pcdy = 0.0
pcdz = 0.0 # at cathode
pcdz = cathodeToAnodeDistance - 50.0 # mm, distance from cathode

# options
sample_freq_MHz = 2.0 # nEXO digitizer
multiplier = 10.0 # oversample
sampling_period = 1.0/(sample_freq_MHz*multiplier) # microsecond (oversampled)
#dZ = cathodeToAnodeDistance/200.0
dZ = drift_velocity * sampling_period 
#wfm_length = int(cathodeToAnodeDistance/dZ)+1 # samples
wfm_length = int((cathodeToAnodeDistance-pcdz)/dZ)+20 # drift_time / sampling_period samples
sampling_period = dZ/drift_velocity

print "simple_gaus(%s, %s): %f" % (s, tau, simple_gaus(s, tau))
print "bessel(%s, %s): %f" % (s, tau, bessel(s, tau))


# a sample waveform, using Ralph's analytical method:
ralph_WF = digi.RalphWF.make_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz, Epcd=1, chID=15,
        cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ, wfm_length=wfm_length)

print "length of ralph_WF: ", len(ralph_WF)

# sampling time points
sample_times = np.arange(wfm_length)*sampling_period

plt.figure(1)
#Collection signal on channel X16
plt.title("Collection signal X16")
plt.xlabel("Time[$\mu$s]")
plt.ylabel("Q/Qtotal")
plt.grid(b=True)
plt.plot(sample_times, ralph_WF, 'o-')
plt.ylim([-np.max(ralph_WF)*0.1, np.max(ralph_WF)*1.1])
#plt.savefig("collect_X16.png")
#raw_input("press enter to continue ")

current_WF = digi.RalphWF.make_current_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz,
        Epcd=1, chID=15, cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
        wfm_length=wfm_length)
print "length of current_WF: ", len(current_WF)

current_WF_deriv = digi.RalphWF.make_current_from_derivative(xpcd=pcdx,
        ypcd=pcdy, zpcd=pcdz, Epcd=1, chID=15,
        cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
        wfm_length=wfm_length)
print "length of current_WF_deriv: ", len(current_WF_deriv)




plt.figure(2)
#Collection signal on channel X16
plt.title("Current signal X16")
plt.xlabel("Time[$\mu$s]")
plt.ylabel("I / Q_total")
plt.grid(b=True)
#plt.semilogy()
plt.plot(sample_times, current_WF,'.-')
plt.plot(sample_times[:-1], current_WF_deriv,'.-')
plt.ylim([-np.max(current_WF)*0.1, np.max(current_WF)*1.1])
#plt.savefig("collect_X16.png")
raw_input("press enter to continue ")



