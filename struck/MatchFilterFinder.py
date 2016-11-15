import ROOT
import subprocess
root_version = subprocess.check_output(['root-config --version'], shell=True)
print "ROOT Version is", root_version
isROOT6 = False
if '6.1.0' in root_version or '6.04' in root_version:
    print "Found ROOT 6"
    isROOT6 = True

if not isROOT6:
    #sourceroot5 is needed for this to work
    print "loading libEXOUtilities"
    ROOT.gSystem.Load("~/software/offline_root5/build/lib/libEXOUtilities")
# also info in root/build_root6_04_18/include/RVersion.h

from ROOT import EXOBaselineRemover
from ROOT import EXODoubleWaveform
#from ROOT import EXOFastFourierTransformFFTW
from ROOT import EXOMatchedFilter
from array import array
import matplotlib.pyplot as plt
import numpy as np

generator = ROOT.TRandom3(0)
WFlength = 800

def BuildTemplate(isStep=False, temp_t = 0, offset=0):
    #isStep = use a step function instead of actual Template
    #temp_t = time to start the WF

    template_WF = array('d', [0]*WFlength)
        
    if isStep:
        for i in xrange(WFlength):
            if i < temp_t:
                template_WF[i] = 0
            elif i < temp_t+offset and i >=temp_t:
                template_WF[i] = 1
        exoTemplate_WF = EXODoubleWaveform(template_WF, WFlength)
        return exoTemplate_WF
    else:
        tfile = ROOT.TFile("templateWF_MatchedFilter.root")
        exowf = tfile.Get("CollectionTemplate")
        return exowf.Clone()


def BuildSignal(isStep=False, offset=200, t=500):
    #For Testing
    WF = array('d', [0]*WFlength)
    noise = 0.2
    if isStep:
        for i in xrange(WFlength):
            WF[i] = generator.Gaus(0.0, noise)
            if i > t and i < t+offset:
                WF[i] += 1.0

        exoWF = EXODoubleWaveform(WF, WFlength)
        return exoWF
    else:
        tfile = ROOT.TFile("templateWF_MatchedFilter.root")
        exowf = tfile.Get("SampleCollection")
        for i in xrange(WFlength):
            WF[i] = exowf.At(i) + generator.Gaus(0.0, noise)
        exoWF = EXODoubleWaveform(WF, WFlength)
        return exoWF

def BuildDerivTemplate():
    tfile = ROOT.TFile("templateWF_MatchedFilter.root")
    exowf = tfile.Get("DerivTemplate")
    return exowf.Clone()



def SelfTest():

    signal = BuildSignal()
    template = BuildTemplate()
    matched_result = signal.Clone()

    print "attempting EXOMatchedFilter transform..."
    temp_offset = 0
    match_filter = EXOMatchedFilter() 
    match_filter.SetNoisePowerSqrMag()
    match_filter.SetTemplateToMatch(template, WFlength, temp_offset)
    match_filter.Transform(matched_result)
    print "donwe with  EXOMatchedFilter transform"


    templateA = np.zeros(WFlength)
    signalA = np.zeros(WFlength)
    matchedA = np.zeros(WFlength)

    for i in xrange(WFlength):
        templateA[i] = template.At(i)
        signalA[i] = signal.At(i)
        matchedA[i] = matched_result.At(i)

    print "plotting..."
    plt.plot(matchedA/np.max(matchedA), c='r')
    plt.plot(signalA, c='b')
    plt.plot(templateA[::-1] , c='m', linewidth=4.0)

    line = np.arange(-10, 10)

    #plt.plot(np.ones(len(line))*t, line)

    plt.show()

def EXOtoNP(exo_wfm):
    wfm_array = np.zeros(WFlength)
    for i in xrange(WFlength):
        wfm_array[i] = exo_wfm.At(i)
    return wfm_array

def ApplyMatchFilter():
    plt.ion()

    tier1_file = ROOT.TFile("~/testing/test_noiselib/tier1_SIS3316Raw_20160922143510_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root")
    tree = tier1_file.Get("HitTree")
    nevents = tree.GetEntries()
    #template = BuildTemplate()
    template = BuildDerivTemplate()
    match_filter = EXOMatchedFilter()
    #match_filter.SetNoisePowerSqrMag()
    #match_filter.SetTemplateToMatch(template, WFlength, 0)
    
    NoisePSFile = ROOT.TFile("~/testing/test_matchfilter/AvgNoisePS.root")

    max_dist = []
    maxmin_dist = []
    amp = []

    #for i in xrange(nevents):
    for i in xrange(int(nevents*0.2)):
        if i%1000 == 0: print (i*1.0)/nevents
        tree.GetEntry(i)
        channel = tree.HitTree.GetSlot()*16 + tree.HitTree.GetChannel()
        if channel==27 or channel==31 or channel==16: continue
        wfm = tree._waveform
        exo_wfm = EXODoubleWaveform(array('d',wfm), len(wfm))
        match_wfm = exo_wfm.Clone()
        
        avg_noise = NoisePSFile.Get("PSwfm%i" % channel)
        #print channel, avg_noise

        match_filter.SetNoisePowerSqrMag(avg_noise)
        match_filter.SetTemplateToMatch(template, WFlength, 0)
        match_filter.Transform(match_wfm)
        match_wfm_np = EXOtoNP(match_wfm)

        exo_wfm_np = EXOtoNP(exo_wfm)
        exo_wfm_np = exo_wfm_np - np.mean(exo_wfm_np[0:200])
        Energy = np.mean(exo_wfm_np[600:800]) - np.mean(exo_wfm_np[0:200])
        exo_wfm_np = exo_wfm_np/np.max(exo_wfm_np)
        
        scale = 1.0e4
        match_max = np.max(match_wfm_np)/scale
        match_max_min = (np.max(match_wfm_np)/scale) - (np.min(match_wfm_np)/scale)
        #if match_max < 0.15 or channel == 31: continue
     
        if True:
            #if match_max < 0.2 or channel == 31: continue
            #plt.title("Ch = %i and Max = %f and Max-Min = %f and Energy = %f" % (channel, match_max, match_max_min, Energy))
            
            wfmax = np.max(np.abs(match_wfm_np))
            sigma = np.std(match_wfm_np[50:200])
            
            if wfmax/sigma < 5.0 and Energy < 10.0: continue

            plt.title("Ch = %i , S = %f, M= %f, R = %f, E=%f" %(channel, sigma, wfmax, wfmax/sigma, Energy))
            plt.plot(match_wfm_np/np.max(np.abs(match_wfm_np)), c='r')
            plt.plot(exo_wfm_np, c='b')
            #plt.plot(EXOtoNP(template)[::-1] , c='m', linewidth=4.0)
            plt.plot(np.roll(EXOtoNP(template),400), c='m', linewidth=4.0)

            plt.ylim(-1.5, 1.5)
            plt.show()
            raw_input()
            plt.clf()
        
        amp.append(Energy)
        max_dist.append(match_max)
        maxmin_dist.append(match_max_min)
    
    plt.scatter(amp, max_dist)
    plt.xlabel("Energy")
    plt.show()
    raw_input()
    plt.clf()
   
    plt.scatter(amp, maxmin_dist)
    plt.xlabel("Energy")
    plt.show()
    raw_input()

if __name__=="__main__":
    #SelfTest()
    ApplyMatchFilter()



