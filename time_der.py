#!/usr/bin/env python

import sys
import ROOT
import numpy as np
import struck_analysis_parameters
from ROOT import EXODoubleWaveform
from ROOT import EXOSmoother
from ROOT import EXOWaveformRegion
from array import array
from ROOT import CLHEP
from collections import defaultdict

ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPalette(1)
ROOT.gStyle.SetTitleStyle(0)
ROOT.gStyle.SetTitleBorderSize(0)

ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")
ROOT.gSystem.Load('/nfs/slac/g/exo/software/hudson/builds-fitting-rhel6-64/build-id/293/lib/libEXOFitting')
ROOT.gSystem.Load("$EXOLIB/lib/libEXOUtilities")

tf = ROOT.TFile('/nfs/slac/g/exo_data4/users/alexis4/test-stand/2015_12_07_6thLXe/tier2/tier2_xenon8300g_1300VPMT_1700Vcathode_amplified_shaped_2015-12-07_21-28-20.root')



c1 = ROOT.TCanvas('c1','' )
c1.SetGrid(1,1)
legend = ROOT.TLegend(0.2, 0.91, 0.9, 1)
legend.SetNColumns(3)
ev_count=0
diff_hist={}
hist_or={}
sm_factor=10
der_sampling=5
tree = tf.Get('tree')
n_entries = tree.GetEntries()
print "%i entries" % n_entries
channel_map = struck_analysis_parameters.channel_map
calibration_values = struck_analysis_parameters.calibration_values
sampling_freq_Hz = struck_analysis_parameters.sampling_freq_Hz
pave_text2 = ROOT.TPaveText(0.11, 0.5, 0.3, 0.59, "NDC")
pave_text2.SetTextAlign(11)
pave_text2.GetTextFont()
pave_text2.SetTextFont(42)
pave_text2.SetFillColor(0)
pave_text2.SetFillStyle(0)
pave_text2.SetBorderSize(0)

while ev_count<n_entries:
 tree.GetEntry(ev_count)
 wfm0_e = []
 wfm1_e = []
 wfm2_e = []
 wfm3_e = []
 wfm4_e = []
 maxval = []
 minval = []
 energy_cl = []
 energy = defaultdict(list)
 ev_tr='ev%i'%ev_count
 legend.Clear()
 pave_text2.Clear()
 for i in range(0,5):
  if i == 0: 
   wfm = tree.wfm0
  elif i == 1: 
   wfm = tree.wfm1
  elif i == 2: 
   wfm = tree.wfm2
  elif i == 3: 
   wfm = tree.wfm3
  elif i == 4: 
   wfm = tree.wfm4
  elif i == 5: 
   wfm = tree.wfm5
  wfm_length = len(wfm)
  wfm_name='wfm_%i' %i
#  zer = ROOT.TF1('zero','0',0,wfm_length/sampling_freq_Hz*CLHEP.millisecond)
  energy_wfm = EXODoubleWaveform(array('d',wfm), wfm_length)
  energy_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
  sm_energy_wfm = EXODoubleWaveform(array('d',wfm), wfm_length)
  smoother = EXOSmoother()
  smoother.SetSmoothSize(sm_factor)
#region = EXOWaveformRegion(15,750)    # not fundamental
#smoother.SetSmoothRegion(region)      # not fundamental
  smoother.Transform(energy_wfm,sm_energy_wfm)
  hist = sm_energy_wfm.GimmeHist('hist_sm'+wfm_name)
  hist_or = energy_wfm.GimmeHist('hist_or'+wfm_name)
  a=hist_or.GetMaximum()
  b=hist_or.GetMinimum()
  diff_hist[i] = ROOT.TH1D(ev_tr+wfm_name,ev_tr+wfm_name,wfm_length,0.04,wfm_length/sampling_freq_Hz*CLHEP.millisecond) #CLHEP starts defines 1 as 1ns
  for j in range(0,wfm_length):
   if j<der_sampling or j>(wfm_length-der_sampling):
    diff_hist[i].Fill(j/sampling_freq_Hz*CLHEP.millisecond,b)
   else:
    diff_hist[i].Fill(j/sampling_freq_Hz*CLHEP.millisecond,(hist.GetBinContent(j+der_sampling)-hist.GetBinContent(j))/10*(a-b)+b)
  diff_hist[i].Smooth()
  diff_hist[i].GetXaxis().SetRange(10,790)
  maxval.append(diff_hist[i].GetMaximum())
  minval.append(diff_hist[i].GetMinimum(20))
  maxval.append(hist_or.GetMaximum())
  minval.append(hist_or.GetMaximum())


 for k in range(0,5):
  if k == 0:
   wfm = tree.wfm0
  elif k == 1:
   wfm = tree.wfm1
  elif k == 2:
   wfm = tree.wfm2
  elif k == 3:
   wfm = tree.wfm3
  elif k == 4:
   wfm = tree.wfm4
  elif k == 5:
   wfm = tree.wfm5
  wfm_length = len(wfm)
  wfm_name='wfm_%i' %k
  for i_sample in range(0,100):
   energy[k].append(wfm[wfm_length - i_sample - 1]- wfm[i_sample])
  energy_wfm = EXODoubleWaveform(array('d',wfm), wfm_length)
  energy_wfm.SetSamplingFreq(sampling_freq_Hz/CLHEP.second)
  sm_energy_wfm = EXODoubleWaveform(array('d',wfm), wfm_length)
  smoother = EXOSmoother()
  smoother.SetSmoothSize(sm_factor)
  smoother.Transform(energy_wfm,sm_energy_wfm)
  hist = sm_energy_wfm.GimmeHist('hist_sm'+wfm_name)
  hist_or = energy_wfm.GimmeHist('hist_or'+wfm_name)  
  hist_or.SetLineColor(struck_analysis_parameters.get_colors()[k])
  diff_hist[k].SetLineColor(struck_analysis_parameters.get_colors()[k])
  diff_hist[k].SetLineStyle(7)
  hist.SetLineWidth(2)
  energy_cl.append(float(np.mean(energy[k]))*calibration_values[k])
  hist_or.SetTitle('event %i'%ev_count)
  hist_or.SetMaximum(max(maxval)+10)
  hist_or.SetMinimum(min(minval)-10)
  legend.AddEntry(hist_or,'%s E=%.2f keV'%(channel_map[k],energy_cl[k]),'l')
  hist_or.Draw('same')
  diff_hist[k].Draw('same')
  hist.Draw('same')
 pave_text2.AddText("#SigmaE_{C} = %.2f keV" %sum(energy_cl))
 pave_text2.Draw()
 legend.Draw()
 c1.Modified()
 c1.Update()
 ROOT.gSystem.ProcessEvents()
 print 'ev num. %i'%ev_count
 ev_count+=1

 val = raw_input('enter to continue (q=quit, b=batch, p=print, n=enter event number) ')
 print val
 if (val == 'q' or val == 'Q'): sys.exit(1) 
 if val == 'b': continue
 if val == 'n':
  num_val = raw_input('number event: ')
  print num_val
  tree.GetEntry(int(num_val))
  ev_count = int(num_val)
 if val == 'p': c1.Print('waveform_entry_%i.png' % (ev_count))
# c1.Clear()
