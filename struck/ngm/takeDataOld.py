"""

This script is for taking data with the 32-channel (2 x 16) pizza-box VME
digitizers, with the 2004 version of the firmware. 

For the DT unit with 2008 version of firmware, use the script takeData_16ch_DT.py. 

"""

# modified from Jason Newby, email 16 June 2016, subject:SIS3316


# from test.C
import time
import ROOT
ROOT.gROOT.SetBatch(True)

def takeData(doLoop=False, n_hours=10.0):

  # ---------------------------------------------------------------------------
  # options
  # ---------------------------------------------------------------------------

  #is_warm = False
  is_warm = True # FIXME

  #file_suffix = "_test" # this gets appended to the file name
  #file_suffix = "_digitizer_noise_tests_" # this gets appended to the file name
  #file_suffix = "_8thLXe_126mvDT_cell_full_cath_1700V_100cg_overnight_" # 126-mV discrim threshold, 1700 cathode bias, 100x PMT coarse gain
  #file_suffix = "_9thLXe_126mvDT_cath_1700V_100cg_setup_" # 126-mV discrim threshold, 1700 cathode bias, 100x PMT coarse gain
  #file_suffix = "_9thLXe_126mvDT_cath_1700V_100cg_overnight_" # 126-mV discrim threshold, 1700 cathode bias, 100x PMT coarse gain
  #file_suffix = "_9thLXe_126mvDT_cath_1700V_100cg_warmup_before_recovery_" # 126-mV discrim threshold, 1700 cathode bias, 100x PMT coarse gain
  #file_suffix = "_PMT_Xe_gas_126mvDT__" # 126-mV discrim threshold, 1700 cathode bias, 100x PMT coarse gain
  #file_suffix = "_11thLXe_pulser_off_noise" # 126-mV discrim threshold, 1700 cathode bias, 100x PMT coarse gain
  #file_suffix = "_9thLXe_pulsar_cooldown_notFull_pulsarisX23_24_"
  #file_suffix = "_11thLXe_124mVDT_1250VPMT_recovery_cathode_pulser_higher_inhibit2"
  #file_suffix = "_noise_tests_900torrAr_ShvFt_dewarOpen"
  file_suffix = "_noise_tests_880torrAr0V_ShvFt_dewarOpen_CMoff"
  n_cards = 2

  runDuration = 2*60 # seconds
  #runDuration = 10 # seconds -- debugging! FIXME
  #A 60s run is 720 MB with 4ms veto

  # settings
  threshold = 0
  gain = 1 # default = 1 1 = 2V; 0 = 5V, use 1 for LXe runs, 0 for testing warm
  #termination = 1 # 1 = 50 ohm?
  nimtriginput = 0x10 # Bit0 Enable : Bit1 Invert , we use 0x10 (from struck root gui)
  trigconf = 0x8 # default = 0x5, we use 0x8 Bit0:Invert, Bit1:InternalBlockSum, Bit2:Internal, Bit3:External                       
  dacoffset = 32768 # default = 32768 
  if is_warm:
      print "This is DAQ offset for warm cell!!!"
      dacoffset = 22768 # default = 32768 # FIXME -- for warm cell

  # could have a few other clock freqs if we define them, look to struck root gui for info
  clock_source_choice = 3 # 0: 250MHz, 1: 125MHz, 2=62.5MHz 3: 25 MHz (we use 3) 
  gate_window_length = 1050 #800 (normal)
  pretriggerdelay = 275 
  if clock_source_choice == 0: # preserve length of wfm in microseconds
      gate_window_length = 8000
      pretriggerdelay = 2000

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

  sis = ROOT.SIS3316SystemMT()
  #sis.setDebug() # NGMModuleBase/NGMModule::setDebug()
  sis.initModules() # NGMModuleBase/NGMModule::initModules()
  sis.SetNumberOfSlots(n_cards) # SIS3316SystemMT::SetNumberOfSlots()
  sis.CreateDefaultConfig("SIS3316") # SIS3316SystemMT _config = new NGMSystemConfigurationv1

  sis.SetInterfaceType("sis3316_eth")
  #sis.SetInterfaceType("sis3316_ethb") # SIS3316SystemMT testing this one since it has VME_FPGA_VERSION_IS_0008_OR_HIGHER

  # NGMSystem::GetConfiguration returns NGMSystemConfiguration, in NGMData/
  # NGMSystemConfiguration::GetSystemParameters() returns
  # NGMConfigurationTable, in NGMData/
  sis.GetConfiguration().GetSystemParameters().SetParameterD("MaxDuration",0,runDuration) #seconds
  sis.GetConfiguration().GetSystemParameters().SetParameterS("OutputFileSuffix",0,file_suffix) 
  sis.GetConfiguration().GetSlotParameters().AddParameterS("IPaddr")
  sis.GetConfiguration().GetSlotParameters().SetParameterS("IPaddr",0,"192.168.1.100")
  if n_cards > 1:
    sis.GetConfiguration().GetSlotParameters().SetParameterS("IPaddr",1,"192.168.2.100")

  print "\n----> calling InitializeSystem()"
  sis.InitializeSystem() # this also calls ConfigureSystem()
  print "----> done InitializeSystem()\n"

  # Adjust trigger thresholds etc. See sis3316card.{h,cc}
  for icard in xrange(n_cards): # loop over cards:
    sis0 = sis.GetConfiguration().GetSlotParameters().GetParValueO("card",icard)

    sis0.nimtriginput = nimtriginput 

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

      #sis0.firthresh[i] = threshold # set threshold

      if icard == 1 and i == 15: 
          sis0.gain[i] = 0 # 5V for PMT
      else:
          sis0.gain[i] = gain # set gain

      #sis0.termination[i] = termination # set termination
      sis0.trigconf[i] = trigconf # set trigger conf

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
  if is_warm:
      print "SETTINGS ARE FOR WARM CELL !!!"
  if doLoop:
      print "===> starting %.1f-hour loop of %.1f-second runs.." % (n_hours, runDuration)
      n_loops = 0
      n_errors = 0
      start_time = time.time()
      last_time = start_time # last_time is time since start of last loop
      hours_elapsed = 0.0
      while hours_elapsed < n_hours:
          try:
              sis.StartAcquisition() 
          except:
              print "error!"
              n_errors += 1
          n_loops += 1
          now = time.time()
          hours_elapsed = (now - start_time)/60.0/60.0
          print "=====> %i loops | %i errors | %.1f seconds | %.1e seconds total | %.2f hours total \n" % (
              n_loops,
              n_errors,
              now - last_time,
              now - start_time,
              hours_elapsed,
          )
          last_time = now
  else:
      print "\n===> starting single run, %.1f seconds" % runDuration
      sis.StartAcquisition() 


if __name__ == "__main__":
    takeData()
