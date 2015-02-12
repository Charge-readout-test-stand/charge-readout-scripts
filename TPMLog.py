"""
This script plots temperature, recent temperature, mass flow, pressure, and
valve status

The main function returns a string that can be used with glob to select all
plots that are produced.

Plot names = DataType_Date_Index*.jpeg

*.dat file columns:
0: time [seconds]
1: TC0 [K]
2: TC1
3: TC2 
4: TC3 
5: TC4
6: T_ambient
7: LN F/T inlet TC [K]
8: LN F/T outlet TC [K]
9: Xe recovery bottle [K]
10: T_min set point
11: T_max set point
12: TC15 on valve XV5 [K] (for t > 3500502750)
13: TC10, regulator temperature [K] (for t > 3500502750)
14: Primary LN valve status
15: Secondar LN valve status
16: Heater 
17: Mass flow rate (uncorrected)
18: Mass flow rate [grams per minute Xe gas]
19: Pressure from 10k Torr baratron [Torr]
20: Pressure from 1k Torr baratron [Torr]
21: Cold cathode gauge [micro Torr]
22: LN mass (minus hooks and dewar tare weight) [lbs]
23: Xenon Bottle mass [kg]
24: Capacitance [pF]
25: T_max set point offset [K]
26: T_min set point offset [K]
27: LN tare mass [lbs]
*** there is another value in the files after LN mass -- what is it?! -- Alexis 06 Feb 2015
"""


import os
import sys
import datetime
import matplotlib.pyplot as plt
import numpy as np
from optparse import OptionParser

def compare_isochoric(data_path, plot_dir, temp_obs, press_obs, time_hours):
    linewidth = 2
    temp, press = np.loadtxt(str(data_path)+"/vapor_pressure_data.txt",unpack=True, usecols = (0,1))
    plt.figure(1)
    plt.title("Isochoric Data NIST")
    plt.xlabel("Temp [K]")
    plt.ylabel("Pressure [torr]")
    plt.grid(b=True)
    iso_data = plt.plot(temp, press)
    plt.setp(iso_data, color = 'c', linewidth = linewidth, label = 'Data')
    legend = plt.legend(loc='best', shadow = False, fontsize='medium', ncol=2)
    plt.savefig(plot_dir+"Comp_Isochoric.jpeg")
    print "printed", plot_dir+"Comp_Isochoric.jpeg"
    plt.clf()
    
    calc_press = []
    for t,p in zip(temp_obs, press_obs):
        if np.min(temp) < t < np.max(temp) and np.min(press) < p < np.max(press): 
            index = (np.abs(temp-t)).argmin()
            calc_press.append(press[index])
        else:
            calc_press.append(0.0)
            
    plt.figure(2)
    plt.title("Isochoric Batron vs Temp")
    plt.xlabel("Time [hours]")
    plt.ylabel("Pressure [torr]")
    plt.grid(b=True)
    iso_calc = plt.plot(time_hours, calc_press)
    iso_real = plt.plot(time_hours, press_obs)
    plt.setp(iso_calc, color = 'c', linewidth = linewidth, label = 'Temp Calc')
    plt.setp(iso_real, color = 'r', linewidth = linewidth, label = 'Baratron')
    legend = plt.legend(loc='best', shadow = False, fontsize='medium', ncol=2)
    plt.savefig(plot_dir+"Comp_Isochoric2.jpeg")
    print "printed", plot_dir+"Comp_Isochoric2.jpeg"
    plt.clf()
        
     

def plot_temp_vs_lmass(filename, title, time_hours, time_stamps, T_ambient, mass):
    linewidth=1
    start_time_hold = datetime.datetime.fromtimestamp(time_stamps[0]- 2082844800)
    end_time_hold = datetime.datetime.fromtimestamp(time_stamps[len(time_stamps)-1]- 2082844800)
    
    start_time = start_time_hold.strftime("%m-%d-%y %I:%M:%p")
    end_time = end_time_hold.strftime("%m-%d-%y %I:%M:%p")
    
    plt.figure(1)
    plt.title(title +"  "+ str(start_time))
    plt.grid(b=True)
    
    #Ambient Temp
    ambient_line = plt.plot(time_hours, T_ambient)
    plt.setp(ambient_line, color = 'c', linewidth = linewidth, label = 'Ambient')
    
    offset = np.mean(T_ambient) - np.mean(mass)
    
    #Load Mass
    mass_line = plt.plot(time_hours, np.array(mass) + offset)
    plt.setp(mass_line, color = 'r', linewidth = linewidth, label = 'Load Mass')
    
    plt.xlabel('Time [hours]  ' + str(start_time) + "  -  " + str(end_time))
    plt.ylabel('Temperature [K]')
    legend = plt.legend(loc='best', shadow = False, fontsize='medium', ncol=2)
    plt.savefig(filename)
    print "printed %s" % filename
    plt.clf()
    
    
        
   
def plot_temperatures(filename, title, time_hours, time_stamps, TC0=None, TC1=None, TC2=None,
    TC3=None, TC4=None, TC15=None, TC10=None, T_ambient=None, T_LN_in=None, T_LN_out=None,
    T_Xe_bottle=None, T_max_set=None,
    T_min_set=None, first_index=0, last_index=-1):

    """
    This function makes a temperature plot
    """

    linewidth=1
    start_time_hold = datetime.datetime.fromtimestamp(time_stamps[first_index]- 2082844800)
    end_time_hold = datetime.datetime.fromtimestamp(time_stamps[last_index]- 2082844800)
    
    start_time = start_time_hold.strftime("%m-%d-%y %I:%M:%p")
    end_time = end_time_hold.strftime("%m-%d-%y %I:%M:%p")

    plt.figure(1)
    plt.title(title +"  "+ str(start_time))
    plt.grid(b=True)

    

    # plot the lines
    # html color names can be used, as defined here:
    # http://www.w3schools.com/tags/ref_colornames.asp


    if TC0 and len(TC0) > 0:
        line1 = plt.plot(time_hours[first_index:last_index], TC0[first_index:last_index])
        plt.setp(line1, color = 'r', linewidth = linewidth, label = 'Cu Bot')

    if TC1 and len(TC1) > 0:
        line2 = plt.plot(time_hours[first_index:last_index], TC1[first_index:last_index])
        plt.setp(line2, color = 'b', linewidth = linewidth, label = 'CellTop')

    if TC2 and len(TC2) > 0:
        line3 = plt.plot(time_hours[first_index:last_index],
        TC2[first_index:last_index])
        plt.setp(line3, color = 'g', linewidth = linewidth, label = 'CellMid')

    if TC3 and len(TC3) > 0:
        line4 = plt.plot(time_hours[first_index:last_index],
        TC3[first_index:last_index])
        plt.setp(line4, color = 'm', linewidth = linewidth, label = 'CellBot')

    if TC4 and len(TC4) > 0:
        line5 = plt.plot(time_hours[first_index:last_index],
        TC4[first_index:last_index])
        plt.setp(line5, color = 'k', linewidth = linewidth, label = 'Cu Top')

    if T_ambient and len(T_ambient) > 0:
        line6 = plt.plot(time_hours[first_index:last_index],
        T_ambient[first_index:last_index])
        plt.setp(line6, color = 'c', linewidth = linewidth, label = 'Ambient')

    if T_LN_in and len(T_LN_in) > 0 and len(T_LN_in) == len(T_ambient):
        line7 = plt.plot(time_hours[first_index:last_index],
        T_LN_in[first_index:last_index])
        plt.setp(line7, color = 'purple', linewidth = linewidth, label = 'LN in')

    if T_LN_out and len(T_LN_out) > 0 and len(T_LN_out) == len(T_ambient):
        line8 = plt.plot(time_hours[first_index:last_index],
        T_LN_out[first_index:last_index])
        plt.setp(line8, color = 'royalblue', linewidth = linewidth, label = 'LN out')

    if T_Xe_bottle and len(T_Xe_bottle) > 0 and len(T_Xe_bottle) == len(T_ambient):
        line8 = plt.plot(time_hours[first_index:last_index],
        T_Xe_bottle[first_index:last_index])
        plt.setp(line8, color = 'magenta', linewidth = linewidth, label = 'Xe bottle')

    if T_max_set and len(T_max_set) > 0 and len(T_max_set) == len(T_ambient):
        line9 = plt.plot(time_hours[first_index:last_index],
        T_max_set[first_index:last_index])
        plt.setp(line9, color = 'r', linewidth = linewidth, label = 'T_max', ls = '--')

    if T_min_set and len(T_min_set) > 0 and len(T_min_set) == len(T_ambient):
        line10 = plt.plot(time_hours[first_index:last_index],
        T_min_set[first_index:last_index])
        plt.setp(line10, color = 'b', linewidth = linewidth, label = 'T_min', ls = '--')
        
    if TC15 and len(TC15) > 0:
        line11 = plt.plot(time_hours[first_index:last_index],
        TC15[first_index:last_index])
        plt.setp(line11, color = 'k', linewidth = linewidth, label = 'XV5')
    
    if TC10 and len(TC10) > 0:
        line12 = plt.plot(time_hours[first_index:last_index],
        TC10[first_index:last_index])
        plt.setp(line12, color = 'g', linewidth = linewidth, label = 'Reg')

    plt.xlabel('Time [hours] : '  + str(start_time) + "  -  " + str(end_time))
    plt.ylabel('Temperature [K]')
    legend = plt.legend(loc='best', shadow = False, fontsize='medium', ncol=2)
    plt.savefig(filename)
    print "printed %s" % filename
    plt.clf()
 

def main(
    filename,   # *.dat file to process
    start_time=None, # start time, in hours, other than first time in file
    stop_time=None,   # stop time, in hours, other than last time in file
):
    
    # options
    recent_time_span = 3600.0 # seconds to use for "recent" plots

    # print some status info 
    print "--> processing", filename
    if start_time != None:
        print "\t using start time of %.2f hours" % start_time
    if stop_time != None:
        print "\t using stop time of %.2f hours" % stop_time

    # choose an output directory for these files

    # on the windows DAQ machine:
    directory = 'C://Users//xenon//Dropbox//labViewPlots/'
    if not os.path.isdir(directory):
        print "trying alexis' path..."
        #directory = '/Users/alexis/stanford-Dropbox/Dropbox/labViewPlots/'
        directory = '/Users/alexis/Downloads/'
        if not os.path.isdir(directory):
            print "trying mikes path.."
            directory = "C://Users//Michael//Documents//EXO//plots//"
            if not os.path.isdir(directory):
                directory = "."

    # construct a base name for plots, based on the input file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    basename = basename.split("test_")[-1]

    
    # construct file names of plots
    filetype = 'jpeg'    
    mfpath = os.path.join(directory, "MassFlow_%s.%s" % (basename, filetype))
    vpath = os.path.join(directory, "ValveStates_%s.%s" % (basename, filetype))
    ppath = os.path.join(directory, "Pressure-10kTorr_%s.%s" % (basename, filetype))
    ppath2 = os.path.join(directory, "Pressure-1kTorr_%s.%s" % (basename, filetype))
    mfrpath = os.path.join(directory, "MassFlowRate_%s.%s" % (basename, filetype))
    ccgpath = os.path.join(directory, "CCGauge_%s.%s" % (basename, filetype))
    rccgpath = os.path.join(directory, "CCGauge-recent_%s.%s" % (basename, filetype))
    ccgpath_log = os.path.join(directory, "CCGauge-log_%s.%s" % (basename, filetype))
    rccgpath_log = os.path.join(directory, "CCGauge-log-recent_%s.%s" % (basename, filetype))
    lnpath = os.path.join(directory, "LN-Mass_%s.%s" % (basename, filetype))
    bottle_mass_path = os.path.join(directory, "BottleMass_%s.%s" % (basename, filetype))
    capacitance_path = os.path.join(directory, "Capacitance_%s.%s" % (basename, filetype))
    hfep_path = os.path.join(directory, "HFE_Pressure_%s.%s" % (basename, filetype))
    dp_path = os.path.join(directory, "dP_Pressure_%s.%s" % (basename, filetype))

    # create some lists to hold values from files
    time_stamps = [] # labview timestamp, in seconds
    time_hours = [] # elapsed time in hours
    time_minutes = [] # elapsed time in minutes
    recent_time = []
    TC0 = []
    TC1 = []
    TC2 = []
    TC3 = []
    TC4 = []
    TC10 = []
    TC15 = []
    T_ambient = []
    T_LN_in = []
    T_LN_out = []
    T_Xe_bottle = []
    T_max_set = []
    T_max_set_offset = []
    T_min_set = []
    T_min_set_offset = []
    mass_flow_rate = []
    PLN = []
    SLN = []
    Heat = []
    Pressure = []
    Pressure2 = []
    ccg_Pressure = []
    ln_mass = []
    ln_tare_mass = []
    bottle_mass = []
    capacitance = []
    hfe_pressure = []

    # open the input file
    testfile = file(filename)

    # a column_offset to handle changes to LabView project
    column_offset = 0
    do_warning = True

    # The mass_flow_rate value saved by LabView is the uncorrected (not scaled
    # by the dial) output of the mass flow meter, multiplied by 5.28. 
    # xenon correction factor: 1.32 [MKS 1479 manual page 50]
    # xenon gas density at 0 C: 5.894 g/L [MKS 1479 manual page 50]

    xenon_density = 5.89 # density of Xe gas [g/L at 0C]
    # xenon density at 300K: 5.3612 g / mL
    # correction for what alexis put in labview:
    xenon_density_ratio = xenon_density / 5.3612 # xenon density correction
    print "xenon_density_ratio: ", xenon_density_ratio

    xenon_gas_correction_factor = 1.32
    #nitrogen_density = 1.25

    # read values from input file:
    for (i_line, line) in enumerate(testfile):
        split_line = line.split()
        data = []
        time_stamp = float(split_line[0])
        time_stamps.append(time_stamp)

        # handling for changes to LabView...

        # 10 Nov 2014  -- LN F/T and xenon bottle TCs were added to LabView
        # plot
        if time_stamp > 3498505091: 
            column_offset = 3 

        # 11 Nov 2014 -- temperature set points were added to LabView plot
        if time_stamp > 3498586822: 
            column_offset = 5 

        #3 Dec 2014 -- thermo couple at XV5 added
        if time_stamp > 3500482580:
            column_offset = 6
        
        #3 Dec 2014 -- thermo couple at regulator
        if time_stamp > 3500502750:
            column_offset = 7

       
        if do_warning:
            print "--> setting column_offset to %i !!" % column_offset
            print "tstamp:  ", time_stamp
            do_warning = False     


        TC0.append(float(split_line[1]))
        TC1.append(float(split_line[2]))
        TC2.append(float(split_line[3]))
        TC3.append(float(split_line[4]))
        TC4.append(float(split_line[5]))
        T_ambient.append(float(split_line[6]))

        # LN TCs added to LabView output 06 Nov 2014
        # LabView modified again 11 Nov 2014
        T_LN_in.append(float(split_line[7]))
        T_LN_out.append(float(split_line[8]))

        # T_Xe_bottle, changed 11 Nov 2014?
        T_Xe_bottle.append(float(split_line[9]))

        # T_max and min changed 11 Nov 2014
        T_min_set.append(float(split_line[10]))
        T_max_set.append(float(split_line[11]))
        
        #TC15 at XV5 and TC10 at REG
        TC15.append(float(split_line[12]))
        TC10.append(float(split_line[13]))
        

        PLN.append(float(split_line[7+column_offset]))
        SLN.append(float(split_line[8+column_offset]))
        Heat.append(float(split_line[9+column_offset]))

        xenon_mass_flow = float(split_line[10+column_offset])*xenon_density_ratio
        mass_flow_rate.append(xenon_mass_flow)

        # for use while testing the system with N2
        #nitrogen_mass_flow = xenon_mass_flow / xenon_gas_correction_factor / xenon_density * nitrogen_density
        #mass_flow_rate.append(nitrogen_mass_flow)

        # mass_flow_rate from LabView is in grams / minute 

        Pressure.append(float(split_line[12+column_offset]))
        Pressure2.append(float(split_line[13+column_offset]))

        ccg_Pressure.append(float(split_line[14+column_offset])/1e6)
        bottle_mass.append(float(split_line[16+column_offset])) 
        try:   
            capacitance.append(float(split_line[17+column_offset]))
        except IndexError:
            pass

        # Temperature set points added to LabView output 06 Nov 2014
        # changed 11 Nov 2014
        try:
            T_max_set_offset.append(float(split_line[18+column_offset]))
            T_min_set_offset.append(float(split_line[19+column_offset]))
        except IndexError:
            pass
        #if i_line % 1000 == 0:
        #  print "line %i" % i_line
        
        #HFE pressure gauge added 12 Dec 2014
        try:
            hfe_pressure.append(float(split_line[20+column_offset]))
        except IndexError:
            pass

        # the tare-subtracted mass is recorded by labview, but we want to plot the
        # tare-included mass, if it is available
        tare_mass = 0.0
        # LN tare mass added around 05 Feb 2015
        try:
            tare_mass = float(split_line[21+column_offset])
            ln_tare_mass.append(tare_mass)
        except IndexError:
            pass
        ln_mass.append(float(split_line[15+column_offset]) + tare_mass)    

    # indices to use if start_time or stop_time are not specified
    first_index = 0
    last_index = len(time_stamps)-1

    start_index_of_last_hour = None
    start_time_stamp_of_last_hour = None
    last_time_stamp = time_stamps[-1]

    # loop over time stamps, converting some units and searching for some
    # special indices
    print "looping over time stamps..."
    for (i, time_stamp) in enumerate(time_stamps):
        seconds_elapsed = time_stamp - time_stamps[0]
        time_hours.append(seconds_elapsed/3600.0) # time in hours
        time_minutes.append(seconds_elapsed/60.0) # time in minutes

        # find time stamp recent_time_span from last_index:
        if start_index_of_last_hour == None:
            #if last_time_stamp - time_stamp <= recent_time_span:
            last_hour_to_consider = (last_time_stamp - time_stamps[0])/3600.0
            if stop_time != None:
                last_hour_to_consider = stop_time
            if last_hour_to_consider*3600 - seconds_elapsed <= recent_time_span:
                start_index_of_last_hour = i
                start_time_stamp_of_last_hour = time_stamp
                print "last_hour_to_consider", last_hour_to_consider
                print "\t found last hour time stamp  at i = %i of %i, t= %.2f hours" % (i, len(time_stamps),  seconds_elapsed/3600.0)
                print "\t last timestamp = %.2f, diff = %.2f" % (last_time_stamp, last_time_stamp - start_time_stamp_of_last_hour )
                print "\t %i recent time stamps" % (len(time_stamps) - start_index_of_last_hour - 1)

        # find first_index, if start_time is specified
        if start_time != None and first_index == 0:
            if time_hours[-1] >= start_time: 
                first_index = i
                print "\t found first index: %i at time %.2f hours" % (i, time_hours[-1])
            
        # find last_index, if stop_time is specified
        if stop_time != None and last_index == len(time_stamps)-1:
            if time_hours[-1] >= stop_time: 
                last_index = i
                print "\t found last index: %i at time %.2f hours" % (i, time_hours[-1])
    print "...done looping over time stamps"
            

    if last_time_stamp - time_stamps[0]  <= 0.0:
        print "last_time_stamp - time_stamps[0] = ", last_time_stamp - time_stamps[0]
        return

    # if the run is too short, recent times start at t0:
    if start_time_stamp_of_last_hour == None:
        start_index_of_last_hour = 0
        start_time_stamp_of_last_hour = time_stamps[0]

    # make a new array for "recent" times, the last hour or running or so
    recent_time = time_hours[start_index_of_last_hour:]

    # open a log file for writing:
    outfile = file("%s/log_%s.txt" % (directory, basename), 'w')
    plot_time = datetime.datetime.now()

    # ags wip

    start_time_hold = datetime.datetime.fromtimestamp(time_stamps[first_index]- 2082844800)
    end_time_hold = datetime.datetime.fromtimestamp(time_stamps[last_index]- 2082844800)
    
    #start_time = start_time_hold.strftime("%m-%d-%y %I:%M:%p")
    #end_time = end_time_hold.strftime("%m-%d-%y %I:%M:%p")
    time_string = "%s to %s" % (
        start_time_hold.strftime("%m-%d-%y %I:%M%p"),
        end_time_hold.strftime("%m-%d-%y %I:%M%p"),
    )
    #print time_string



    mass = 0.0
    Vol = []



    if len(mass_flow_rate) > 1:
      print "integrating %i mass flow rate points..." % len(mass_flow_rate)

      for (i_time, minute_time) in enumerate(time_minutes):

          delta_time_minutes  = 0.0
          if i_time > 0:
              delta_time_minutes = minute_time - time_minutes[i_time-1]

          mass += mass_flow_rate[i_time]*delta_time_minutes
          Vol.append(mass)

          #if i_time % 100 == 0: # debugging
          #  print "i: %i | time [min]: %.1f | delta_time_minutes: %.2f | rate [g/min]:%.2e | mass %.2f g" % (
          #  i_time, minute_time, delta_time_minutes, mass_flow_rate[i_time], mass)

      print "done with integral"

      # do a sanity check on the integral...
      #sum_mass_flow_rate = 0.0
      # this is not a time average:
      #for rate in mass_flow_rate: sum_mass_flow_rate += rate
      #average_flow_rate = sum_mass_flow_rate / len(mass_flow_rate)
      #total_flow_volume = average_flow_rate*time_minutes[-1]
      #total_flow_mass = total_flow_volume*xenon_density
      #print "\t average flow rate: %.4f L/min" % average_flow_rate
      #print "\t elapsed time: %.2e minutes" % time_minutes[-1]
      #print "\t total flow from average: %.4f L" % total_flow_volume
      #print "\t total flow from average: %.4f g" % total_flow_mass
      #print "\t total flow from integral: %.4f g" % mass
    
    print "--> starting plots..."

    # plot temperatures
    filename = os.path.join(directory, "Temp_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'Temperature', time_hours, time_stamps, TC0, TC1, TC2, TC3,
    TC4, TC15, TC10, T_ambient, T_LN_in, T_LN_out, T_Xe_bottle, T_max_set, T_min_set, first_index,
    last_index)

    # plot recent temperatures
    filename = os.path.join(directory, "Temp-recent_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'Recent Temperature', time_hours, time_stamps, TC0, TC1, TC2,
    TC3, TC4, TC15, TC10, T_ambient, T_LN_in, T_LN_out, T_Xe_bottle, T_max_set, T_min_set,
    first_index=start_index_of_last_hour)

    # plot LXe cell and Cu plate temperatures
    filename = os.path.join(directory, "Temp-cell_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'LXe cell and Cu plate temperature', time_hours, 
    time_stamps, TC0, TC1, TC2, TC3, TC4, first_index=first_index, last_index=last_index)

    # plot LXe cell and Cu plate recent temperatures
    filename = os.path.join(directory, "Temp-cell-recent_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'Recent LXe cell and Cu plate temperature',
    time_hours,time_stamps, TC0, TC1, TC2, TC3, TC4, first_index=start_index_of_last_hour)
    
    #plot just Ambient Temperature
    filename = os.path.join(directory, "Ambient_Only_%s.%s" % (basename, filetype))
    plot_temp_vs_lmass(filename, 'Bottle Mass vs Ambient Temp', time_hours, time_stamps, T_ambient, bottle_mass)

    linewidth=1
   

    if len(Vol) > 0:
      lxe_density = 3.0 # kg/L # FIXME to be more accurate
      xenon_volume = mass/lxe_density/1e3
      plt.figure(3)
      plt.grid(b=True)
      plt.title('Integrated mass flow (%.1f g of xenon = %.1f L LXe)' %
      (mass, xenon_volume))
      uline1 = plt.plot(time_hours[first_index:last_index],
      Vol[first_index:last_index])
      plt.setp(uline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Mass Flow [g of xenon]')
      plt.savefig(mfpath)
      print "printed %s" % mfpath
      plt.clf()
      
    plt.figure(4)
    plt.grid(b=True)
    plt.title('Valves / Heaters')
    # plot the lines:
    vline1 = plt.plot(time_hours[first_index:last_index], PLN[first_index:last_index])
    #vline2 = plt.plot(time_hours, SLN)
    vline3 = plt.plot(time_hours[first_index:last_index], Heat[first_index:last_index])
    # plot the fill areas:
    plt.fill_between(time_hours[first_index:last_index],PLN[first_index:last_index], color='b')
    plt.fill_between(time_hours[first_index:last_index],Heat[first_index:last_index], color='r')
    plt.setp(vline1, color = 'b', linewidth = 2.0, label = 'LN Valve',)
    #plt.setp(vline2, color = 'b', linewidth = 2.0, label = 'LN Valve 2')
    plt.setp(vline3, color = 'r', linewidth = 2.0, label = 'Heater',)
    plt.xlabel('Time [hours] %s' % time_string)
    plt.legend(loc = 'best', shadow = False)
    #plt.axis([0, time_hours[-1]*1.1, -0.2, 1.2])
    plt.savefig(vpath)
    print "printed %s" % vpath
    plt.clf()
    
    plt.figure(5)
    plt.grid(b=True)
    plt.title('Xenon system pressure XP3 (10k Torr Baratron)')
    pline1 = plt.plot(time_hours[first_index:last_index],
    Pressure[first_index:last_index])
    plt.setp(pline1, color = 'b', linewidth = linewidth)
    plt.xlabel('Time [hours] %s' % time_string)
    plt.ylabel('Pressure [Torr]')
    plt.savefig(ppath)
    print "printed %s" % ppath
    plt.clf()

    if len(Pressure2) > 0:
      plt.figure(6)
      plt.grid(b=True)
      plt.title('Vacuum system pressure XP5 (1k Torr Baratron)')
      pline1 = plt.plot(time_hours[first_index:last_index],
      Pressure2[first_index:last_index])
      plt.setp(pline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Pressure [Torr]')
      plt.savefig(ppath2)
      print "printed %s" % ppath2
      plt.clf()
      
    if len(mass_flow_rate) > 0:
      plt.figure(7)
      plt.title('Mass Flow Rate')
      plt.grid(b=True)
      mfline1 = plt.plot(time_hours[first_index:last_index],
      mass_flow_rate[first_index:last_index])
      plt.setp(mfline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Rate [grams/minute xenon gas]')
      plt.savefig(mfrpath)
      print "printed %s" % mfrpath
      plt.clf()

    if len(ccg_Pressure) > 0:

        try:
            outfile.write("XP4 (cold cathode gauge) pressure [Torr]: %.2e \n" % ccg_Pressure[-1])
            plt.figure(8)
            plt.grid(b=True)
            plt.title('Cold Cathode Pressure')
            mfline1 = plt.plot(time_hours[first_index:last_index],
            ccg_Pressure[first_index:last_index])
            plt.setp(mfline1, color = 'b', linewidth = linewidth)
            plt.yscale('log')
            plt.xlabel('Time [hours] %s' % time_string)
            plt.ylabel('Pressure [Torr]')
            plt.savefig(ccgpath_log)
            print "printed %s" % ccgpath_log
            plt.clf()

            plt.figure(9)
            plt.grid(b=True)
            plt.title('Recent Cold Cathode Pressure')
            mfline1 = plt.plot(recent_time, ccg_Pressure[start_index_of_last_hour:])
            plt.setp(mfline1, color = 'b', linewidth = linewidth)
            plt.yscale('log')
            plt.xlabel('Time [hours]')
            plt.ylabel('Pressure [Torr]')
            plt.savefig(rccgpath_log)
            print "printed %s" % rccgpath_log
            plt.clf()
        except ValueError:
            print "--> no log-scale CC gauge plots"
            pass

        # convert to micro torr for the linear plot:
        for i in xrange(len(ccg_Pressure)): ccg_Pressure[i]*=1e6 

        plt.figure(10)
        plt.grid(b=True)
        plt.title('Cold Cathode Pressure')
        mfline1 = plt.plot(time_hours[first_index:last_index],
        ccg_Pressure[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('Pressure [10^-6 Torr]')
        plt.savefig(ccgpath)
        print "printed %s" % ccgpath
        plt.clf()

        plt.figure(11)
        plt.grid(b=True)
        plt.title('Recent Cold Cathode Pressure')
        mfline1 = plt.plot(recent_time, ccg_Pressure[start_index_of_last_hour:])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours]')
        plt.ylabel('Pressure [10^-6 Torr]')
        plt.savefig(rccgpath)
        print "printed %s" % rccgpath
        plt.clf()
   
    if len(ln_mass) > 0:
        ln_density = 1.78 # lb / Liter
        # ln_mass is total mass (dewar tare weight + hooks + LN)
        old_amt_ln = ln_mass[start_index_of_last_hour] - ln_tare_mass[start_index_of_last_hour]
        new_amt_ln = ln_mass[last_index] - ln_tare_mass[last_index]
        print "old amt ln [lb]:", old_amt_ln
        print "new amt ln [lb]:", new_amt_ln
        print "recent time span:", recent_time_span
        ln_consumption_rate = (old_amt_ln - new_amt_ln) / (recent_time_span/3600.0)
        ln_consumption_rate_info = "LN consumption rate [lb / hour]: %.2f" %  ln_consumption_rate
        print ln_consumption_rate_info
        print "LN consumption rate [L / hour]:", ln_consumption_rate/ln_density
        try: 
            ln_hours_remaining = (new_amt_ln)/ ln_consumption_rate
        except ZeroDivisionError:
            ln_hours_remaining = -999.99
            
        print "LN time remaining: [hours]", ln_hours_remaining
        outfile.write("LN time remaining [hours]: %.2f \n" % ln_hours_remaining)
        outfile.write("LN consumption rate [lb/hour]: %.2f \n" % ln_consumption_rate)
        outfile.write("LN consumption rate [L/hour]: %.2f \n" % (ln_consumption_rate/ln_density))

        # estimate when LN dewar will be empty
        empty_time = datetime.datetime.fromtimestamp(
          time_stamps[last_index]- 2082844800 + ln_hours_remaining*3600.0)

        plt.figure(12)
        plt.grid(b=True)
        plt.title('LN mass (should run out in %.1f hours, at %s) \n total mass = %.1f lb, LN mass = %.1f lb (%.1f  L), tare = %.1f lb' % (
            ln_hours_remaining,
            empty_time.strftime("%m-%d-%y %I:%M%p"),
            new_amt_ln + ln_tare_mass[last_index],
            new_amt_ln,
            new_amt_ln/ln_density,
            ln_tare_mass[last_index],
        ))
        ln_line = plt.plot(time_hours[first_index:last_index],
            ln_mass[first_index:last_index], label = "Total mass")
        ln_tare_line = plt.plot(time_hours[first_index:last_index],
            ln_tare_mass[first_index:last_index], label = "Tare (dewar + hooks)")
        plt.setp(ln_line, color = 'b', linewidth = linewidth)
        plt.setp(ln_tare_line, color = 'red', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('LN mass - tare weight [lb]')
        legend = plt.legend(loc='best', shadow = False, fontsize='medium', ncol=2)
        plt.savefig(lnpath)
        print "printed %s" % lnpath
        plt.clf()
        outfile.write("LN total mass [lb]: %.3f \n" % ln_mass[-1])
        outfile.write("LN tare mass [lb]: %.3f \n" % ln_tare_mass[-1])
        outfile.write("LN mass [lb]: %.3f \n" % (ln_mass[-1] - ln_tare_mass[-1])) 



    if len(bottle_mass) > 0:
        plt.figure(13)
        plt.grid(b=True)
        plt.title('Xenon bottle mass')
        mfline1 = plt.plot(time_hours[first_index:last_index],
        bottle_mass[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('Mass [kg]')
        plt.savefig(bottle_mass_path)
        print "printed %s" % bottle_mass_path
        plt.clf()
        outfile.write("Xenon bottle mass [kg]: %.3f \n" % bottle_mass[-1])
        total_mass = 0.0
        for mass in bottle_mass[first_index:last_index]:
            total_mass += mass
        average_mass = total_mass / len(bottle_mass[first_index:last_index])
            
        print "average xenon bottle mass in this time period: %.3f kg" % average_mass

    if len(capacitance) > 0:
        plt.figure(14)
        plt.grid(b=True)
        plt.title('Xenon cell capacitance')
        mfline1 = plt.plot(time_hours[first_index:last_index],
        capacitance[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('Capacitance [pF]')
        plt.savefig(capacitance_path)
        print "printed %s" % capacitance_path
        plt.clf()
        outfile.write("Xenon cell capacitance [pF]: %.3f \n" % capacitance[-1])
    
    print "HFE pressure list length:", len(hfe_pressure)
    print "time list length:", len(time_hours)

    if len(hfe_pressure) > 0:
        if len(hfe_pressure) == len(time_hours):
            plt.figure(15)
            plt.grid(b=True)
            last_pressure = hfe_pressure[-1]
            last_pressure_psia = last_pressure/760*14.7
            title = 'HFE Pressure HP2 (%.1f torr = %.1f psia = %.1f psig)' % (
                last_pressure, 
                last_pressure_psia,
                last_pressure_psia - 14.7
            ) # FIXME -- make this conversion more accurate 
            plt.title(title)
            hfe_line = plt.plot(time_hours[first_index:last_index],
            hfe_pressure[first_index:last_index])
            plt.setp(hfe_line, color = 'b', linewidth = linewidth)
            plt.xlabel('Time [hours] %s' % time_string)
            plt.ylabel('Pressure [torr]')
            plt.savefig(hfep_path)
            print "printed %s" % hfep_path
            plt.clf()
            outfile.write("HP2 HFE Pressure [torr]: %.1f (%.1f psia, %.1f psig)\n" % (
                last_pressure, last_pressure_psia, last_pressure_psia-14.7))

            # plot the pressure difference, dP [torr]
            dP = []
            for i in xrange(len(hfe_pressure)): 
                dP.append(Pressure[i] - hfe_pressure[i])

            plt.figure(15)
            plt.grid(b=True)
            last_pressure = hfe_pressure[-1]
            last_pressure_psia = last_pressure/760*14.7
            title = 'dP = Xenon XP3 - HFE HP2 (should be <0) %.1f torr' % (dP[last_index]) 
            plt.title(title)
            dP_line = plt.plot(time_hours[first_index:last_index], dP[first_index:last_index])
            plt.setp(dP_line, color = 'b', linewidth = linewidth)
            plt.xlabel('Time [hours] %s' % time_string)
            plt.ylabel('Pressure [torr]')
            plt.savefig(dp_path)
            print "printed %s" % dp_path
            plt.clf()
            outfile.write("dP (Xenon XP3 - HFE XP2) [torr]: %.1f \n" % dP[-1])

        else:
            print "hfe_pressure list and time_hours list are different lengths"
            print "--> skipping HFE pressure plot"
            
    compare_isochoric(os.path.dirname(os.path.realpath(sys.argv[0])), directory, TC2[first_index:last_index], Pressure[first_index:last_index], time_hours[first_index:last_index])
    
    outfile.write("Xenon mass in cell (integrated mass flow) [g]: %.4f \n" % mass)
    outfile.write("XP5 Vacuum system (1k Torr Baratron) [Torr]: %.2f \n" % Pressure2[-1])
    outfile.write("XP3 Xenon system (10k Torr Baratron) [Torr]: %.2f \n" % Pressure[-1])
    outfile.write("Cu top [K]: %.3f (used for temp control) \n" % TC4[-1])
    outfile.write("Cu bot [K]: %.3f \n" % TC0[-1])
    outfile.write("Cell top [K]: %.3f \n" % TC1[-1])
    outfile.write("Cell mid [K]: %.3f \n" % TC2[-1])
    outfile.write("Cell bot [K]: %.3f \n" % TC3[-1])
    outfile.write("Ambient [K]: %.3f \n" % T_ambient[-1])

    if len(T_LN_in) > 0:
        outfile.write("LN F/T inlet [K]: %.3f \n" % T_LN_in[-1])

    if len(T_LN_out) > 0:
        outfile.write("LN F/T outlet [K]: %.3f \n" % T_LN_out[-1])

    if len(T_Xe_bottle) > 0:
        outfile.write("Xe bottle [K]: %.3f \n" % T_Xe_bottle[-1])

    if len(T_max_set) > 0:
        try:
            outfile.write("Setpoint max [K]: %.3f - %.3f \n" % (T_max_set[-1],
            T_max_set_offset[-1]))
        except:
            print "T_max_set info not available!"

    if len(T_min_set) > 0:
        try:
            outfile.write("Setpoint min [K]: %.3f + %.3f \n" % (T_min_set[-1],
            T_min_set_offset[-1]))
        except:
            print "T_min_set info not available!"

    outfile.write("Run duration: %s \n" % time_string)
    outfile.write("Plotting script run time: %s \n" % plot_time)
    outfile.write("Last LabView time stamp: %s \n" % datetime.datetime.fromtimestamp(time_stamps[-1]- 2082844800))
    outfile.close()


    print "done!!!!"
    
    # make a string that selects all plots that were produced:
    file_string = os.path.join(directory, "*%s.*" % basename)
    #print file_string
    return file_string
    
if __name__ == '__main__':

    usage = "argument: *.dat data file name"
    parser = OptionParser(usage)

    parser.add_option("--start",dest="start",type="float",default=None,
        help="specify start time, in hours, for plots (use first time in .dat file by default)")
    parser.add_option("--stop",dest="stop",type="float",default=None,
        help="specify stop time, in hours, for plots (use last time in .dat file by default)")
    options,args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        parser.error("==> Wrong number of arguments!")

    for filename in args:
        main(filename, options.start, options.stop)
        


