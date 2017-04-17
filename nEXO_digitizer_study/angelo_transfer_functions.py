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
from scipy.fftpack import ifft
import matplotlib.pyplot as plt
from mc.digi import RalphWF
from mc import digi

def simple_gaus(s, tau):
    return 10.954/(0.83*tau*s+1.477)/(pow(0.83* tau*s+1.417, 2.0)+pow(0.598,2))/(pow(0.83* tau*s+1.204, 2)+pow(1.299,2))


def bessel(s, tau):
    return 1.0/(0.61* tau*s+0.9264)/(pow(0.61* tau*s,2) + 0.61*1.703*tau*s + 0.9211)/(pow(0.61* tau*s, 2) + 0.61*1.181*tau*s + 1.172)

def transform(wfm, transfer_function, tau):
    """
    FFT the wfm
    multiply wfm FFT by transfer function
    iFFT the product & return
    """

    print "--transform: wfm [0], [-1]", wfm[0], wfm[-1]

    wfm_fft = fft(wfm)
    print "--transform: wfm_fft [0], [-1]", wfm_fft[0], wfm_fft[-1]

    #transformed_wfm = np.zeros(len(wfm_fft)) 
    transformed_wfm = []
    for i, i_wfm in enumerate(wfm_fft):
        val = i_wfm*transfer_function(i*1j, tau)
        transformed_wfm.append(val)
        #print i, i*1j, transformed_wfm[i] # debugging
    print "--transform: transformed_wfm [0], [-1]", transformed_wfm[0], transformed_wfm[-1]

    transformed_wfm_ifft = ifft(transformed_wfm)
    print "--transform: transformed_wfm_ifft [0], [-1]", transformed_wfm_ifft[0], transformed_wfm_ifft[-1]
    #return transformed_wfm
    return transformed_wfm_ifft


# physical constants
cathodeToAnodeDistance = 1e3 # mm
drift_velocity = 1.71 # mm/microsecond

# PCD coords
pcdx= 1.5 # mm
pcdy = 0.0
#pcdz = 0.0 # at cathode
distanceFromAnode = 5.0 # mm
pcdz = cathodeToAnodeDistance - distanceFromAnode # mm

# options
sample_freq_MHz = 2.0 # nEXO digitizer baseline
multiplier = 10.0 # oversampling multiplier
sampling_period = 1.0/(sample_freq_MHz*multiplier) # microsecond (oversampled)
#dZ = cathodeToAnodeDistance/200.0
dZ = drift_velocity * sampling_period 
#wfm_length = int(cathodeToAnodeDistance/dZ)+1 # samples
wfm_length = int((cathodeToAnodeDistance-pcdz)/dZ)+20 # drift_time / sampling_period samples
sampling_period = dZ/drift_velocity

print "drift_length [mm]:", cathodeToAnodeDistance-pcdz
print "sampling_period [microseconds]: ", sampling_period
print "dZ [mm]", dZ


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
#raw_input("press enter to continue ")

current_WF_fft = fft(current_WF)
#current_WF_fft = fft(current_WF_deriv)

# check a few things:
print "current_WF_fft[0]:", current_WF_fft[0]
print "current_WF_fft[-1]:", current_WF_fft[-1]

#print "current_WF_fft:"
#for i in xrange(len(current_WF_fft)):
#    print "\t", i, current_WF_fft[i]

new_current_WF = ifft(current_WF_fft)
# check a few things:
print "new_current_WF[0]:", new_current_WF[0], np.abs(new_current_WF[0])
print "new_current_WF[-1]:", new_current_WF[-1], np.abs(new_current_WF[-1])

# tau=1/(2*pi*fbw) and fbw is the max frequency content of the signal you want to preserve
fbw = 500.0
tau = 1.0/(2.0*np.pi*fbw) 
s = 0
       
print "simple_gaus(%s, %s): %f" % (s, tau, simple_gaus(s, tau))
print "bessel(%s, %s): %f" % (s, tau, bessel(s, tau))

sg_filtered_current_WF = transform(current_WF, simple_gaus, tau)
be_filtered_current_WF = transform(current_WF, bessel, tau)

# check a few things:
print "sg_filtered_current_WF[0]:", sg_filtered_current_WF[0], np.abs(sg_filtered_current_WF[0])
print "sg_filtered_current_WF[-1]:", sg_filtered_current_WF[-1], np.abs(sg_filtered_current_WF[-1])

plt.figure(3)
#Collection signal on channel X16
plt.title("Current signal X16")
plt.xlabel("Time[$\mu$s]")
plt.ylabel("I / Q_total")
plt.grid(b=True)
#plt.semilogy()
plt.plot(sample_times, current_WF,'.', label='current wfm')
#plt.plot(sample_times[:-1], current_WF_deriv,'.-')
plt.plot(sample_times, np.abs(new_current_WF),'-', label='after FFT/iFFT') # a test
plt.plot(sample_times, np.abs(sg_filtered_current_WF),'.-', label='after SG') # a test
plt.plot(sample_times, np.abs(be_filtered_current_WF),'.-', label='after SG') # a test
legend = plt.legend(loc='upper left')
plt.ylim([-np.max(current_WF)*0.1, np.max(current_WF)*1.1])
#plt.savefig("collect_X16.png")
#raw_input("press enter to continue ")




raw_input("press enter to continue ")
