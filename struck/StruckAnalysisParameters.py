import pandas as pd
import numpy as np
import math
import csv
#import ROOT


microsecond = 1.e3
second = 1.0e9
DEBUG = True

class StruckAnalysisParameters:
  def __init__( self ):
      self.channel_map = None
      self.calibration_constants = None
      self.run_parameters = None

  def GetChannelMapFromFile( self, input_file ):
      self.channel_map = pd.read_csv( input_file, delimiter=',' )
      
  def GetCalibrationConstantsFromFile( self, input_file ):
      self.calibration_constants = pd.read_csv( input_file, delimiter=',' )

      # Index the calibration constants by the channel name (i.e. 'X1-12')
      self.calibration_contsants = self.calibration_constants.set_index('ChannelName')  


  def GetRunParametersFromFile( self, input_file ):
      # Run parameters:
      #     Drift Length [mm]
      #     Drift Velocity [mm/us]
      #     Max Drift Time [us]
      #     Energy Start Time [us]
      #     Decay Start Time [us]
      #     Decay End Time [us]
      #     Decay Guess [us]
      #     Sampling Rate [MHz]
      #     Sampling Period [ns]
      #     Waveform Length [samples]
      #     Pretrigger Length [samples]
      #     Baseline Length [samples]
      #     Num Struck Boards

      # The input file needs two columns: 'Parameter' and 'Value'
      # We will end up with a dict called run_parameters

      temp_dataframe = pd.read_csv( input_file, delimiter=',' )
      self.run_parameters = dict(zip(temp_dataframe['Parameter'],temp_dataframe['Value']))


      # Here we actually need to calculate some stuff.
      self.run_parameters['Max Drift Time [us]'] = self.run_parameters['Drift Length [mm]'] / \
                                                   self.run_parameters['Drift Velocity [mm/us]']

      self.run_parameters['Sampling Period [ns]'] = 1.e9/(self.run_parameters['Sampling Rate [MHz]']*1.e6)


      self.run_parameters['Baseline Average Time [us]'] = self.run_parameters['Baseline Length [samples]'] * \
                                                          self.run_parameters['Sampling Period [ns]'] / 1.e3

      self.run_parameters['Energy Start Time [us]'] = (self.run_parameters['Waveform Length [samples]'] - \
                                                       self.run_parameters['Baseline Length [samples]'] ) * \
                                                      self.run_parameters['Sampling Period [ns]'] / 1.e3
                                                      # Energy is calculated using the last N samples of the waveform

      self.run_parameters['Decay Start Time [us]'] = self.run_parameters['Energy Start Time [us]']
      self.run_parameters['Decay End Time [us]'] = self.run_parameters['Decay Start Time [us]'] + \
                                                   self.run_parameters['Baseline Length [samples]']

      self.run_parameters['Decay Guess [us]'] = 200.

      # Finally, set the inversion flag
      if self.run_parameters['Sampling Rate [MHz]'] == 125:
         self.run_parameters['DoInvert'] = True
      elif self.run_parameters['Sampling Rate [MHz]'] == 62.5:
         self.run_parameters['DoInvert'] = False
      else:
         self.run_parameters['DoInvert'] = False
    
      if DEBUG:
         print('\nrun_parameters:')
         print(self.run_parameters)      


 
