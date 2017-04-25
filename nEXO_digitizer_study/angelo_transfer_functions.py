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
import matplotlib
matplotlib.use('Agg') # batch mode
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


def digitize(wfm, max_val=3.0, bits=11):
    """
    quantize wfm into ADC units
    """
    digitized_wfm = []
    for i_wfm in wfm:
        new_val = int(i_wfm/max_val*pow(2,bits))*max_val/pow(2,bits)
        digitized_wfm.append(new_val)
    return digitized_wfm

def main():

    # options
    do_draw_current = False # draw current after SG & Bessel filters, in lin and log scale
    do_trap_filter = False # EXOTrapezoidalFilter
    do_draw_charge = False # draw RalphWF.make_WF and integrated current wfm
    do_compare_current_wfms = False
    do_calc_sum_channel = False # print final charge induced on strip, for debugging

    # physical constants
    cathodeToAnodeDistance = 1e3 # mm
    drift_velocity = 1.71 # mm/microsecond
    digi.RalphWF.drift_velocity = drift_velocity

    # PCD coords
    pcdx= 1.5 # mm, centered over one pad
    pcdy = 0.0 # centered over strip
    distanceFromAnode = 200.0 # mm
    distanceFromAnode = 1e3 # mm
    pcdz = cathodeToAnodeDistance - distanceFromAnode # mm
    drift_time = distanceFromAnode / drift_velocity 
    chID=15
    #Epcd = 2457.8 * 48.0 # electrons (bb0n Q-val * e-s per keV, from NEST)
    Epcd = 1.0
    "electrons in 0nbb deposit:", Epcd

    # options
    baseline_sampling_freq_MHz = 2.0 # nEXO digitizer baseline
    oversampling_multiplier = 20 # oversampling multiplier
    oversampled_freq_MHz = baseline_sampling_freq_MHz*oversampling_multiplier
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
    print "baseline sampling freq [MHz]", baseline_sampling_freq_MHz
    print "oversampling_multiplier:", oversampling_multiplier
    print "oversampled_freq_MHz:", oversampled_freq_MHz
    print "drift_length [mm]:", distanceFromAnode
    print "drift time [microseconds]: ", distanceFromAnode/drift_velocity
    print "sampling_period [microseconds] (oversampled): ", sampling_period
    print "dZ [mm] (oversampled)", dZ

    # sampling time points
    oversampled_sample_times = np.arange(wfm_length+padding_samples)*sampling_period
    # undo oversamping -- go back to usual sampling rate:
    # use numpy array slicing for this:
    baseline_sampling_times = oversampled_sample_times[1::oversampling_multiplier]

    if do_draw_current or do_draw_charge or do_trap_filter:

        # current wfm, from analytical expression
        print "---> calculating current WF"
        current_WF = digi.RalphWF.make_current_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz,
                Epcd=Epcd, chID=chID, cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
                wfm_length=wfm_length)
        current_WF = np.concatenate([np.zeros(padding_samples), current_WF]) # prepend padding zeros
        print "length of current_WF [samples]: ", len(current_WF)


    # compare current wfms calculated from instantaneous & numerical derivatives
    if do_compare_current_wfms:

        # current wfm, from numerical derivative of charge wfm
        current_WF_deriv = digi.RalphWF.make_current_from_derivative(xpcd=pcdx,
                ypcd=pcdy, zpcd=pcdz, Epcd=Epcd, chID=chID,
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
        plt.plot(oversampled_sample_times, current_WF,'.-', label='instantaneous')
        plt.plot(oversampled_sample_times[:-1], current_WF_deriv, '.-', label='calc from deriv of charge')
        #plt.semilogy()
        plt.xlim([cathode_arrival_time-3.0, cathode_arrival_time+1.0 ])
        plt.ylim([-np.max(current_WF)*0.1, np.max(current_WF)*1.1])
        #plt.ylim([0, np.max(current_WF)*2])
        legend = plt.legend(loc='upper left')
        plt.savefig("current_signals_X16.png")
        #raw_input("press enter to continue ")

    # tau=1/(2*pi*fbw) and fbw is the max frequency content of the signal you want to preserve
    ###fbw = baseline_sampling_freq_MHz*0.5 # MHz ?! not sure about units
    fbw = 1.0/oversampling_multiplier/2.0 # 1 MHz, I think 
    #fbw = 1.0/oversampling_multiplier/2.0/4.0 # 250 kHz, per Ralph
    print "fbw:", fbw
    tau = 1.0/(2.0*np.pi*fbw) 
    print "tau [fraction of sampling period]:", tau
    print "tau [microseconds]:", tau*sampling_period

    
    adc_bits = 12
    adc_max = 1.0
    if fbw == 1.0/oversampling_multiplier/2.0:
        adc_max = 3.0

    if do_draw_current or do_draw_charge or do_trap_filter:

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
        current_WF_sampled = current_WF[1::oversampling_multiplier]
        sg_filtered_current_WF_sampled = sg_filtered_current_WF[1::oversampling_multiplier]

        sg_digitized_wfm = digitize(sg_filtered_current_WF_sampled, max_val=adc_max, bits=adc_bits)

    # draw current after SG & Bessel filters, in lin and log scale
    if do_draw_current:
        for i in xrange(1): # lin, then log
            plt.figure(3+i)
            #Collection signal on channel X16
            plt.title("Current signal X16: charge (%.1f, %.1f, %.1f) mm" % (pcdx, pcdy, distanceFromAnode))
            plt.xlabel("Time  [$\mu s$]")
            if Epcd == 1.0: # special labels for unit signal
                plt.ylabel("Current / Q_total  [$\mu s^{-1}$]")
            else:
                plt.ylabel("Current [e$^-$/$\mu s$]")
                
            plt.grid(b=True)
            if not do_impulse_response:
                plt.plot(oversampled_sample_times, current_WF,'.-', label='inst, %.1f MHz' % oversampled_freq_MHz)
                #plt.plot(oversampled_sample_times[:-1], current_WF_deriv,'.-')
            plt.plot(oversampled_sample_times, sg_filtered_current_WF,'-', label='SG (fbw=%.3f) %i MHz' % (fbw, oversampled_freq_MHz)) # a test
            plt.plot(oversampled_sample_times, be_filtered_current_WF,'-', label='Bessel (fbw=%.3f) %i MHz' % (fbw, oversampled_freq_MHz)) # a test

            # plot things sampled at baseline sampling freq, ~ 2 MHz
            #plt.plot(baseline_sampling_times, current_WF_sampled,'.-', label='inst, %i MHz' % baseline_sampling_freq_MHz)
            plt.plot(baseline_sampling_times, sg_filtered_current_WF_sampled,'.-', label='SG, %i MHz' % baseline_sampling_freq_MHz)
            #plt.plot(baseline_sampling_times, sg_digitized_wfm,'.-', label='SG, digitization, %i MHz' % baseline_sampling_freq_MHz)

            legend = plt.legend(loc='upper left', ncol=2)
            if i > 0: # log y scale 
                plt.semilogy()
                plt.ylim([0, np.max(current_WF)*100])
            else: # lin y scale, zoom in on x axis
                plt.ylim([-np.max(current_WF)*0.05, np.max(current_WF)*1.3])
                plt.xlim([cathode_arrival_time-3.0, cathode_arrival_time+3.0 ])
                if do_impulse_response:
                    plt.ylim([-np.max(sg_filtered_current_WF)*0.1, np.max(sg_filtered_current_WF)*2])
                    plt.xlim([cathode_arrival_time-1.0, cathode_arrival_time+3.0 ])
            plt.savefig("current_signals_filtered_X16_fbw%.3e_%i.png" % (fbw, i))

    # charge waveform:
    if do_draw_charge:

        # using Ralph's analytical expression
        ralph_WF = digi.RalphWF.make_WF(xpcd=pcdx, ypcd=pcdy, zpcd=pcdz, Epcd=Epcd, chID=chID,
                cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ, wfm_length=wfm_length)
        ralph_WF = np.concatenate([np.zeros(padding_samples), ralph_WF]) # prepend padding zeros

        # integrated current wfm, with some norm factor
        sg_digitized_charge = np.cumsum(sg_digitized_wfm)*1.0/baseline_sampling_freq_MHz*0.43

        # plot charge signal
        plt.figure(1)
        #Collection signal on channel X16
        plt.title("Collection signal X16: charge (%.1f, %.1f, %.1f) mm" % (pcdx, pcdy, distanceFromAnode))
        plt.xlabel("Time  [$\mu s$]")
        if Epcd == 1: # special labels for unit signal 
            plt.ylabel("Q/Qtotal")
        else:
            plt.ylabel("Q [e$^-$s]")
        plt.grid(b=True)
        plt.plot(oversampled_sample_times, ralph_WF, '.-', label='analytical charge %i MHz' % oversampled_freq_MHz)
        plt.plot(baseline_sampling_times, sg_digitized_charge, '.-', label='integrated charge %i MHz (fbw=%.3f)' % (
            baseline_sampling_freq_MHz, fbw))
        legend = plt.legend(loc='upper left',) #ncol=2)
        plt.ylim([-np.max(ralph_WF)*0.1, np.max(ralph_WF)*1.3])
        #plt.ylim([-np.max(ralph_WF)*0.1, np.max(sg_digitized_charge)*1.3])
        plt.savefig("charge_signals_X16_fbw%.3e_%i.png" % (fbw, i))
        #raw_input("press enter to continue ")
    # end do_draw_charge 


    # trapezoidal filtering
    #try:
    if do_trap_filter:
        import ROOT
        print "loading libEXOROOT"
        ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
        from ROOT import EXOTrapezoidalFilter
        from ROOT import EXODoubleWaveform
        from array import array
        canvas = ROOT.TCanvas("canvas","canvas")
        canvas.SetGrid()
        trap_filter = EXOTrapezoidalFilter()
        #trap_filter.SetFlatTime(10e3)
        # per anti-aliasing slides from Veljko, ramp should be 5-20x times the shaping time of the antialiasing filter
        print "default trap filter decay constant:", trap_filter.GetDecayConstant()
        trap_filter.SetRampTime(tau*sampling_period*1*1e3) # ns
        trap_filter.SetFlatTime(10e3)
        trap_filter.SetDecayConstant(trap_filter.GetRampTime())
        #trap_filter.SetDecayConstant(1.0e3)
        #wfm = sg_digitized_wfm
        wfm = sg_filtered_current_WF
        #wfm = current_WF


        exo_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
        trap_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
        #trap_wfm.SetSamplingFreq(baseline_sampling_freq_MHz/1000.0)
        trap_wfm.SetSamplingFreq(baseline_sampling_freq_MHz*oversampling_multiplier/1000.0)
        exo_wfm.SetSamplingFreq(baseline_sampling_freq_MHz*oversampling_multiplier/1000.0)
        trap_filter.Transform(trap_wfm)
        hist = trap_wfm.GimmeHist("trap_hist")
        hist2 = exo_wfm.GimmeHist("exo_hist")
        hist.SetTitle("flat time: %.1f #mus, ramp time: %.1f #mus" % (
            trap_filter.GetFlatTime()/1e3, trap_filter.GetRampTime()/1e3))
        hist.SetLineColor(ROOT.kBlue)
        hist.SetMarkerColor(ROOT.kBlue)
        hist2.SetLineColor(ROOT.kRed)
        hist.SetLineWidth(2)
        hist2.SetLineWidth(2)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.4)
        hist.SetAxisRange(cathode_arrival_time-10.0, cathode_arrival_time+30.0)
        hist.SetMinimum(0)
        hist.Draw("l")
        hist2.Draw("l same")
        canvas.Update()
        canvas.Print("trap_filter.png")

        # impulse wfm, for testing
        impulse_wfm = np.zeros(len(current_WF))
        impulse_wfm[int(cathode_arrival_time/sampling_period)] = 1.0
        impulse_wfm = EXODoubleWaveform(array('d',impulse_wfm), len(impulse_wfm))
        impulse_wfm.SetSamplingFreq(baseline_sampling_freq_MHz*oversampling_multiplier/1000.0)

        canvas2 = ROOT.TCanvas("canvas2","canvas2")
        canvas2.SetGrid()
        canvas2.cd()
        trap_filter.Transform(impulse_wfm)
        hist = impulse_wfm.GimmeHist("impulse_hist")
        hist.SetTitle("flat time: %.1f #mus, ramp time: %.1f #mus" % (
            trap_filter.GetFlatTime()/1e3, trap_filter.GetRampTime()/1e3))
        hist.SetLineColor(ROOT.kBlue)
        hist.SetMarkerColor(ROOT.kBlue)
        hist.SetLineWidth(2)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(0.4)
        hist.SetAxisRange(cathode_arrival_time-5.0, cathode_arrival_time+15.0)
        hist.Draw("ipl")
        canvas2.Update()
        canvas2.Print("trap_filter_impulse.png")

    #except: print "trap fail"


    print "--> calculating wfms at different x,y positions"
    plt.figure(5)
    #Collection signal on channel X16
    plt.xlabel("Time  [$\mu s$]")
    if Epcd == 1: # special labels for unit signal 
        plt.ylabel("I / Q_total  [$\mu s^{-1}$]")
    else:
        plt.ylabel("I [e$^-$s/$\mu s$]")
    plt.grid(b=True)

    pcdz = cathodeToAnodeDistance - distanceFromAnode # mm
    coords_list = []
    #coords_list.append([0, 0, pcdz]) # 25% of full signal
    coords_list.append([1.5, 0, pcdz]) # center of pad
    if True: # different x, y coords
        coords_list.append([0.1, 0, pcdz]) # near outer corner
        coords_list.append([1.5, 1.4, pcdz]) # near indside corner
        coords_list.append([0.8, 0.7, pcdz]) # along edge
        #coords_list.append([2.9, 0, pcdz]) # near outer corner, same as 0.1, 0
        #coords_list.append([4.5, 0, pcdz]) # not on X16

    # different z coords
    coords_list.append([1.5, 0, pcdz+100.0]) # center of pad
    coords_list.append([1.5, 0, pcdz+200.0]) # center of pad
    coords_list.append([1.5, 0, pcdz+300.0]) # center of pad

    #baseline_sampling_times = oversampled_sample_times[1::oversampling_multiplier]

    # print final charge induced on strip, for debugging
    if do_calc_sum_channel:
        print "calculating sum_channel"
        for coords in coords_list:
            print "coords:", coords
            x = coords[0]
            y = coords[1]
            z = coords[2]
            print "\t Q: %.2f" %  digi.RalphWF.sum_channel(x, y, 1e-6, chID) 
    
    current_wfms = []
    max_current = 0
    for coords in coords_list:
        
        print "coords:", coords

        x = coords[0]
        y = coords[1]
        z = coords[2]

        # current wfm, from analytical expression

        #current_wfm = digi.RalphWF.make_current_WF(
        #current_wfm = digi.RalphWF.make_WF(    # really charge, for testing
        current_wfm = digi.RalphWF.make_current_from_derivative(
                xpcd=x, ypcd=y, zpcd=z, Epcd=Epcd, chID=chID,
                cathodeToAnodeDistance=cathodeToAnodeDistance, dZ=dZ,
                wfm_length=wfm_length)

        current_wfm = np.concatenate([np.zeros(padding_samples), current_wfm]) # prepend padding zeros
        print "\t current_wfm max:", np.amax(current_wfm)

        # filter the current wfm
        #current_wfm = transform(current_wfm, simple_gaus, tau)
        print "\t sg_filtered_current_WF:", np.amax(current_wfm)

        # undo oversamping -- go back to usual sampling rate:
        # use numpy array slicing for this:
        #current_wfm = current_wfm[1::oversampling_multiplier]
        print "\t sg_filtered_current_WF_sampled:", np.amax(current_wfm)

        #current_wfm = digitize(current_wfm, max_val=adc_max, bits=adc_bits) # digitize with ADC bits
        print "\t sg_digitized_wfm:", np.amax(current_wfm)

        current_wfms.append(current_wfm) # save for later charge integration

        # choose the correct times for the x axis
        plot_times = oversampled_sample_times
        if len(plot_times) - len(current_wfm) > 1:
            plot_times = baseline_sampling_times
        if len(plot_times) != len(current_wfm):
            plot_times = plot_times[:-1]

        #print "\t current_wfm length:", len(current_wfm)
        #print "\t plot_times length:", len(plot_times)

        if Epcd == 1.0:
            label='(%.1f, %.1f, %i)mm: %.2f' % (x, y, z, np.max(current_wfm))
        else:
            label='(%.1f, %.1f, %i)mm: %.2e' % (x, y, z, np.max(current_wfm))

        plt.plot(plot_times, current_wfm, '.-', label=label)

        if np.max(current_wfm) > max_current: max_current = np.max(current_wfm)

        # end loop over coords_list

    plot_sampling_period = plot_times[1] - plot_times[0]
    plot_sampling_freq = 1.0 / plot_sampling_period

    plt.title("Current signals on X16 (%i MHz, fbw=%.3f, E=%.1f %.1f ADC max, %i bits)" % (
        plot_sampling_freq, fbw, Epcd, adc_max, adc_bits))
    legend = plt.legend(loc='upper left', ncol=2)
    plt.ylim([-max_current*0.1, max_current*1.5])
    #plt.xlim([cathode_arrival_time-1.0, cathode_arrival_time+0.5 ])
    plt.xlim([cathode_arrival_time-3.0, cathode_arrival_time+5.0 ])
    plt.savefig("digitized_current_signals_X16_fbw%.3e.png" % fbw)


    plt.figure(6)
    #Collection signal on channel X16
    plt.title("Integrated charge on X16 (%i MHz, fbw=%.3f, E=%.1f %.1f ADC max, %i bits)" % (
        plot_sampling_freq, fbw, Epcd, adc_max, adc_bits))
    plt.xlabel("Time  [$\mu s$]")
    if Epcd == 1: # special labels for unit signal 
        plt.ylabel("Q/Qtotal")
    else:
        plt.ylabel("Q [e$^-$s]")
    plt.grid(b=True)

    max_charge = 0
    print "--> integrating current wfms at different x,y positions"
    for i, current_wfm  in enumerate(current_wfms):

        coords = coords_list[i]
        x = coords[0]
        y = coords[1]
        z = coords[2]

        # integrate to find the charge
        sg_digitized_charge = np.cumsum(current_wfm)*plot_sampling_freq 
        print "\t sg_digitized_charge:", np.amax(sg_digitized_charge)
        if Epcd == 1.0:
            label='(%.1f, %.1f, %.1f): %.3f' % (x, y, z, np.max(sg_digitized_charge))
        else:
            label='(%.1f, %.1f, %.1f): %.2e' % (x, y, z, np.max(sg_digitized_charge))

        plt.plot(plot_times, sg_digitized_charge, '-', label=label) 

        if np.max(sg_digitized_charge) > max_charge: max_charge = np.max(sg_digitized_charge)

        # end loop over current wfms

    legend = plt.legend(loc='upper left', ncol=2)
    plt.ylim([-max_charge*0.1, max_charge*1.5])
    plt.savefig("integrated_charge_signals_X16_fbw%.3e.png" % fbw)

    #raw_input("press enter to continue ")
    # end of main()


if __name__ == "__main__":
    main()

