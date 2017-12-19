import ROOT

#run using test.sh
#by using env -i test.sh
#need this to clear enviorment so that NGg doesn't exis_

ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")

from array import array
import numpy as np
import matplotlib.pyplot as plt

n_bins = 300
e_low  = 500
e_high = 2000

energy_fitter = ROOT.EXOEnergyMCBasedFit1D()
energy_fitter.SetVerboseLevel(1)

data_energy = np.random.normal(1200,20,100000)
mc_energy   = np.random.normal(1000,0.01,1000000)#np.ones(1.e5)*1000.0
mc_weight   = np.ones_like(mc_energy)


#energy_fitter.AddMC('MC',0,0,0,0,0,array('d',mc_energy),array('d',mc_weight),len(array('d',mc_energy)))
#energy_fitter.AddData('data','MC',0,0,0,0,0,0,array('d',data_energy),len(array('d',data_energy)))


energy_fitter.AddMC('MC',0,0,0,0,0, mc_energy, mc_weight, len(mc_energy))
energy_fitter.AddData('data','MC',0,0,0,0,0,0, data_energy, len(data_energy))


calib_func = ROOT.TF1('calib','[0]*x',e_low,e_high)
calib_func.SetParameter(0,1.0)
calib_func.SetParError(0,0.1)
energy_fitter.SetFunction('calib',calib_func)

resol_func = ROOT.TF1('resol','[0]',e_low,e_high)
resol_func.SetParameter(0,20)
resol_func.SetParError(0,0.1)
energy_fitter.SetFunction('resol',resol_func)

dataId = ROOT.std.vector('TString')()
dataId.push_back('data')

energy_fitter.SetDataHisto('all','title', dataId , n_bins, e_low, e_high)
energy_fitter.BinMCEnergy(1)
energy_fitter.ExecuteFit(1,"SIMPLEX",1.)
energy_fitter.ExecuteFit(1,'MIGRAD',1.)

energy_fitter.ApplyFittedParameters()
energy_fitter.SaveHistosIn('mcfit.root','recreate')


hist =  energy_fitter.GetHisto('MC','MC','')
histData = energy_fitter.GetHisto('data','data','data')

print dir(energy_fitter)
print energy_fitter.GetFitter().GetParameter(0)
print energy_fitter.GetFitter().GetParameter(1)/energy_fitter.GetFitter().GetParameter(0)


