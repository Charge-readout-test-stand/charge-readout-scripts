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
9: Xe recovery bottle
10: T_min set point
11: T_max set point
12: Primary LN valve status
13: Secondar LN valve status
14: Heater 
15: Mass flow rate (uncorrected)
16: Mass flow rate [grams per minute Xe gas]
17: Pressure from 10k Torr baratron [Torr]
18: Pressure from 1k Torr baratron [Torr]
19: Cold cathode gauge [micro Torr]
20: TC gauge [Volts]
21: Bottle weight [kg]
22: Capacitance [pF]
23: T_max set point offset [K]
24: T_min set point offset [K]
"""

import os
import sys
import datetime
import matplotlib.pyplot as plt
from optparse import OptionParser
  
def plot_temperatures(filename, title, time_hours, TC0=None, TC1=None, TC2=None,
    TC3=None, TC4=None, T_ambient=None, T_LN_in=None, T_LN_out=None,
    T_Xe_bottle=None, T_max_set=None,
    T_min_set=None, first_index=0, last_index=-1):

    """
    This function makes a temperature plot
    """

    linewidth=1

    plt.figure(1)
    plt.title(title)
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

    plt.xlabel('Time [hours]')
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
    tcgpath = os.path.join(directory, "TCGauge_%s.%s" % (basename, filetype))
    bottle_mass_path = os.path.join(directory, "BottleMass_%s.%s" % (basename, filetype))
    capacitance_path = os.path.join(directory, "Capacitance_%s.%s" % (basename, filetype))


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
    tcg_Pressure = []
    bottle_mass = []
    capacitance = []

    # open the input file
    testfile = file(filename)

    # a column_offset to handle changes to LabView project
    column_offset = 0
    do_warning = True

    # The mass_flow_rate value saved by LabView is the uncorrected (not scaled
    # by the dial) output of the mass flow meter, multiplied by 5.28. 
    # xenon correction factor: 1.32 [MKS 1479 manual page 50]
    # xenon density at 0 C: 5.894 [MKS 1479 manual page 50]

    xenon_density = 5.89 # density of Xe gas [g/L at 0C]
    # xenon density at 300K: 5.3612 g / mL
    # correction for what alexis put in labview:
    xenon_density_ratio = xenon_density / 5.3612 # xenon density correction
    print "xenon_density_ratio: ", xenon_density_ratio

    xenon_gas_correction_factor = 1.32
    nitrogen_density = 1.25

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
            if do_warning:
                print "--> setting column_offset to %i !!" % column_offset
                do_warning = False


        # 11 Nov 2014 -- temperature set points were added to LabView plot
        if time_stamp > 3498586822: 
            column_offset = 5 
            if do_warning:
                print "--> setting column_offset to %i !!" % column_offset
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

        PLN.append(float(split_line[7+column_offset]))
        SLN.append(float(split_line[8+column_offset]))
        Heat.append(float(split_line[9+column_offset]))

        xenon_mass_flow = float(split_line[10+column_offset])*xenon_density_ratio
        nitrogen_mass_flow = xenon_mass_flow / xenon_gas_correction_factor / xenon_density * nitrogen_density
        mass_flow_rate.append(nitrogen_mass_flow)


          # mass_flow_rate from LabView is in grams / minute 



        Pressure.append(float(split_line[12+column_offset]))
        Pressure2.append(float(split_line[13+column_offset]))

        ccg_Pressure.append(float(split_line[14+column_offset])/1e6)
        tcg_Pressure.append(float(split_line[15+column_offset]))    
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

    # indices to use if start_time or stop_time are specified
    first_index = 0
    last_index = len(time_stamps)-1

    start_index_of_last_hour = None
    start_time_stamp_of_last_hour = None
    last_time_stamp = time_stamps[-1]

    # loop over time stamps, converting some units and searching for some
    # special indices
    for (i, time_stamp) in enumerate(time_stamps):
        seconds_elapsed = time_stamp - time_stamps[0]
        time_hours.append(seconds_elapsed/3600.0) # time in hours
        time_minutes.append(seconds_elapsed/60.0) # time in minutes

        # find time stamp recent_time_span from end of file:
        if start_index_of_last_hour == None:
            if last_time_stamp - time_stamp <= recent_time_span:
                start_index_of_last_hour = i
                start_time_stamp_of_last_hour = time_stamp
                print "found most recent time at i = %i of %i, t= %.2f" % (i, len(time_stamps),  start_time_stamp_of_last_hour)
                print "last timestamp = %.2f, diff = %.2f" % (last_time_stamp, last_time_stamp - start_time_stamp_of_last_hour )
                print "%i recent time stamps" % (len(time_stamps) - start_index_of_last_hour - 1)

        # find first_index, if start_time is specified
        if start_time != None and first_index == 0:
            if time_hours[-1] >= start_time: 
                first_index = i
                print "found first index: %i at time %.2f hours" % (i, time_hours[-1])
            
        # find last_index, if stop_time is specified
        if stop_time != None and last_index == len(time_stamps)-1:
            if time_hours[-1] >= stop_time: 
                last_index = i
                print "found last index: %i at time %.2f hours" % (i, time_hours[-1])
            

    if last_time_stamp - time_stamps[0]  <= 0.0:
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
    plot_temperatures(filename, 'Temperature', time_hours, TC0, TC1, TC2, TC3,
    TC4, T_ambient, T_LN_in, T_LN_out, T_Xe_bottle, T_max_set, T_min_set, first_index,
    last_index)

    # plot recent temperatures
    filename = os.path.join(directory, "Temp-recent_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'Recent Temperature', time_hours, TC0, TC1, TC2,
    TC3, TC4, T_ambient, T_LN_in, T_LN_out, T_Xe_bottle, T_max_set, T_min_set,
    first_index=start_index_of_last_hour)

    # plot LXe cell and Cu plate temperatures
    filename = os.path.join(directory, "Temp-cell_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'LXe cell and Cu plate temperature', time_hours,
    TC0, TC1, TC2, TC3, TC4, first_index=first_index, last_index=last_index)

    # plot LXe cell and Cu plate recent temperatures
    filename = os.path.join(directory, "Temp-cell-recent_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'Recent LXe cell and Cu plate temperature',
    time_hours, TC0, TC1, TC2, TC3, TC4, first_index=start_index_of_last_hour)

    linewidth=1
   

    if len(Vol) > 0:
      plt.figure(3)
      plt.grid(b=True)
      plt.title('Integrated mass flow (%.2f g of xenon)' % mass)
      uline1 = plt.plot(time_minutes[first_index:last_index],
      Vol[first_index:last_index])
      plt.setp(uline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [minutes]')
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
    plt.xlabel('Time [hours]')
    plt.legend(loc = 'best', shadow = False)
    #plt.axis([0, time_hours[-1]*1.1, -0.2, 1.2])
    plt.savefig(vpath)
    print "printed %s" % vpath
    plt.clf()
    
    plt.figure(5)
    plt.grid(b=True)
    plt.title('Xenon system pressure (10k Torr Baratron)')
    pline1 = plt.plot(time_hours[first_index:last_index],
    Pressure[first_index:last_index])
    plt.setp(pline1, color = 'b', linewidth = linewidth)
    plt.xlabel('Time [hours]')
    plt.ylabel('Pressure [Torr]')
    plt.savefig(ppath)
    print "printed %s" % ppath
    plt.clf()

    if len(Pressure2) > 0:
      plt.figure(6)
      plt.grid(b=True)
      plt.title('Vacuum system pressure (1k Torr Baratron)')
      pline1 = plt.plot(time_hours[first_index:last_index],
      Pressure2[first_index:last_index])
      plt.setp(pline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [hours]')
      plt.ylabel('Pressure [Torr]')
      plt.savefig(ppath2)
      print "printed %s" % ppath2
      plt.clf()
      
    if len(mass_flow_rate) > 0:
      plt.figure(7)
      plt.title('Mass Flow Rate')
      plt.grid(b=True)
      mfline1 = plt.plot(time_minutes[first_index:last_index],
      mass_flow_rate[first_index:last_index])
      plt.setp(mfline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [minutes]')
      plt.ylabel('Rate [grams/minute xenon gas]')
      plt.savefig(mfrpath)
      print "printed %s" % mfrpath
      plt.clf()

    if len(ccg_Pressure) > 0:

        try:
            outfile.write("CC pressure [Torr]: %.2e \n" % ccg_Pressure[-1])
            plt.figure(8)
            plt.grid(b=True)
            plt.title('Cold Cathode Pressure')
            mfline1 = plt.plot(time_hours[first_index:last_index],
            ccg_Pressure[first_index:last_index])
            plt.setp(mfline1, color = 'b', linewidth = linewidth)
            plt.yscale('log')
            plt.xlabel('Time [hours]')
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
        plt.xlabel('Time [hours]')
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
   
    if len(tcg_Pressure) > 0:
        plt.figure(12)
        plt.grid(b=True)
        plt.title('TC Gauge Pressure')
        mfline1 = plt.plot(time_hours[first_index:last_index],
        tcg_Pressure[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours]')
        plt.ylabel('Signal [V]')
        plt.savefig(tcgpath)
        print "printed %s" % tcgpath
        plt.clf()
        outfile.write("TC pressure [V]: %.3f \n" % tcg_Pressure[-1])

    if len(bottle_mass) > 0:
        plt.figure(13)
        plt.grid(b=True)
        plt.title('Xenon bottle mass')
        mfline1 = plt.plot(time_hours[first_index:last_index],
        bottle_mass[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours]')
        plt.ylabel('Mass [kg]')
        plt.savefig(bottle_mass_path)
        print "printed %s" % bottle_mass_path
        plt.clf()
        outfile.write("Xenon bottle mass [kg]: %.3f \n" % bottle_mass[-1])

    if len(capacitance) > 0:
        plt.figure(14)
        plt.grid(b=True)
        plt.title('Xenon cell capacitance')
        mfline1 = plt.plot(time_hours[first_index:last_index],
        capacitance[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours]')
        plt.ylabel('Capacitance [pF]')
        plt.savefig(capacitance_path)
        print "printed %s" % capacitance_path
        plt.clf()
        outfile.write("Xenon cell capacitance [pF]: %.3f \n" % capacitance[-1])

    outfile.write("Xenon mass, integrated mass flow [g]: %.4f \n" % mass)

    outfile.write("Vacuum system 1k Torr Baratron [Torr]: %.2f \n" % Pressure2[-1])
    outfile.write("Xenon system 10k Torr Baratron [Torr]: %.2f \n" % Pressure[-1])
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
        help="specify start time, in hours, for plots (use first time in .dat file by defaulg)")
    parser.add_option("--stop",dest="stop",type="float",default=None,
        help="specify stop time, in hours, for plots (use last time in .dat file by defaulg)")
    options,args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        parser.error("==> Wrong number of arguments!")

    for filename in args:
        main(filename, options.start, options.stop)
        


