#!/usr/bin/env python
"""
copied from SLAC:
/u/xo/manisha2/nEXO_analysis_charge_digitizer_study/draw_waveform.py

ElecChannel def:
/g/g17/alexiss/software/digitizer_study/nexo-code/nexo-offline/DataModel/ElecEvent/Event/ElecChannel.h 

ElecEvent def:
/g/g17/alexiss/software/digitizer_study/nexo-code/nexo-offline/DataModel/ElecEvent/Event/ElecEvent.h

"""

import os
import sys
import ROOT
#ROOT.gROOT.SetBatch(True)

"""
This script draws waveforms from digi root file."
"""

def main(nEXOAnalysisFilename, nEXOSniperFilename):

  nEXOAnalysisFile = ROOT.TFile(nEXOAnalysisFilename)
  waveformTree = nEXOAnalysisFile.Get("waveformTree")
  evtTree = nEXOAnalysisFile.Get("evtTree")
  print "%i entries in evtTree" % evtTree.GetEntries()
  print "%i entries in waveformTree" % waveformTree.GetEntries()

  status = ROOT.gSystem.Load("$NEXOTOP/nexo-offline/InstallArea/Linux-x86_64/lib/libChargeDigitizer.so")
  nEXOSniperFile = ROOT.TFile(nEXOSniperFilename)
  ElecEvent = nEXOSniperFile.Get("Event/Elec/ElecEvent")
  print "%i entries in ElecEvent tree" % ElecEvent.GetEntries()

  canvas = ROOT.TCanvas("canvas", "")
  canvas.SetGrid()
  waveformTree.SetLineColor(ROOT.kBlue)
  waveformTree.SetMarkerColor(ROOT.kBlue)
  #waveformTree.SetMarkerSize(0.8)
  waveformTree.SetMarkerSize(1.0)
  waveformTree.SetMarkerStyle(8)

  ElecEvent.SetLineColor(ROOT.kRed)
  ElecEvent.SetMarkerColor(ROOT.kRed)
  ElecEvent.SetMarkerSize(0.8)
  ElecEvent.SetMarkerStyle(8)


  i_entry = 0
  waveform_entry = 0

  # nEXO_Analysis has evtTree, with one entry per event, and waveformTree, with
  # one entry per waveform.

  # nEXO sniper has ElecEvent, with one entry per event, and a vector,
  # fElecChannels

  for i_entry in xrange(evtTree.GetEntries()):

      evtTree.GetEntry(i_entry)
      ElecEvent.GetEntry(i_entry)

      #evtTree.Show(i_entry)
      #ElecEvent.Show(i_entry)

      print "===> entry %i | event %i | %i channel(s) hit | GenX:%i | GenY:%i | GenZ:%i" % (
        i_entry, 
        evtTree.EventNumber, evtTree.NumChannels, evtTree.GenX, evtTree.GenY, evtTree.GenZ)
      #print "waveform_entry %i" % (waveform_entry)

      for i_waveform in xrange(evtTree.NumChannels):
          waveformTree.GetEntry(waveform_entry)
          print "--> waveformTree entry %i | Tile: %i | Channel: %i | CC %i | WFA %i" % (
              waveform_entry, 
              waveformTree.WFTileId,
              waveformTree.WFLocalId,
              waveformTree.WFChannelCharge,
              waveformTree.WFAmplitude[waveformTree.WFLen-1]
          )

          if waveformTree.EventNumber != evtTree.EventNumber:
              print "evtTree and waveformTree events don't match"
              sys.exit(1)

          else:
              #selection = "Entry$==%i" % waveform_entry
              #selection = "Entry$==%i && Iteration$>waveformTree.WFLen*0.9" % waveform_entry
              #selection = "Entry$==%i && WFAmplitude>0.01*WFAmplitude[WFLen-1]" % waveform_entry
              selection = "Entry$==%i && Iteration$<WFLen-1 && WFAmplitude>0.1*WFAmplitude[WFLen-1]" % waveform_entry
              selection += " && 1-(Iteration$ % 2)" # downsample 2x

              n_samples = waveformTree.Draw("WFAmplitude/WFAmplitude[WFLen-1]:WFTime", selection, "pl")
              print "%i samples" % n_samples
              #waveformTree.Draw("WFAmplitude:WFTime*1.71/1.8958", selection, "pl")
              
              ElecEvent.GetEntry(i_entry) # this seems to reset vars afer Draw/Scan
              n_wfms = ElecEvent.fElecChannels.size()
              if i_waveform >= n_wfms:
                  print "ElecEvent tree only has %i waveforms!!"
                  waveform_entry += 1
                  continue

              #print "ElecEvent.fElecChannels[i_waveform].WFLen() :", wf_len



              #print "ElecEvent NTE", ElecEvent.ElecEvent.NTE()

              #print ElecEvent.ElecEvent.ElecChannels()
              #print ElecEvent.fElecChannels[i_waveform]

              #print n_wfms
              #print ElecEvent.ElecEvent.ElecChannels().size()

              elec_channel = ElecEvent.fElecChannels[i_waveform]
              #print "ElecEvent local id:", ElecEvent.fElecChannels[i_waveform].WFLocalId()
              #print "ElecEvent local id:", ElecEvent.ElecEvent.ElecChannels()[i_waveform].WFLocalId()
              wf_len = elec_channel.WFLen()
              #print "ElecEvent local id:", elec_channel.WFLocalId()
              #print "ElecEvent wf len:", wf_len
              #print "ChannelNTE:", elec_channel.ChannelNTE()
              #print "WFAmplitude[-1]:", elec_channel.WFAmplitude()[wf_len-1]

              print "--> ElecEvent entry %i | Tile: %i | Channel: %i | CC %i | WFA %i" % (
                  i_entry, 
                  elec_channel.WFTileId(),
                  elec_channel.WFLocalId(),
                  elec_channel.ChannelNTE(),
                  elec_channel.WFAmplitude()[wf_len-1],
              )


              selection = "Entry$==%i && Iteration$<%i" % (i_entry, wf_len)

              # if we want to access any quantities from ElecEvent, I think it
              # has to happen before this draw cmd:
              ElecEvent.Draw(
                  #"fElecChannels[%i].fWFAmplitude:fElecChannels[%i].fWFTime" % (i_waveform, i_waveform),
                  "fElecChannels[%i].fWFAmplitude/fElecChannels[%i].fWFAmplitude[%i]:fElecChannels[%i].fWFTime" % (
                      i_waveform, i_waveform, wf_len-1, i_waveform),
                  selection,
                  "lp same"
              )
              canvas.Update()
              #waveformTree.Show(waveform_entry)

              #ElecEvent.Scan(
              #    #"ElecEvent.fElecChannels.fWFAmplitude:ElecEvent.fElecChannels.fWFTime:fWFLen:fChannelLocalId:@fElecChannels.size()",
              #    #"fWFLen:fChannelLocalId:@fElecChannels.size()",
              #    "fElecChannels[%i].fWFLen:fElecChannels[%i].fChannelLocalId:fElecChannels[%i].fWFAmplitude" % (
              #        i_waveform, i_waveform, i_waveform),
              #    "Entry$==%i" % i_entry
              #)

              val = raw_input("\t press enter (q to quit) ")
              if val == 'q': sys.exit()

              waveform_entry+=1
              # end loop over wfms


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "arguments: nEXOAnalysis file, nEXO-sniper digi file"
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])

