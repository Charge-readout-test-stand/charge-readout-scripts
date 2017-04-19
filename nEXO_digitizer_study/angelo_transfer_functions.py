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

    #print "--transform: wfm [0], [-1]", wfm[0], wfm[-1]

    wfm_fft = fft(wfm)
    #print "--transform: wfm_fft [0], [-1]", wfm_fft[0], wfm_fft[-1]

    wfm_length = len(wfm)

    #transformed_wfm = np.zeros(len(wfm_fft)) 
    transformed_wfm = []
    for i, i_wfm in enumerate(wfm_fft):
        val = i_wfm*transfer_function(2*np.pi*i*1j/wfm_length, tau)
        transformed_wfm.append(val)
        #print i, i*1j, transformed_wfm[i] # debugging
    #print "--transform: transformed_wfm [0], [-1]", transformed_wfm[0], transformed_wfm[-1]

    transformed_wfm_ifft = ifft(transformed_wfm)
    #print "--transform: transformed_wfm_ifft [0], [-1]", transformed_wfm_ifft[0], transformed_wfm_ifft[-1]
    return np.abs(transformed_wfm_ifft)


# physical constants
cathodeToAnodeDistance = 1e3 # mm
drift_velocity = 1.71 # mm/microsecond

# PCD coords
pcdx= 1.5 # mm
pcdy = 0.0
#pcdz = 0.0 # at cathode
distanceFromAnode = 200.0 # mm
pcdz = cathodeToAnodeDistance - distanceFromAnode # mm
drift_time = distanceFromAnode / drift_velocity 

# options
sample_freq_MHz = 2.0 # nEXO digitizer baseline
oversampling_multiplier = 10 # oversampling multiplier
oversampled_freq_MHz = sample_freq_MHz*oversampling_multiplier
sampling_period = 1.0/oversampled_freq_MHz # microsecond (oversampled)
#dZ = cathodeToAnodeDistance/200.0
dZ = drift_velocity * sampling_period 
#wfm_length = int(cathodeToAnodeDistance/dZ)+1 # samples
wfm_length = int(distanceFromAnode/dZ) # drift_time / sampling_period samples

# extend waveform after charge arrives
padding_time = 100.0 # microseconds
padding_samples = int(padding_time/sampling_period)
#padding_samples = wfm_length
wfm_length += padding_samples
#sampling_period = dZ/drift_velocity


print "drift_length [mm]:", distanceFromAnode
print "drift time [microseconds]: ", distanceFromAnode/drift_velocity
print "sampling_period [microseconds]: ", sampling_period
print "dZ [mm]", dZ


# a sample waveform, using Ralph's analytical method:
ralph_WF = digi.RalphWF.make_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz, Epcd=1, chID=15,
        cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ, wfm_length=wfm_length)
ralph_WF = np.concatenate([np.zeros(padding_samples), ralph_WF]) # prepend padding zeros
print "length of ralph_WF [samples]: ", len(ralph_WF)

# sampling time points
sample_times = np.arange(wfm_length+padding_samples)*sampling_period

plt.figure(1)
#Collection signal on channel X16
plt.title("Collection signal X16: charge (%.1f, %.1f, %.1f) mm" % (pcdx, pcdy, distanceFromAnode))
plt.xlabel("Time  [$\mu s$]")
plt.ylabel("Q/Qtotal")
plt.grid(b=True)
plt.plot(sample_times, ralph_WF, '.-')
plt.ylim([-np.max(ralph_WF)*0.1, np.max(ralph_WF)*1.1])
plt.savefig("charge_signals_X16.png")
#raw_input("press enter to continue ")

current_WF = digi.RalphWF.make_current_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz,
        Epcd=1, chID=15, cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
        wfm_length=wfm_length)
current_WF = np.concatenate([np.zeros(padding_samples), current_WF]) # prepend padding zeros
#print "length of current_WF: ", len(current_WF)

current_WF_deriv = digi.RalphWF.make_current_from_derivative(xpcd=pcdx,
        ypcd=pcdy, zpcd=pcdz, Epcd=1, chID=15,
        cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
        wfm_length=wfm_length)
current_WF_deriv = np.concatenate([np.zeros(padding_samples), current_WF_deriv]) # prepend padding zeros
#print "length of current_WF_deriv: ", len(current_WF_deriv)

if False:
    plt.figure(2)
    #Collection signal on channel X16
    plt.title("Current signal X16: charge (%.1f, %.1f, %.1f) mm" % (pcdx, pcdy, distanceFromAnode))
    plt.xlabel("Time  [$\mu s$]")
    plt.ylabel("I / Q_total  [$\mu s^{-1}$]")
    plt.grid(b=True)
    plt.plot(sample_times, current_WF,'.-', label='instantaneous')
    plt.plot(sample_times[:-1], current_WF_deriv, '.-', label='calc from deriv of charge')
    #plt.semilogy()
    plt.ylim([-np.max(current_WF)*0.1, np.max(current_WF)*1.1])
    #plt.ylim([0, np.max(current_WF)*2])
    legend = plt.legend(loc='upper left')
    plt.savefig("current_signals_X16.png")
    #raw_input("press enter to continue ")

current_WF_fft = fft(current_WF)
#current_WF_fft = fft(current_WF_deriv)

# check a few things:
#print "current_WF_fft[0]:", current_WF_fft[0]
#print "current_WF_fft[-1]:", current_WF_fft[-1]

#print "current_WF_fft:"
#for i in xrange(len(current_WF_fft)):
#    print "\t", i, current_WF_fft[i]

new_current_WF = ifft(current_WF_fft)
# check a few things:
#print "new_current_WF[0]:", new_current_WF[0], np.abs(new_current_WF[0])
#print "new_current_WF[-1]:", new_current_WF[-1], np.abs(new_current_WF[-1])
new_current_WF = np.abs(new_current_WF)

# tau=1/(2*pi*fbw) and fbw is the max frequency content of the signal you want to preserve
fbw = 10.0 # units?!
tau = 1.0/(2.0*np.pi*fbw) 
s = 0
       
#print "simple_gaus(%s, %s): %f" % (s, tau, simple_gaus(s, tau))
#print "bessel(%s, %s): %f" % (s, tau, bessel(s, tau))

sg_filtered_current_WF = transform(current_WF, simple_gaus, tau)
be_filtered_current_WF = transform(current_WF, bessel, tau)

# undo oversamping -- go back to usual sampling rate:
# use numpy array slicing for this:
sample_times_sampled = sample_times[1::oversampling_multiplier]
current_WF_sampled = current_WF[1::oversampling_multiplier]
sg_filtered_current_WF_sampled = sg_filtered_current_WF[1::oversampling_multiplier]

# check a few things:
#print "sg_filtered_current_WF[0]:", sg_filtered_current_WF[0], np.abs(sg_filtered_current_WF[0])
#print "sg_filtered_current_WF[-1]:", sg_filtered_current_WF[-1], np.abs(sg_filtered_current_WF[-1])

for i in xrange(2):
    plt.figure(3+i)
    #Collection signal on channel X16
    plt.title("Current signal X16: charge (%.1f, %.1f, %.1f) mm" % (pcdx, pcdy, distanceFromAnode))
    plt.xlabel("Time  [$\mu s$]")
    plt.ylabel("I / Q_total  [$\mu s^{-1}$]")
    plt.grid(b=True)
    plt.plot(sample_times, current_WF,'.-', label='inst, %.1f MHz' % oversampled_freq_MHz)
    #plt.plot(sample_times[:-1], current_WF_deriv,'.-')
    #plt.plot(sample_times, new_current_WF,'-', label='after FFT/iFFT') # a test
    plt.plot(sample_times, sg_filtered_current_WF,'.-', label='after SG %.1f MHz' % oversampled_freq_MHz) # a test
    plt.plot(sample_times, be_filtered_current_WF,'.-', label='after Bessel %.1f MHz' % oversampled_freq_MHz) # a test

    # plot things sampled at baseline sampling freq, ~ 2 MHz
    plt.plot(sample_times_sampled, current_WF_sampled,'.-', label='inst, %.1f MHz' % sample_freq_MHz)
    plt.plot(sample_times_sampled, sg_filtered_current_WF_sampled,'.-', label='after SG, %.1f MHz' % sample_freq_MHz)

    legend = plt.legend(loc='upper left')
    if i > 0: # log y scale 
        plt.semilogy()
        plt.ylim([0, np.max(current_WF)*2])
    else: # lin y scale
        plt.ylim([-np.max(current_WF)*0.1, np.max(current_WF)*1.1])
        cathode_arrival_time = padding_time + drift_time
        plt.xlim([cathode_arrival_time - 2.0, cathode_arrival_time + 0.5 ])
    plt.savefig("current_signals_filtered_X16.png")
raw_input("press enter to continue ")

