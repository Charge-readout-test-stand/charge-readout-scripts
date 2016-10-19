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

plt.ion()

fig = plt.figure()

event_list = np.arange(events)
random.shuffle(event_list)

merge_cmd = "gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=./noisetraces/NoiseTraces.pdf ./noisetraces/event*pdf"

time_step = 4e-8 #40ns
samps = 800 #samples
freqs = np.fft.fftfreq(samps, time_step)
freqs = np.abs(freqs[freqs<0]) #cut negative freqs but nyquist is only negative
freqs = np.append(freqs,0.0)
freqs = freqs[::-1]
freqs /= 1e3 #kHz

for evi in event_list[:50]:
    ax = plt.subplot(111)
    tree.GetEntry(evi)
    evn = tree.event

    sum_wfm = np.zeros(800)
    fft_list = []
    for ich in xrange(32):
        if ich==27 or ich==31: continue
        name = struck_analysis_parameters.channel_map[ich]
        wfm_array = getattr(tree, "wfm%i"%ich)
        wfm_current = np.array([wfm_array[wfmi] for wfmi in xrange(800)])
        #print ich, np.std(wfm_current[:200])
        wfm_current -= np.mean(wfm_current)
        wfm_current *= struck_analysis_parameters.calibration_values[ich]
        ax.plot((wfm_current + ich*200), label=name)
        sum_wfm += wfm_current

        fft = np.fft.rfft(wfm_current)
        fft_list.append( (name, fft))

    ax.plot(sum_wfm + 32*200, label="Sum WF")
    
    lgd = ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0),
              ncol=2, fancybox=True, shadow=True)
    
    plt.title("Calibrated Noise Traces Event %i" % evi)
    plt.ylim(-200,7000)
    plt.xlabel("Sample")
    plt.ylabel("Energy[keV] (200keV offset between channels)")
    plt.show()
    
    plt.savefig("./noisetraces/event%i.pdf" % evi, bbox_extra_artists=(lgd,), bbox_inches='tight')
    print "./noisetraces/event%i.pdf"% evi
    #raw_input()
    fig.clf()
    
    ax = plt.subplot(111)
    #ax.set_yscale('log')

    coherent_sum = np.abs(np.fft.rfft(sum_wfm))**2
    incoherent_sum = np.zeros_like(fft_list[0][1])

    for fft in fft_list:
        incoherent_sum += np.abs(fft[1])**2

    ax.plot(freqs, coherent_sum, label="Coherent Sum", c='r')
    ax.plot(freqs, incoherent_sum, label="Incoherent Sum", c='b')

    lgd = ax.legend(loc='upper center',
                    ncol=2, fancybox=True, shadow=True)
    
    plt.title("Power Spectrum Event %i" % evi)
    plt.xlabel("Freq[kHz]")
    plt.ylabel("Power")
    plt.xlim(-np.max(freqs)*0.01, np.max(freqs)*1.01)
    plt.show()
    plt.savefig("./noisetraces/event%i_fft.pdf" % evi, bbox_extra_artists=(lgd,), bbox_inches='tight')
    #raw_input()
    fig.clf()


os.system(merge_cmd)
os.system("rm -rf ./noisetraces/event*pdf")


