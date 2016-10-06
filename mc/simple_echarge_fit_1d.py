#!/usr/bin/python

"""
This uses EXO tools, so it needs root 5. 

at LLNL: 
source $HOME/setup_nEXO.sh

created from Caio's test_simple_echarge_fit_1d.py
https://confluence.slac.stanford.edu/display/exo/MC-Based+Energy+Fit
"""


import sys
import math
from ROOT import gROOT
gROOT.SetBatch(True)

from ROOT import *
import numpy, sys
import time

import cPickle as pickle

from struck import struck_analysis_parameters


# load libraries
gSystem.Load('$EXOLIB/lib/libEXOUtilities.so')

# pickle usage
#use_pickle_file = True 
use_pickle_file = False


#struck_name = "~/9th_LXe/red_red_overnight_9thLXe_v1.root" # Ubuntu DAQ
#struck_name = "~/9thLXe/red_red_overnight_9thLXe_v1.root" # LLNL
#struck_name = "~/9thLXe/red_overnight_9thLXe_v1.root" # LLNL
#struck_name = "~/9thLXe/overnight_9thLXe_v2.root" # LLNL
#struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_20160919225337_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root" # LLNL
#struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_2016091922*.root" # 4 files, LLNL
#struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_201609192*.root" # 33 files, LLNL
struck_name = "~/scratch/9thLXe/2016_09_19_overnight/tier3/tier3_SIS3316Raw_201609200*.root" # 298 files, LLNL

mc_name = "/p/lscratchd/alexiss/mc_slac/red_jobs_0_to_3399.root" # LLNL, white noise
#mc_name = "/p/lscratchd/alexiss/mc_slac/no_noise_hadd_0_to_3999.root" # LLNL, no added noise


energy_var_name = "SignalEnergy"
rise_time_name = "rise_time_stop95_sum"
sigma_guess_keV = 32.0

trigger_time = 8.0
max_drift_time = 9.0
#max_drift_time = 8.5
max_drift_time = 8.0

min_rise_time = trigger_time + struck_analysis_parameters.drift_time_threshold
max_rise_time = trigger_time + max_drift_time



for channel, val in enumerate(struck_analysis_parameters.charge_channels_to_use):
    if not val: continue
    print channel, struck_analysis_parameters.channel_map[channel]

    selection = []
    selection.append("nsignals==1")
    selection.append("(%s >= %f && %s <= %f)" % (
        rise_time_name,
        min_rise_time,
        rise_time_name,
        max_rise_time,
    ))
    selection = " && ".join(selection)
    print "selection", selection

    prefix = '%i_%i_ch%i' % (
        min_rise_time*1e3,
        max_rise_time*1e3,
        channel,
    )
    print "prefix", prefix
    pickle_file_name = '%s_mc_fits_.p' % prefix

    ch_selection = "signal_map[%i]" % channel
    #mc_ch_selection = "(%s || channel==21)" % ch_selection # X17 & Y17 are symmetric in MC
    #mc_selection = "%s && %s" % (mc_ch_selection, selection)

    data_selection = "%s && %s && !is_bad && !is_pulser" % (ch_selection, selection)
    mc_selection = "%s && %s" % (ch_selection, selection)

    """
    try:
        print 'Loading pickle file...'
        mc_energy,mc_weight,data_energy = pickle.load(open(pickle_file_name,'rb'))
        use_pickle_file = True
    except:
        print "creating new pickle file..."
        use_pickle_file = False
    """

    if not use_pickle_file:
        #gROOT.SetBatch(True)

        # load data
        #data_file = TFile(struck_name)
        #data_tree = data_file.Get('tree')

        data_tree = TChain("tree")
        print "n struck files:", data_tree.Add(struck_name)
        mc_file = TFile(mc_name)

        mc_tree = mc_file.Get('tree')

        print "data_selection", data_selection
        print "mc_selection", mc_selection

        data_tree.SetEstimate(data_tree.GetEntries()+1)
        data_tree.Draw(energy_var_name,data_selection,"para goff")
        
        mc_tree.SetEstimate(mc_tree.GetEntries()+1)
        mc_tree.Draw(energy_var_name,mc_selection,"para goff")
        #mc_tree.Draw("energy_mc:weight",mc_selection,"para goff")

        data_energy = []
        for i in range(data_tree.GetSelectedRows()):
            data_energy.append(data_tree.GetV1()[i])

        mc_energy = []
        mc_weight = []

        for i in range(mc_tree.GetSelectedRows()):
            mc_energy.append(mc_tree.GetV1()[i])
            #mc_weight.append(mc_tree.GetV2()[i])
            mc_weight.append(1.0)

        pickle.dump([mc_energy,mc_weight,data_energy], open(pickle_file_name,'wb'))

        mc_file.Close()
        #data_file.Close()
        print "done pickling..."
        #sys.exit()


    if not use_pickle_file:
        print 'Loading pickle file %s...' % pickle_file_name
        mc_energy,mc_weight,data_energy = pickle.load(open(pickle_file_name,'rb'))

    #for e in data_energy:
    #    print e

    #energy_fitter = EXOEnergyCalibFitMC1D(data_tree.GetV1(),data_tree.GetV1(),data_tree.GetSelectedRows(),data_tree.GetV1(),data_tree.GetSelectedRows())
    #energy_fitter = EXOEnergyCalibFitMC1D(mc_tree.GetV1(),mc_tree.GetV2(),mc_tree.GetSelectedRows(),data_tree.GetV1(),data_tree.GetSelectedRows())
    energy_fitter = EXOEnergyCalibFitMC1D(numpy.array(mc_energy),numpy.array(mc_weight),len(mc_energy),numpy.array(data_energy),len(data_energy))
    energy_fitter.SetVerboseLevel(-1)#3)

    #energy_fitter.SetFunction('calib','[0]+x',pars,error_pars)
    #pars = numpy.array([100.,1.])
    #error_pars = numpy.array([0.2,1.])
    #calib_func = TF1('calib','[0]+[1]*x',0,100000)
    pars = numpy.array([1.0])
    error_pars = numpy.array([0.05])
    calib_func = TF1('calib','[0]*x',0,100000)
    calib_func.SetParameters(pars)
    calib_func.SetParErrors(error_pars)
    energy_fitter.SetFunction('calib',calib_func)

    #energy_fitter.SetFunction('resol','[0]',pars,error_pars)
    #pars = numpy.array([0.015*2615])
    #error_pars = numpy.array([0.002*2615])
    #resol_func  = TF1('resol','[0]',0,100000)
    pars = numpy.array([50,0.5, 0.0])
    error_pars = numpy.array([50,0.5, 10.0])
    resol_func  = TF1('resol','sqrt([0]*[0]+[1]*[1]*x + [2]*[2]*x*x)',0,100000)
    resol_func.SetParameters(pars)
    resol_func.SetParErrors(error_pars)
    energy_fitter.SetFunction('resol',resol_func)

    energy_fitter.SetDataHisto(100,300,1300)
    energy_fitter.BinMCEnergy(1)

    start_time = time.time()
    energy_fitter.ExecuteFit()
    end_time = time.time()
    print end_time - start_time, 'seconds'

    h = TH1D()
    print 'data energy for E_true = 570 keV is', energy_fitter.GetPeakPosition(570), '+-', energy_fitter.GetPeakPositionError(570)#,1000,h)
    print 'resolution for E_true = 570 keV is', energy_fitter.GetPeakWidth(570), '+-', energy_fitter.GetPeakWidthError(570)#,1000,h)
    #print 'data energy for E_true = 1173 keV is', energy_fitter.GetPeakPosition(1173), '+-', energy_fitter.GetPeakPositionError(1173)#,1000,h)
    #print 'resolution for E_true = 1173 keV is', energy_fitter.GetPeakWidth(1173), '+-', energy_fitter.GetPeakWidthError(1173)#,1000,h)
    #print 'data energy for E_true = 1332 keV is', energy_fitter.GetPeakPosition(1332), '+-', energy_fitter.GetPeakPositionError(1332)#,1000,h)
    #print 'resolution for E_true = 1332 keV is', energy_fitter.GetPeakWidth(1332), '+-', energy_fitter.GetPeakWidthError(1332)#,1000,h)
    #h.GetFunction('gaus').Print()

    #h.Draw()
    #raw_input()

    #fit_result = energy_fitter.GetFitter()
    #print fit_result.GetCovarianceMatrixElement(0,0), fit_result.GetCovarianceMatrixElement(0,1) 
    #print fit_result.GetCovarianceMatrixElement(1,0), fit_result.GetCovarianceMatrixElement(1,1) 

    hdata = energy_fitter.GetHisto('data')#.Draw()
    #raw_input('data')
    hmc = energy_fitter.GetHisto('MC')#.Draw()
    #raw_input('MC')
    hscale = energy_fitter.GetHisto('scale')#.Draw()
    #raw_input('scale')

    hmc = hmc.Clone()
    hmc.Multiply(hscale)

    canvas = TCanvas("canvas","")
    canvas.SetGrid()

    legend = TLegend(0.1, 0.91, 0.9, 0.99)
    legend.SetNColumns(2)
    legend.SetFillColor(0)

    hdata.SetXTitle("%s [keV]" % energy_var_name)
    hdata.SetYTitle("Counts / %s [keV]" % hdata.GetBinWidth(1))
    hdata.GetYaxis().SetTitleOffset(1.3)
    hdata.SetMarkerStyle(8)
    hdata.SetMarkerSize(0.8)
    hdata.Draw("pz")
    legend.AddEntry(hdata, "Ch %i %s Data" % (channel, struck_analysis_parameters.channel_map[channel]), "p")

    hmc.SetLineColor(kBlue)
    hmc.SetLineWidth(2)
    hmc.Draw('same')
    legend.AddEntry(hmc, "MC", "l")

    legend.Draw()
    canvas.Update()
    canvas.Print("%s_EXOEnergyCalibFitMC1D.pdf" % prefix)

    print "calibration pars:"
    for i in xrange(calib_func.GetNpar()):
        print "\t %i : %f" % (i, math.fabs(calib_func.GetParameter(i)))
    print "resolution pars:"
    for i in xrange(resol_func.GetNpar()):
        print "\t %i : %f" % (i, math.fabs(resol_func.GetParameter(i)))

    pave_text = TPaveText(0.3, 0.7, 0.99, 0.9, "NDC")
    pave_text.SetFillColor(0)
    pave_text.SetFillStyle(0)
    pave_text.SetBorderSize(0)
    for i in xrange(calib_func.GetNpar()):
        pave_text.AddText("cal %i: %f\n" % (
            i,
            math.fabs(calib_func.GetParameter(i)),
        ))
    for i in xrange(resol_func.GetNpar()):
        pave_text.AddText("res %i: %f\n" % (
            i,
            math.fabs(resol_func.GetParameter(i)),
        ))
    pave_text.AddText(data_selection+"\n")
    pave_text.AddText(mc_selection+"\n")
    pave_text.Draw()

    canvas.Update()
    canvas.Print("%s_EXOEnergyCalibFitMC1D_notes.pdf" % prefix)

    if not gROOT.IsBatch(): raw_input('combine')

    #fit_result.mnprin(5,fit_result.fAmin)

    energy_fitter.SaveHistosIn('ch_%itest_fit_out_echarge_co60.root' % channel,'recreate')
    energy_fitter.IsA().Destructor(energy_fitter)

    # end loop over channels

