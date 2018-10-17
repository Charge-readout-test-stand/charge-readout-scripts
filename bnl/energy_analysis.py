import os
from scripts.Energy_Analysis import Energy

import openpyxl as px
from openpyxl import Workbook
import glob
import matplotlib.pyplot as plt

class calibration_analysis:
    def loop(self):
        self.cal_dir_name = (glob.glob(self.cal_path)[0])
            
        print ("\nPath is " + self.cal_dir_name + "\\")

        for self.root, self.dirs, self.files in os.walk(self.cal_dir_name):
            break
        
        self.help_info()
        
        while(1):
            function = raw_input( "Enter 'end, 'help', 'peak', 'area''\n")
            if (function == "end"):
                break
                
            elif (function == "help"):
                self.help_info()
                
            elif (function == "peak"):
                self.Energy_analysis_peak()
                
            elif (function == "area"):
                self.Energy_analysis_area()
                
            else:
                print ("That's not a function")
                
				
    def Energy_analysis_peak(self):
        
        samples = 10000
        Energy_data = self.analysis.Energy(cal_directory = self.cal_path, data_directory = self.data_path, samples = samples, analysis = "peak")
		
        for bins in [100,280,500]:
            fig = plt.figure(figsize=(12,8))
            ax = fig.add_subplot(111)  
            ax.hist(Energy_data,bins=bins)
            ax.set_xlabel("Energy (keV)")
            ax.set_ylabel("Counts")
            ax.set_title("Energy Spectrum")
            fig.savefig ("{}{} bins.jpg".format(self.output_directory, bins))
            fig.clf()
            plt.close()
            
    def Energy_analysis_area(self):
        
        samples = 100000
        Energy_data = self.analysis.Energy(cal_directory = self.cal_path, data_directory = self.data_path, samples = samples, analysis = "area")
		
        for bins in [100,280,500]:
            fig = plt.figure(figsize=(12,8))
            ax = fig.add_subplot(111)  
            ax.hist(Energy_data,bins=bins)
            ax.set_xlabel("Energy (keV)")
            ax.set_ylabel("Counts")
            ax.set_title("Energy Spectrum")
            ax.set_xlim(0, 1400)
#            ax.set_yscale('log', nonposy='mask')
            fig.savefig ("{}{} bins.jpg".format(self.output_directory, bins))
            fig.clf()
            plt.close()
        
    def help_info(self):
        print ("Type 'peak' to analyze the data for the energy spectrum based on pulse peaks")
        print ("Type 'area' to analyze the data for the energy spectrum based on pulse area")
        print ("Type 'end' to exit.")
        
    def __init__(self):
        self.analysis = Energy()
        self.cal_path = "Z:\\nEXO - Charge Readout\\Stanford Setup\\Stanford Trip April 2018\\Calibration_Actual\\"
        self.data_path = "Z:\\nEXO - Charge Readout\\Stanford Setup\\Stanford Trip April 2018\\Test_Data"
        self.output_directory = "Z:\\nEXO - Charge Readout\\Stanford Setup\\Stanford Trip April 2018\\Test_Output\\"
        self.INT_pulse_excel_name = "\\Internal_Pulse_Data.xlsx"
        self.INT_RMS_excel_name = "\\Internal_RMS_Data.xlsx"
            
        
if __name__ == "__main__":
    calibration_analysis().loop()