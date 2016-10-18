#!/bin/bash 
source ~/setup_NGM.sh
#printenv 

#python rootver.py
time python generateTier3Files.py --Noise /p/lscratchd/alexiss/9thLXe/2016_09_19_overnight/tier1/tier1_SIS3316Raw_20160922095853_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.root

#time python generateTier3Files.py  /p/lscratchd/alexiss/2016_08_15_8th_LXe_overnight/tier1/tier1_SIS3316Raw_20160816020500_8thLXe_126mvDT_cell_full_cath_1700V_100cg_overnight__1-ngm.root 
