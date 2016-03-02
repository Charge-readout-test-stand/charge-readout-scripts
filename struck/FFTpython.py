#!/usr/bin/env python

import math
import sys
import ROOT
import numpy as np
from scipy.fftpack import fft
import struck_analysis_parameters
import matplotlib.pyplot as plt
from optparse import OptionParser
from array import array


ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
ROOT.gSystem.Load('/nfs/slac/g/exo/software/hudson/builds-fitting-rhel6-64/build-id/293/lib/libEXOFitting')
ROOT.gSystem.Load("$EXOLIB/lib/libEXOUtilities")
parser = OptionParser()
options,args = parser.parse_args()

tf = ROOT.TFile('/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier2/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root')
tree = tf.Get('tree')

rand = ROOT.TRandom3(0)
ev_n = 0
wfm_samp =800
t_sample =0.048
t = np.linspace(0.0, wfm_samp*t_sample, wfm_samp)
w_t = np.linspace(0.0, 1/(2.0*t_sample), wfm_samp/2.0 )
plt.ion()

while ev_n < tree.GetEntries:
 pywfm = []
 tree.GetEntry(ev_n)
 wfm=tree.wfm0
 pywfm2 = array('d',wfm)
# pywfm = 10*np.sin(32*2*np.pi*t)+0.5*np.sin(5*2*np.pi*t)
 for i in range(len(t)):
  pywfm.append(float(0.7*rand.Gaus(0,struck_analysis_parameters.rms_keV[0]))+4800.0)
 FFT = fft(pywfm)
 FFT2 = fft(pywfm2)
 plt.figure(1)
 plt.plot(t,pywfm2,'r-')
 plt.plot(t,pywfm,'k-')
 plt.xlabel('Time [$\mu$s]')
 plt.figure(2)
 plt.loglog(w_t[2:],np.abs(FFT[2:wfm_samp/2]),'k-',label='rand')
 plt.loglog(w_t[2:],np.abs(FFT2[2:wfm_samp/2]),'r-',label='data')
 plt.xlim([0.03,20])
 plt.xlabel('Frequency [MHz]')
 plt.legend()
 print ev_n
 ev_n+=1
 raw_input()
 plt.clf()
 plt.figure(1)
 plt.clf()
