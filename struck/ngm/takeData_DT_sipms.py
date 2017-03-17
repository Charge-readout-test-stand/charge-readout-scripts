"""

This script is for taking data with the 16-channel desktop unit, with these
firmware versions:

  VME FPGA firmware: 33162008
  ADC FPGA firmware: 02500008

For the 32-channel VME unit, use the script takeData.py. 


To run in a loop, run from the command line like this:

  while true; do time python takeData.py ; done



modified from Jason Newby, email 16 June 2016, subject:SIS3316
"""

import time
import ROOT
ROOT.gROOT.SetBatch(True)


def takeData(doLoop=False, n_hours=10.0):

  # ---------------------------------------------------------------------------
  # options
  # ---------------------------------------------------------------------------

  file_suffix = "_trigger_testing_DT" # this gets appended to the file name

  runDuration = 2*60 # seconds
  #runDuration = 5 # seconds # FIXME!!
  #runDuration = 10 # seconds -- debugging! FIXME
  #A 60s run is 720 MB with 4ms veto

  # settings
  threshold = 10
  gaptime = 30 # delay
  risetime = 4 # peaking time
  firenable = 1
  gain = 0 # default = 1 1 = 2V; 0 = 5V, use 1 for LXe runs, 0 for testing warm
  #termination = 1 # 1 = 50 ohm?
  nimtriginput = 0x10 # Bit0 Enable : Bit1 Invert , we use 0x10 (from struck root gui)
  #nimtrigoutput = 0
  #nimtrigoutput = 0xFF # first 8 channels trigger
  nimtrigoutput = 0xFFFF # any channel triggers
  #nimtriginput = 0
  #trigconf = 0x8 # default = 0x5, we use 0x8 Bit0:Invert, Bit1:InternalBlockSum, Bit2:Internal, Bit3:External                       
  trigconf = 0
  #trigconf += 0x4 # internal
  trigconf += 0x8 # external
  dacoffset = 32768 # default = 32768 
  #dacoffset = 22768 # default = 32768 # FIXME -- for warm cell

  # could have a few other clock freqs if we define them, look to struck root gui for info
  clock_source_choice = 3 # 0: 250MHz, 1: 125MHz, 2=62.5MHz 3: 25 MHz (we use 3) 
  #gate_window_length = 800 #800 (normal)
  gate_window_length = 1050 #800 (normal)
  #pretriggerdelay = 200 
  pretriggerdelay = 275 # 11th LXe
  if clock_source_choice == 0: # preserve length of wfm in microseconds
      gate_window_length*=10
      pretriggerdelay*=10

  # ---------------------------------------------------------------------------

  """ 
  NGM inheritance info (mashed up with file path info!):

  ROOT::TTask
    NGMModuleBase/NGMModule
      NGMModuleBase/NGMSystem
        Systems/SIS3316System/SIS3316SystemMT

  ROOT::TNamed
    NGMData/NGMSystemConfiguration
      NGMData/NGMSystemConfigurationv1
  """

  # ---------------------------------------------------------------------------


  if doLoop:
      print "===> starting %.1f-hour loop of %.1f-second runs.." % (n_hours, runDuration)
  else:
      print "===> starting single %.1f-second run.." % (runDuration)

  n_loops = 0
  n_errors = 0
  start_time = time.time()
  last_time = start_time # last_time is time since start of last loop
  now = start_time
  hours_elapsed = 0.0
  while hours_elapsed < n_hours:
      try:

          sis = ROOT.SIS3316SystemMT()
          sis.setDebug() # NGMModuleBase/NGMModule::setDebug()
          sis.initModules() # NGMModuleBase/NGMModule::initModules()
          sis.SetNumberOfSlots(1) # SIS3316SystemMT::SetNumberOfSlots()
          sis.CreateDefaultConfig("SIS3316") # SIS3316SystemMT _config = new NGMSystemConfigurationv1

          #sis.SetInterfaceType("sis3316_eth")
          sis.SetInterfaceType("sis3316_ethb") # SIS3316SystemMT testing this one since it has VME_FPGA_VERSION_IS_0008_OR_HIGHER

          # NGMSystem::GetConfiguration returns NGMSystemConfiguration, in NGMData/
          # NGMSystemConfiguration::GetSystemParameters() returns
          # NGMConfigurationTable, in NGMData/
          sis.GetConfiguration().GetSystemParameters().SetParameterD("MaxDuration",0,runDuration) #seconds
          sis.GetConfiguration().GetSystemParameters().SetParameterS("OutputFileSuffix",0,file_suffix) 
          sis.GetConfiguration().GetSlotParameters().AddParameterS("IPaddr")
          #sis.GetConfiguration().GetSlotParameters().SetParameterS("IPaddr",0,"192.168.2.101") # eth2
          sis.GetConfiguration().GetSlotParameters().SetParameterS("IPaddr",0,"192.168.1.101") # eth1

          print "\n----> calling InitializeSystem()"
          sis.InitializeSystem() # this also calls ConfigureSystem()
          print "----> done InitializeSystem()\n"

          # Adjust trigger thresholds etc. See sis3316card.{h,cc}
          for icard in xrange(1): # loop over cards:
            sis0 = sis.GetConfiguration().GetSlotParameters().GetParValueO("card",icard)

            sis0.nimtriginput = nimtriginput 
            sis0.nimtrigoutput = nimtrigoutput

            # need to use this method to set clock freq. We don't want to change the
            # master/slave sharingmode:
            sis0.SetClockChoice(clock_source_choice,sis0.sharingmode)

            print "\nSIS", icard, \
              "| nimtriginput:", sis0.nimtriginput, \
              "| clock_source_choice:", sis0.clock_source_choice, \
              "| sharingmode:", sis0.sharingmode, \
              "| nimtrigoutput:", sis0.nimtrigoutput

            for j in xrange(4): # loop over adc groups

                sis0.gate_window_length_block[j] = gate_window_length
                sis0.sample_length_block[j] = gate_window_length # is this right?!
                sis0.pretriggerdelay_block[j] = pretriggerdelay
                sis0.dacoffset[j] = dacoffset

                print "\t ADC group",  j, \
                    "| dacoffset:", sis0.dacoffset[j], \
                    "| gate_window_length:", sis0.gate_window_length_block[j], \
                    "| sample_length:", sis0.sample_length_block[j], \
                    "| pretriggerdelay:", sis0.pretriggerdelay_block[j] 

            # end loop over adc groups

            for i in xrange(16):  # loop over each channel

              sis0.firthresh[i] = threshold # set threshold

              sis0.gain[i] = gain # set gain
              #if icard == 0 and i == 0: 
              #    sis0.gain[i] = 0 # 5V for PMT

              #sis0.termination[i] = termination # set termination
              sis0.trigconf[i] = trigconf # set trigger conf
              sis0.risetime[i] = risetime
              sis0.gaptime[i] = gaptime
              sis0.firenable[i] = firenable

              print "\t SIS", icard, "ch%i" % i, \
                  "| gain:", sis0.gain[i], \
                  "| termination:", sis0.termination[i], \
                  "| firthresh:", sis0.firthresh[i], \
                  "| trigconf:", sis0.trigconf[i]

             # end loop over channels

          # end loop over cards

          print "\n-----> configure system" 
          sis.ConfigureSystem()
          print "\n-----> start acquisition" 

          print "=====> starting run %i | %i errors | %.1f seconds | %.1e seconds total | %.2f hours total \n" % (
              n_loops,
              n_errors,
              now - last_time,
              now - start_time,
              hours_elapsed,
          )
          sis.StartAcquisition() 

          sis.IsA().Destructor(sis) # try to fix memory leak, 24 Jan 2017


      except:
          print "error!"
          n_errors += 1

      n_loops += 1
      now = time.time()
      hours_elapsed = (now - start_time)/60.0/60.0
      print "=====> %i runs | %i errors | %.1f seconds | %.1e seconds total | %.2f hours total \n" % (
          n_loops,
          n_errors,
          now - last_time,
          now - start_time,
          hours_elapsed,
      )
      last_time = now

      if not doLoop:
          print "====> done with single run"
          break


if __name__ == "__main__":
    takeData()
