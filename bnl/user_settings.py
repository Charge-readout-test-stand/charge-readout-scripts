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
        self.chs_per_chip = 16
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



        #Calibrations from Eric
        self.baseline = [835.7035233,
                         785.4093147,
                         668.0711201,
                         696.3609495,
                         694.146460,
                         768.477665,
                         657.5784539,
                         673.8498967,
                         686.1396048,
                         656.6810507,
                         741.1312354,
                         719.5818142,
                         727.6348561,
                         738.6533884,
                         769.735579,
                         834.0063882,
                         827.7514778, #Chip-1
                         812.12848,
                         737.0389287,
                         763.766811,
                         690.6924757,
                         683.7517013,
                         707.6741157,
                         753.5130846,
                         736.6342144,
                         816.5855655,
                         671.9205128,
                         687.5914252,
                         823.966909,
                         764.2289776,
                         859.4492179,
                         795.2097818,
                         737.8788709, #Chip-2
                         824.4678237,
                         730.8475844,
                         766.4192275,
                         723.2965185,
                         758.0948673,
                         663.1126027,
                         1060.625029,
                         654.7750798,
                         1258.803202,
                         742.594744,
                         682.1034605,
                         1244.165536,
                         1114.865585,
                         757.3189321,#Chip-3
                         820.8566489,
                         757.1188912,
                         696.7344437,
                         793.4456321,
                         699.9039958,
                         707.9059098,
                         684.8048375,
                         629.9206116,
                         635.6101101,
                         676.5024281,
                         648.96331,
                         689.2834636,
                         721.6633448,
                         728.6672158,
                         744.1916212,
                         754.657193,
                         750.4190732
                         ]
        
        self.amp_gain = [ 83.68373149,     
                         82.52148913,
                         83.92299749,
                         84.25208723,
                         84.90022112,
                         83.43910014,
                         86.64043783,    
                         82.48600934,
                         86.16394242,
                         82.20794381,
                         80.96235922,
                         80.57438829,
                         80.31349896,
                         80.14670673,
                         78.83553379,
                         81.06300847,
                         84.5827328, #Chip1
                         82.18392647,
                         83.68846973,
                         83.56881406,
                         82.36139542,
                         82.01388641,
                         81.22469406,
                         83.18294622,
                         80.5185893,
                         80.23603831,
                         81.64239557,
                         79.07498051,
                         79.26591723,
                         79.51317742,
                         78.8738379,
                         77.7560062,
                         35.01626103, #Chip2
                         32.07965536,     
                         -0.921358267,
                         31.29403277,
                         31.82621826,
                         32.31955125,
                         31.55917224,
                         -0.227367342,
                         8.855628932,
                         1.840571068,
                         -2.53057174,
                         -5.035448339,
                         -2.21348193,
                         5.721536618,
                         -5.478483521,
                         11.44485217,
                         87.64519675, #Chip3
                         89.40643639,
                         84.29749508,
                         87.77914136,
                         88.60445904,
                         87.75775832,
                         85.73176289,
                         87.56531294,
                         85.05576325,
                         83.59928164,
                         85.20431619,
                         83.34482503,
                         84.37221004,
                         85.20741385,
                         82.78355067, 
                         84.91050504
                         ]

        self.rms = [    1.761847665,
                        2.856469135,
                        3.376063518,
                        2.67294318,
                        3.121124799,
                        4.180957489,
                        3.121264304,
                        3.129606206,
                        3.235747189,
                        1.887441766,
                        3.223642896,
                        3.38141264,
                        3.394286908,
                        3.198752314,
                        4.223277176,
                        3.475717979,
                        2.312077853, #Chip-1
                        3.285239335,
                        3.566937496,
                        3.113912941,
                        3.246769848,
                        3.182278241,
                        3.013733757,
                        3.209247979,
                        4.681702761,
                        5.178292853,
                        3.200384271,
                        2.727544267,
                        2.911691602,
                        2.82416332,
                        3.048729342,
                        3.008460616,
                        186.3338555, #Chip-2
                        189.7494023,
                        221.6904378,
                        172.6216429,
                        162.8605089,
                        177.8691555,
                        149.3292105,
                        207.5466539,
                        158.0607694,
                        923.8974292,
                        423.5833696,
                        204.4966467,
                        232.5828134,
                        801.0076535,
                        175.0033087,
                        344.9165594,
                        2.519351742, #Chip3     
                        3.03635022,
                        3.305294377,
                        2.287769187,
                        6.469368852,
                        3.259552776,
                        3.114482193,
                        2.252434,
                        3.190767691,
                        3.014598571,
                        3.065199665,
                        2.577759858,
                        3.166340154,
                        3.002152639,
                        3.103444407,
                        3.399036074
                       ]
        
        self.int_gain = [
                        663.5959212,
                        651.2548741,
                        671.642391,
                        657.867585,
                        670.1186632,
                        651.4893674,
                        692.4564624,
                        655.8576425,
                        703.2654866,
                        668.7718953,
                        658.6894281,
                        663.0130378,
                        655.3886559,
                        648.5146525,
                        633.3087674,
                        644.4143697,
                        736.4518708, #Chip1
                        711.1042624,
                        729.0517091,
                        721.3698577,
                        705.0223253,
                        703.008214,
                        696.7800721,
                        707.6712806,
                        681.6891259,
                        675.4800413,
                        708.9737234,
                        682.2495277,
                        685.9353156,
                        674.5843513,
                        671.7093891,
                        673.2905439,
                        0, #Chip2
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        724.1420895,#Chip3
                        734.0578059,
                        692.5934363,
                        719.9346099,
                        741.1488831,
                        736.8479039,
                        733.741575,
                        734.7344866,
                        706.9637808,
                        692.867384,
                        714.2746117,
                        692.2778009,
                        692.4519959,
                        707.9821517,
                        682.0136944,
                        703.2386874
                        ]


