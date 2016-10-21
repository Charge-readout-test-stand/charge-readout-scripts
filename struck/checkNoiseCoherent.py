import ROOT
import numpy as np
import matplotlib.pyplot as plt
import struck_analysis_parameters
import random
import os

tfile = ROOT.TFile("/p/lscratchd/jewell6/MCData_9thLXe/NoiseFiles/noiselib/NoiseLib_9thLXe.root")

tree = tfile.Get("tree")
events = tree.GetEntries()
print "Events in File = ", events

fig = plt.figure()
ax = plt.subplot(111)

event_list = np.arange(events)
random.shuffle(event_list)

time_step = 4e-8 #40ns
samps = 800 #samples
freqs = np.fft.fftfreq(samps, time_step)
freqs = np.abs(freqs[freqs<0]) #cut negative freqs but nyquist is only negative
freqs = np.append(freqs,0.0)
freqs = freqs[::-1]
freqs /= 1e3 #kHz

incoherent_sum_avg = np.zeros_like(freqs)
coherent_sum_avg = np.zeros_like(freqs)

n = 1000

for track, evi in enumerate(event_list[:n]):
    tree.GetEntry(evi)
    sum_wfm = np.zeros(samps)
    if track%10==0:print (1.0*track)/n
    for ich in xrange(32):
        if ich==27 or ich==31: continue
        name = struck_analysis_parameters.channel_map[ich]
        wfm_array = getattr(tree, "wfm%i"%ich)
        wfm_current = np.array([wfm_array[wfmi] for wfmi in xrange(800)])
        wfm_current -= np.mean(wfm_current)
        wfm_current *= struck_analysis_parameters.calibration_values[ich]
        sum_wfm += wfm_current
        
        fft = np.fft.rfft(wfm_current)
        incoherent_sum_avg += np.abs(fft)**2
    
    coherent_sum_avg += np.abs(np.fft.rfft(sum_wfm))**2

coherent_sum_avg /= n
incoherent_sum_avg /= n

ax.plot(freqs, incoherent_sum_avg,c='r',label='Incoherent Sum')
ax.plot(freqs, coherent_sum_avg,c='b', label='Coherent Sum')
lgd = ax.legend(loc='upper center',ncol=2, fancybox=True, shadow=True)


plt.xlabel("Freq[kHz]")
plt.ylabel("Power")
plt.title("Average Noise Power Spectrum")
plt.savefig("AvgPower.pdf",bbox_extra_artists=(lgd,), bbox_inches='tight')

plt.show()

