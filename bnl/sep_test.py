import os,sys,glob
import numpy as np
import struct
import matplotlib.pyplot as plt
import Data_Chip1

#data_directory = "/p/lscratchd/wu41/teststand_data/14thLXe/2018_04_18/Separated_Packets/"
data_directory =  '/p/lscratchd/jewell6/14thLXe_BNL/set0'

Data_Chip1.Data_Analysis().Seperate_Packets(data_directory,1000,1)

