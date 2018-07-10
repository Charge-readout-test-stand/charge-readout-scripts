from datetime import datetime
class user_editable_settings:
    def __init__(self):
        #TRIGGERED DATA SETTINGS#########################################################################
        #All timings are in 500 ns increments (2 means 1 us, 10 means 5 us, etc...)
        #Delay inherent to the FPGA.  This should be set once.
        self.default_delay = 4;
        #How many samples to send out after the trigger (for each channel).  No higher than 290
        self.post_trigger = 200;
        #No need to change unless there's problems.  Must be bigger than 16
        self.timeout_wait = 100;
        #How many samples to send out before the trigger.
        self.pre_trigger = 20;
        #How much room the C dll accounts for in case packets start coming in faster than they can be written
        self.buffer_size = 50
        #How many packets to combine into one file.  This is to speed up writing to disk, a later function will separate them
        self.packets_per_file = 4
        #The path to the C dll that gets the triggered data
        self.DLL_LOCATION = "C:\\Users\\xenon\\Desktop\\nEXO_BNL_ASIC_Code\\2018_4_15\\read_socket.dll"

        
        #CALIBRATION SETTINGS############################################################################
        #The temp you're saying the run was at.  This affects how the analysis looks at the test pulses
        #Since both DACs give slightly different values at different temperatures
        #Must be "RT" or "LN"
        self.temp       = ("LN")
        #If you're using the long kapton cable, this is necessary, especially in cold
        self.long_cable = False
        #Path everything will be saved at
        self.path = "D:\\nEXO\\" + (datetime.now().strftime('%Y_%m_%d'))  +"\\" 
		#Files to analyze with a quick check:
        self.analysis_files = ["D:\\nEXO\\2018_4_18\\Triggered_data_run\\Seperated\\Chip0Packet12"]
        #Default synchronization settings.  If startup shows that it has to constantly re-synch, change these to what it says

        #COLD
        
#        self.REG_LATCHLOC1_4_data = 0x0B0C0B0B
#        self.REG_CLKPHASE_data = 0x00
#        #Read clock.  A pll_0 of 0x00040003 is a setting of 3 for ASIC 0 and 4 for ASIC 1
#        #Reg 21, 22, 23
#        self.read_asic_1_0 = 0x00020006
#        self.read_asic_3_2 = 0x00020014
#        self.read_asic_neg = 0x80000000
        
        #WARM
        
        self.REG_LATCHLOC1_4_data = 0x14111112
        self.REG_CLKPHASE_data = 0xFF000000
        #Read clock.  A pll_0 of 0x00040003 is a setting of 3 for ASIC 0 and 4 for ASIC 1
        #Reg 21, 22, 23
        self.read_asic_1_0 = 0x0002001C
        self.read_asic_3_2 = 0x0000000A
        self.read_asic_neg = 0x80020000

        #GENERAL SETTINGS###############################################################################
        self.chip_num = 4
        #Which IP addresses you gave those 4 sockets
        self.CHIP_IP = ['192.168.121.83','192.168.121.82','192.168.121.81','192.168.121.80']
        self.FEMB_VER = "nEXO(FE-ASIC with internal DAC)"
        
        #These settings are only necessary if you need to use the long cable
        
#1 is Reg21
        self.cold_min1   = [0x12, 0x7,  0xA,  0x7 ]
        self.cold_max1   = [0x1A, 0xE,  0x12, 0x14]
        self.cold_step1  = [2,    1,    1,    2   ]
        
        self.cold_min2   = [0xA,  0xE,  0xA, 0xC ]
        self.cold_max2   = [0x14, 0x14, 0xB, 0x14]
        self.cold_step2  = [1,    1,    1,   1   ]
        
#Bathtub Parameters

        self.bath_read_min   = [0x11, 0x08, 0x00, 0x00 ]
        self.bath_read_max   = [0x1F, 0x1F, 0x00, 0x11]
        self.bath_read_step  = [2,    2,    4,    4 ]
        
        self.bath_write_min  = [0x05, 0x17, 0x00, 0x00 ]
        self.bath_write_max  = [0x0F, 0x35, 0x1F, 0x1F]
        self.bath_write_step = [2,    2,    4,    4 ]
        
        self.bath_latch_down = [0,  0,  0,  0 ]
        self.bath_latch_up   = [0,  0,  0,  0 ]
        
        self.error_codes = [0x2b7, 0x15b, 0x56e]
