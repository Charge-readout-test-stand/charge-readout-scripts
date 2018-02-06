import ROOT

#run using test.sh
#by using env -i test.sh
#need this to clear enviorment so that NGg doesn't exis_

ROOT.gSystem.Load("$EXOLIB/lib/libEXOROOT")

from array import array
import numpy as np
import matplotlib.pyplot as plt
import os,sys

plt.ion()

def get_cut():
    selection = []
    selection.append("nfound_channels==30") #cut the dead channel events 
    selection.append("SignalEnergy > 200")
    selection.append("nsignals==2")
    selection.append("nXsignals==1")
    selection.append("nYsignals==1")
    selection.append("(rise_time_stop95_sum-trigger_time) > 10")
    selection.append("(rise_time_stop95_sum-trigger_time) < 15")
    selection = " && ".join(selection)
    return selection

def get_cutMC():
    selection = []
    #selection.append("SignalEnergy > 200")
    selection.append("nsignals==2")
    selection.append("nXsignals==1")
    selection.append("nYsignals==1")
    selection.append("(rise_time_stop95_sum-trigger_time) > 6")
    selection.append("(rise_time_stop95_sum-trigger_time) < 8.5")
    selection.append("MCtotalEventLXeEnergy*1.e3 > 1")
    selection = " && ".join(selection)
    return selection


def get_dcmd():
    draw_array = []
    draw_array.append("SignalEnergy")
    #draw_array.append("SignalEnergyLight")
    draw_cmd =  ":".join(draw_array)
    return draw_cmd, len(draw_array)

def GetMC():
    #Just testing a random MC I found
    mcfile = "/home/teststand/mc/jobs_0_to_3399.root"
    tmcfile = ROOT.TFile(mcfile)
    mctree  = tmcfile.Get("tree")
    mctree.SetBranchStatus("*",0)
    mctree.SetBranchStatus("SignalEnergy", 1)
    mctree.SetBranchStatus("MCtotalEventLXeEnergy",1)
    mctree.SetBranchStatus("nsignals",1)
    mctree.SetBranchStatus("nXsignals",1)
    mctree.SetBranchStatus("nYsignals",1)
    mctree.SetBranchStatus("rise_time_stop95_sum",1)
    mctree.SetBranchStatus("trigger_time",1)
    mctree.SetEstimate(mctree.GetEntries())
    select = get_cutMC()
    print "Draw"
    #mctree.Draw("MCtotalEventLXeEnergy*1.e3",select,"goff")
    mctree.Draw("SignalEnergy",select,"goff")
    n = mctree.GetSelectedRows()
    
    mcenergy = np.array([mctree.GetVal(0)[i] for i in xrange(n)])

    return mcenergy

def process_file(filename):
    tfile = ROOT.TFile(filename)
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())

    #Speed things up by setting on and off branches
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("SignalEnergy",1)
    tree.SetBranchStatus("nsignals",1)
    tree.SetBranchStatus("nXsignals",1)
    tree.SetBranchStatus("nYsignals",1)
    tree.SetBranchStatus("channel",1)
    tree.SetBranchStatus("energy",1)
    tree.SetBranchStatus("nfound_channels",1)
    tree.SetBranchStatus("SignalEnergyLight",1)
    tree.SetBranchStatus("lightEnergy",1)
    tree.SetBranchStatus("rise_time_stop95_sum",1)
    tree.SetBranchStatus("trigger_time",1)

    selectcmd = get_cut()
    drawcmd,nvals   = get_dcmd()

    print "Draw CMD",  drawcmd
    print "Select CMD",selectcmd
    tree.Draw(drawcmd,selectcmd,"goff")
    n = tree.GetSelectedRows()

    chargeEnergy  =  np.array([tree.GetVal(0)[i] for i in xrange(n)])
    mc_energy     =  GetMC()
    print "MC Found", len(mc_energy)
    mc_weight     =  np.ones_like(mc_energy)

    n_bins = 100
    e_low  = 200
    e_high = 800
    energy_fitter = ROOT.EXOEnergyMCBasedFit1D()
    energy_fitter.SetVerboseLevel(1)

    energy_fitter.AddMC('MC',0,0,0,0,0, mc_energy, mc_weight, len(mc_energy))
    energy_fitter.AddData('data','MC',0,0,0,0,0,0, chargeEnergy, len(chargeEnergy))
        
    calib_func = ROOT.TF1('calib','[0]*x',e_low,e_high)
    calib_func.SetParameter(0,1.0)
    calib_func.SetParError(0,0.1)
    energy_fitter.SetFunction('calib',calib_func)
    
    resol_func = ROOT.TF1('resol','[0]',e_low,e_high)
    resol_func.SetParameter(0,20)
    resol_func.SetParError(0,1.0)
    #resol_func.FixParameter(0,30)
    energy_fitter.SetFunction('resol',resol_func)

    dataId = ROOT.std.vector('TString')()
    dataId.push_back('data')

    energy_fitter.SetDataHisto('all','title', dataId , n_bins, e_low, e_high)
    energy_fitter.BinMCEnergy(1)
    energy_fitter.ExecuteFit(1,"SIMPLEX",1.)
    energy_fitter.ExecuteFit(1,'MIGRAD' ,1.)

    #print dir(energy_fitter)
    energy_fitter.ApplyFittedParameters()
    energy_fitter.SaveHistosIn('mcfit.root','recreate')


    histMC =  energy_fitter.GetHisto('MC','MC','')
    histData = energy_fitter.GetHisto('data','data','data')
    print histMC.GetEntries()

    print "Chi2", energy_fitter.GetChi2()
    print "Final Fit"
    print energy_fitter.GetFitter().GetParameter(0)
    print energy_fitter.GetFitter().GetParameter(1)


if __name__ == "__main__":

    filename = None
    if len(sys.argv) < 2:
        print "argument: [sis tier 3 root file]"
        #sys.exit(1)
        #filename = "overnight_new_bias_tier3_all_v1_12_3_2017.root"
        #filename = "overnight_new_bias_tier3_all_v2_12_4_2017.root"
        filename  = "~/2017_11_13_SiPM_Run/overnight_new_bias/tier3_added/overnight_new_bias_tier3_all_v3_12_6_2017.root"
    else:
        filename = sys.argv[1]

    print "Using ", filename
    process_file(filename)



