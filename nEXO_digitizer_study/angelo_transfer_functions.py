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
    return 10.954/(0.83*tau*s+1.477)/(pow(0.83*tau*s+1.417, 2.0)+pow(0.598,2))/(pow(0.83*tau*s+1.204,2)+pow(1.299,2))

def bessel(s, tau):
    return 1.0/(0.61*tau*s+0.9264)/(pow(0.61*tau*s,2) + 0.61*1.703*tau*s + 0.9211)/(pow(0.61*tau*s,2) + 0.61*1.181*tau*s + 1.172)

def transform(wfm, transfer_function, tau):
    """
    FFT the wfm
    multiply wfm FFT by transfer function
    iFFT the product & return
    """

    wfm_fft = fft(wfm) # FFT of input wfm

    wfm_length = len(wfm) # wfm length

    # multiply wfm fft by transfer_function 
    transformed_wfm = []
    for k, i_wfm in enumerate(wfm_fft):
        val = i_wfm*transfer_function(2*np.pi*k*1j/wfm_length, tau)
        transformed_wfm.append(val)

    transformed_wfm_ifft = ifft(transformed_wfm) # ifft
    return np.abs(transformed_wfm_ifft)


def digitize(wfm, max_val=4e5, bits=11):
    """
    quantize wfm into ADC units
    """
    digitized_wfm = []
    for i_wfm in wfm:
        new_val = int(i_wfm/max_val*pow(2,bits))*max_val/pow(2,bits)
        digitized_wfm.append(new_val)
    return digitized_wfm

def main():

    # physical constants
    cathodeToAnodeDistance = 1e3 # mm
    drift_velocity = 1.71 # mm/microsecond

    # PCD coords
    pcdx= 1.5 # mm, centered over one pad
    pcdy = 0.0 # centered over strip
    distanceFromAnode = 200.0 # mm
    distanceFromAnode = 1e3 # mm
    pcdz = cathodeToAnodeDistance - distanceFromAnode # mm
    drift_time = distanceFromAnode / drift_velocity 
    Epcd = 2457.8 * 48.0 # electrons (bb0n Q-val * e-s per keV, from NEST)
    "electrons in 0nbb deposit:", Epcd

    # options
    sample_freq_MHz = 2.0 # nEXO digitizer baseline
    oversampling_multiplier = 20 # oversampling multiplier
    oversampled_freq_MHz = sample_freq_MHz*oversampling_multiplier
    sampling_period = 1.0/oversampled_freq_MHz # microsecond (oversampled)
    dZ = drift_velocity * sampling_period 
    wfm_length = int(distanceFromAnode/dZ) # drift_time / sampling_period samples

    # extend waveform after charge arrives
    padding_time = 600.0 # microseconds
    padding_samples = int(padding_time/sampling_period)
    wfm_length += padding_samples
    cathode_arrival_time = padding_time + drift_time
    #sampling_period = dZ/drift_velocity

    # print some info:
    print "baseline sampling freq [MHz]", sample_freq_MHz
    print "oversampling_multiplier:", oversampling_multiplier
    print "oversampled_freq_MHz:", oversampled_freq_MHz
    print "drift_length [mm]:", distanceFromAnode
    print "drift time [microseconds]: ", distanceFromAnode/drift_velocity
    print "sampling_period [microseconds] (oversampled): ", sampling_period
    print "dZ [mm] (oversampled)", dZ

    # sampling time points
    sample_times = np.arange(wfm_length+padding_samples)*sampling_period

    # a sample waveform, using Ralph's analytical method:
    if False:
        ralph_WF = digi.RalphWF.make_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz, Epcd=Epcd, chID=15,
                cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ, wfm_length=wfm_length)
        ralph_WF = np.concatenate([np.zeros(padding_samples), ralph_WF]) # prepend padding zeros

        # plot charge signal
        plt.figure(1)
        #Collection signal on channel X16
        plt.title("Collection signal X16: charge (%.1f, %.1f, %.1f) mm" % (pcdx, pcdy, distanceFromAnode))
        plt.xlabel("Time  [$\mu s$]")
        if Epcd == 1: 
            plt.ylabel("Q/Qtotal")
        else:
            plt.ylabel("Q [e$^-$s]")
        plt.grid(b=True)
        plt.plot(sample_times, ralph_WF, '.-')
        plt.ylim([-np.max(ralph_WF)*0.1, np.max(ralph_WF)*1.1])
        plt.savefig("charge_signals_X16.png")
        #raw_input("press enter to continue ")

    # current wfm, from analytical expression
    current_WF = digi.RalphWF.make_current_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz,
            Epcd=Epcd, chID=15, cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
            wfm_length=wfm_length)
    current_WF = np.concatenate([np.zeros(padding_samples), current_WF]) # prepend padding zeros
    print "length of current_WF: ", len(current_WF)

    # compare current wfms calculated from instantaneous & numerical derivatives
    if False:
        # current wfm, from numerical derivative of charge wfm
        current_WF_deriv = digi.RalphWF.make_current_from_derivative(xpcd=pcdx,
                ypcd=pcdy, zpcd=pcdz, Epcd=Epcd, chID=15,
                cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
                wfm_length=wfm_length)
        current_WF_deriv = np.concatenate([np.zeros(padding_samples), current_WF_deriv]) # prepend padding zeros
        #print "length of current_WF_deriv: ", len(current_WF_deriv)

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

    # tau=1/(2*pi*fbw) and fbw is the max frequency content of the signal you want to preserve
    #fbw = oversampling_multiplier*0.5 # MHz ?! not sure about units
    fbw = 1.0/oversampling_multiplier/2.0
    print "fbw:", fbw
    tau = 1.0/(2.0*np.pi*fbw) 
    s = 0

    # test impulse response
    do_impulse_response = False
    if do_impulse_response:
        current_WF = np.zeros(len(current_WF))
        current_WF[int(cathode_arrival_time/sampling_period)] = 1.0
           
    # filter the current wfm
    sg_filtered_current_WF = transform(current_WF, simple_gaus, tau)
    be_filtered_current_WF = transform(current_WF, bessel, tau)

    # undo oversamping -- go back to usual sampling rate:
    # use numpy array slicing for this:
    sample_times_sampled = sample_times[1::oversampling_multiplier]
    current_WF_sampled = current_WF[1::oversampling_multiplier]
    sg_filtered_current_WF_sampled = sg_filtered_current_WF[1::oversampling_multiplier]

    sg_digitized_wfm = digitize(sg_filtered_current_WF_sampled)


    # draw current after SG & Bessel filters, in lin and log scale
    for i in xrange(2): # lin, then log
        plt.figure(3+i)
        #Collection signal on channel X16
        plt.title("Current signal X16: charge (%.1f, %.1f, %.1f) mm" % (pcdx, pcdy, distanceFromAnode))
        plt.xlabel("Time  [$\mu s$]")
        if Epcd == 1.0:
            plt.ylabel("Current / Q_total  [$\mu s^{-1}$]")
        else:
            plt.ylabel("Current [e$^-$/$\mu s$]")
            
        plt.grid(b=True)
        if not do_impulse_response:
            plt.plot(sample_times, current_WF,'.-', label='inst, %.1f MHz' % oversampled_freq_MHz)
            #plt.plot(sample_times[:-1], current_WF_deriv,'.-')
        plt.plot(sample_times, sg_filtered_current_WF,'-', label='SG (fbw=%.3f) %i MHz' % (fbw, oversampled_freq_MHz)) # a test
        plt.plot(sample_times, be_filtered_current_WF,'-', label='Bessel (fbw=%.3f) %i MHz' % (fbw, oversampled_freq_MHz)) # a test

        # plot things sampled at baseline sampling freq, ~ 2 MHz
        #plt.plot(sample_times_sampled, current_WF_sampled,'.-', label='inst, %i MHz' % sample_freq_MHz)
        plt.plot(sample_times_sampled, sg_filtered_current_WF_sampled,'.-', label='SG, %i MHz' % sample_freq_MHz)
        plt.plot(sample_times_sampled, sg_digitized_wfm,'.-', label='SG, digitization, %i MHz' % sample_freq_MHz)

        legend = plt.legend(loc='upper left', ncol=2)
        if i > 0: # log y scale 
            plt.semilogy()
            plt.ylim([0, np.max(current_WF)*100])
        else: # lin y scale, zoom in on x axis
            plt.ylim([-np.max(current_WF)*0.05, np.max(current_WF)*1.3])
            plt.xlim([cathode_arrival_time-7.0, cathode_arrival_time+7.0 ])
            if do_impulse_response:
                plt.ylim([-np.max(sg_filtered_current_WF)*0.1, np.max(sg_filtered_current_WF)*2])
                plt.xlim([cathode_arrival_time-1.0, cathode_arrival_time+3.0 ])
        plt.savefig("current_signals_filtered_X16.png")

    # trapezoidal filtering
    #try:
    if False:
        import ROOT
        print "loading libEXOROOT"
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
        from ROOT import EXOTrapezoidalFilter
        from ROOT import EXODoubleWaveform
        from array import array
        canvas = ROOT.TCanvas("canvas","")
        canvas.SetGrid()
        trap_filter = EXOTrapezoidalFilter()
        #trap_filter.SetFlatTime(10e3)
        trap_filter.SetRampTime(500) # ns
        trap_filter.SetFlatTime(10.0*trap_filter.GetRampTime())
        trap_filter.SetDecayConstant(trap_filter.GetRampTime())
        #wfm = sg_digitized_wfm
        wfm = sg_filtered_current_WF
        #wfm = current_WF

        # impulse wfm, for testing
        #wfm = np.zeros(len(current_WF))
        #wfm[int(cathode_arrival_time/sampling_period)] = 1.0

        exo_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
        trap_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
        #trap_wfm.SetSamplingFreq(sample_freq_MHz/1000.0)
        trap_wfm.SetSamplingFreq(sample_freq_MHz*oversampling_multiplier/1000.0)
        exo_wfm.SetSamplingFreq(sample_freq_MHz*oversampling_multiplier/1000.0)
        trap_filter.Transform(trap_wfm)
        hist = trap_wfm.GimmeHist("trap_hist")
        hist2 = exo_wfm.GimmeHist("exo_hist")
        hist.SetTitle("flat time: %.1f, ramp time: %.1f" % (trap_filter.GetFlatTime(), trap_filter.GetRampTime()))
        hist.SetLineColor(ROOT.kBlue)
        hist.SetMarkerColor(ROOT.kBlue)
        hist2.SetLineColor(ROOT.kRed)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.4)
        hist.SetAxisRange(cathode_arrival_time-10.0, cathode_arrival_time+10.0)
        hist.Draw("pl")
        hist2.Draw("l same")
    #except: print "trap fail"

    raw_input("press enter to continue ")
    # end of main()

if __name__ == "__main__":
    main()

