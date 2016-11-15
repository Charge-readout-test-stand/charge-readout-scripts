import ROOT
import numpy as np
import matplotlib.pyplot as plt
import struck_analysis_parameters
import random
import os,sys

#tfile = ROOT.TFile("/p/lscratchd/jewell6/MCData_9thLXe/NoiseFiles/noiselib/NoiseLib_9thLXe.root")
tfile = ROOT.TFile("NoiseLib_9thLXe.root")

tree = tfile.Get("tree")
events = tree.GetEntries()
print "Events in File = ", events


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
incoherent_sum_avgx = np.zeros_like(freqs)
incoherent_sum_avgy = np.zeros_like(freqs)
coherent_sum_avg = np.zeros_like(freqs)
coherent_sum_avgx = np.zeros_like(freqs)
coherent_sum_avgy = np.zeros_like(freqs)

n = 1000

plt.ion()

for track, evi in enumerate(event_list[:n]):
    
    tree.GetEntry(evi)
    sum_wfm = np.zeros(samps)
    #sum_fft = np.zeros_like(freqs)
    
    sum_wfmx = np.zeros(samps)
    sum_wfmy = np.zeros(samps)

    incoherent_sum = np.zeros_like(freqs)
    incoherent_sumx = np.zeros_like(freqs)
    incoherent_sumy = np.zeros_like(freqs)
    coherent_sum = np.zeros_like(freqs)
    coherent_sumx = np.zeros_like(freqs)
    coherent_sumy = np.zeros_like(freqs)
    rms_sum = 0
    rms_sumx = 0
    rms_sumy = 0

    if track%10==0:print (1.0*track)/n
    
    for ich in xrange(32):
        if ich==27 or ich==31 or ich==16: continue
        #if ich==27 or ich==31: continue
        name = struck_analysis_parameters.channel_map[ich]
        
        wfm_array = getattr(tree, "wfm%i"%ich)
        wfm_current = np.array([wfm_array[wfmi] for wfmi in xrange(800)])
        wfm_current -= np.mean(wfm_current)
        wfm_current *= struck_analysis_parameters.calibration_values[ich]
        sum_wfm += wfm_current
        rms_sum += np.std(wfm_current)**2

        fft = np.fft.rfft(wfm_current)
        fft_norm = fft/samps
        #sum_fft+=fft_norm
        incoherent_sum += 2*np.abs(fft_norm)**2
        
        if "X" in name:
            sum_wfmx+=wfm_current
            rms_sumx += np.std(wfm_current)**2
            incoherent_sumx += 2*np.abs(fft_norm)**2
        elif "Y" in name:
            sum_wfmy+=wfm_current
            incoherent_sumy += 2*np.abs(fft_norm)**2
            rms_sumy += np.std(wfm_current)**2
        else:
            print "??"
            sys.exit(0)

    #coherent_sum += 2*np.abs(sum_fft)**2
    sum_fft = np.fft.rfft(sum_wfm)/samps
    sum_fftx = np.fft.rfft(sum_wfmx)/samps
    sum_ffty = np.fft.rfft(sum_wfmy)/samps    

    coherent_sum += 2*np.abs(sum_fft)**2
    coherent_sumx += 2*np.abs(sum_fftx)**2
    coherent_sumy += 2*np.abs(sum_ffty)**2

    #RMS Noise in freq is integral of PS and should give same result
    #just a check
    print
    print "Integral Incoherennt", np.sqrt(np.sum(incoherent_sum))
    print "Sum of RMS", np.sqrt(rms_sum)

    print "Integral COherent", np.sqrt(np.sum(coherent_sum))
    print "Sum WFM RMS", np.std(sum_wfm)    
    
    print "----X----"
    print "Integral Incoherennt", np.sqrt(np.sum(incoherent_sumx))
    print "Sum of RMS", np.sqrt(rms_sumx)

    print "Integral COherent", np.sqrt(np.sum(coherent_sumx))
    print "Sum WFM RMS", np.std(sum_wfmx)

    print "----Y-----"
    print "Integral Incoherennt", np.sqrt(np.sum(incoherent_sumy))
    print "Sum of RMS", np.sqrt(rms_sumy)

    print "Integral COherent", np.sqrt(np.sum(coherent_sumy))
    print "Sum WFM RMS", np.std(sum_wfmy)
    

    print

    #plt.plot(sum_wfmy,c='r', label='y')
    #plt.plot(sum_wfmx,c='b', label='x')
    #lgd = plt.legend(loc='upper center',ncol=2, fancybox=True, shadow=True)
    #raw_input()
    #plt.clf()

    incoherent_sum_avg += incoherent_sum 
    incoherent_sum_avgx += incoherent_sumx
    incoherent_sum_avgy += incoherent_sumy
    coherent_sum_avg += coherent_sum
    coherent_sum_avgx += coherent_sumx
    coherent_sum_avgy += coherent_sumy


coherent_sum_avg /= n
coherent_sum_avgx /= n
coherent_sum_avgy /= n
incoherent_sum_avg /= n
incoherent_sum_avgx /= n
incoherent_sum_avgy /= n

plt.figure(1)
plt.plot(freqs, incoherent_sum_avg,c='r',label='Incoherent Sum')
plt.plot(freqs, coherent_sum_avg,c='b', label='Coherent Sum')
lgd = plt.legend(loc='upper center',ncol=2, fancybox=True, shadow=True)

plt.xlabel("Freq[kHz]")
plt.ylabel("Power")
plt.title("Average Noise Power Spectrum")
plt.savefig("AvgPower.pdf",bbox_extra_artists=(lgd,), bbox_inches='tight')


plt.figure(2)
plt.plot(freqs, incoherent_sum_avgx,c='r',label='Incoherent Sum')
plt.plot(freqs, coherent_sum_avgx,c='b', label='Coherent Sum')
lgd = plt.legend(loc='upper center',ncol=2, fancybox=True, shadow=True)

plt.xlabel("Freq[kHz]")
plt.ylabel("Power")
plt.title("Average Noise Power Spectrum X")
plt.savefig("AvgPowerX.pdf",bbox_extra_artists=(lgd,), bbox_inches='tight')


plt.figure(3)
plt.plot(freqs, incoherent_sum_avgy,c='r',label='Incoherent Sum')
plt.plot(freqs, coherent_sum_avgy,c='b', label='Coherent Sum')
lgd = plt.legend(loc='upper center',ncol=2, fancybox=True, shadow=True)

plt.xlabel("Freq[kHz]")
plt.ylabel("Power")
plt.title("Average Noise Power Spectrum Y")
plt.savefig("AvgPowerY.pdf",bbox_extra_artists=(lgd,), bbox_inches='tight')


plt.figure(4)
plt.plot(freqs, coherent_sum_avgx,c='r', label='Coherent Sum X')
plt.plot(freqs, coherent_sum_avgy,c='b', label='Coherent Sum Y')
lgd = plt.legend(loc='upper center',ncol=2, fancybox=True, shadow=True)

plt.xlabel("Freq[kHz]")
plt.ylabel("Power")
plt.title("Average Noise Power Spectrum X vs Y")
plt.savefig("AvgPowerXvY.pdf",bbox_extra_artists=(lgd,), bbox_inches='tight')



plt.show()
raw_input()
