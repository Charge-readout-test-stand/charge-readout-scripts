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
6: TC5
7: PLN valve status
8: SLN valve status
9: Heater 
10: Mass flow rate (uncorrected)
11: Mass flow rate [Liters of Xe gas]
12: Pressure from 10k Torr baratron [Torr]
13: Pressure from 1k Torr baratron [Torr]
14: Cold cathode gauge [micro Torr]
15: TC gauge [Volts]
16: Bottle weight [kg]
18: Capacitance [pF]
"""

import os
import sys
import datetime
import matplotlib.pyplot as plt
#import numpy as np


def main(filename):
    testfile = file(filename)
    print "--> processing", filename
    # on the windows DAQ machine:
    directory = 'C://Users//xenon//Dropbox//labViewPlots/'
    if not os.path.isdir(directory):
        print "trying alexis' path..."
        #directory = '/Users/alexis/stanford-Dropbox/Dropbox/labViewPlots/'
        directory = '/Users/alexis/Downloads/'
        
    basename = os.path.split(filename)[1][5:-4]

    recent_time_span = 3600.0 # seconds to use for "recent" plots
    
    filetype = 'jpeg'    
    tpath = os.path.join(directory, "Temp_%s.%s" % (basename, filetype))
    rtpath = os.path.join(directory, "Temp-recent_%s.%s" % (basename, filetype))
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

    time_stamps = [] # labview timestamp, in seconds
    time_hours = [] # elapsed time in hours
    time_2 = []
    time_minutes = [] # elapsed time in minutes
    rtime = []
    TC0 = []
    TC1 = []
    TC2 = []
    TC3 = []
    TC4 = []
    TC5 = []
    MFR = []
    PLN = []
    SLN = []
    Heat = []
    Pressure = []
    Pressure2 = []
    ccg_Pressure = []
    tcg_Pressure = []
    bottle_mass = []
    capacitance = []

    # read values from input file:
    for (i_line, line) in enumerate(testfile):
        split_line = line.split()
        data = []
        time_stamps.append(float(split_line[0]))
        TC0.append(float(split_line[1]))
        TC1.append(float(split_line[2]))
        TC2.append(float(split_line[3]))
        TC3.append(float(split_line[4]))
        TC4.append(float(split_line[5]))
        TC5.append(float(split_line[6]))
        PLN.append(0.8*float(split_line[7]))
        SLN.append(float(split_line[8]))
        Heat.append(1.2*float(split_line[9]))
        MFR.append(float(split_line[10]))
        Pressure.append(float(split_line[12]))
        Pressure2.append(float(split_line[13]))
        ccg_Pressure.append(float(split_line[14])/1e6)
        tcg_Pressure.append(float(split_line[15]))    
        bottle_mass.append(float(split_line[16])) 
        try:   
         capacitance.append(float(split_line[17]))
        except IndexError:
            #print "column 16 doesn't exist!"
            pass
        #if i_line % 1000 == 0:
        #  print "line %i" % i_line

    start_index_of_last_hour = None
    start_time_stamp_of_last_hour = None
    last_time_stamp = time_stamps[-1]
    for (i, time_stamp) in enumerate(time_stamps):
        seconds_elapsed = round(time_stamp - time_stamps[0])
        time_hours.append(float(seconds_elapsed/3600)) # time in hours
        time_minutes.append(float(seconds_elapsed/60)) # time in minutes
        # find time stamp from one hour ago:
        if start_index_of_last_hour == None:
            if last_time_stamp - time_stamp <= recent_time_span:
                start_index_of_last_hour = i
                start_time_stamp_of_last_hour = time_stamp
                print "found most recent time at i = %i of %i, t= %.2f" % (i, len(time_stamps),  start_time_stamp_of_last_hour)
                print "last timestamp = %.2f, diff = %.2f" % (last_time_stamp, last_time_stamp - start_time_stamp_of_last_hour )
                print "%i recent time stamps" % (len(time_stamps) - start_index_of_last_hour - 1)

    if last_time_stamp - time_stamps[0]  <= 0.0:
        return

    # if the run is too short, recent times start at t0:
    if start_time_stamp_of_last_hour == None:
        start_index_of_last_hour = 0
        start_time_stamp_of_last_hour = time_stamps[0]

    rtime = time_hours[start_index_of_last_hour:]
    # subtract off t0 from every time
    #rtime[:] = [x - time_hours[0] for x in rtime]

    # open a log file for writing:
    outfile = file("%s/log_%s.txt" % (directory, basename), 'w')
    plot_time = datetime.datetime.now()

    rTC0 = TC0[-len(rtime):]
    rTC1 = TC1[-len(rtime):]
    rTC2 = TC2[-len(rtime):]
    rTC3 = TC3[-len(rtime):]
    rTC4 = TC4[-len(rtime):]
    rTC5 = TC5[-len(rtime):]
    rMFR = MFR[-len(rtime):]
    rPLN = PLN[-len(rtime):]
    rSLN = SLN[-len(rtime):]
    rHeat = Heat[-len(rtime):]
    rPressure = Pressure[-len(rtime):]
    rccg_Pressure = ccg_Pressure[-len(rtime):]

    volume = 0.0
    Vol = []
    if len(MFR) > 1:
      print "integrating %i mass flow rate points..." % len(MFR)
      for (i_time, minute_time) in enumerate(time_minutes):
          if i_time == len(time_minutes)-1:
              #volume = np.trapz(MFR, time_minutes, 0.5)
              volume += MFR[i_time]*5.89
              # the factor 5.89 is the density of Xe gas [g/L] at 0C
              Vol.append(volume)
          else:
              #volume = np.trapz(MFR[0:i_time+1],time_minutes[0:i_time+1], 0.5)
              volume += MFR[i_time]*5.89
              # the factor 5.89 is the density of Xe gas [g/L] at 0C
              Vol.append(volume)
              #if i_time % 100 == 0:
              #  print "mfr time %i" % i_time

      print "done with numpy integral"
      sum_mass_flow_rate = 0.0
      for rate in MFR: sum_mass_flow_rate += rate
      average_flow_rate = sum_mass_flow_rate / len(MFR)
      print "average flow rate: %.4f L/min" % average_flow_rate
    
    print "starting plots..."

    linewidth=1
    plt.figure(1)
    plt.title('Temperature')
    plt.grid(b=True)
    line1 = plt.plot(time_hours, TC0)
    line2 = plt.plot(time_hours, TC1)
    line3 = plt.plot(time_hours, TC2)
    line4 = plt.plot(time_hours, TC3)
    line5 = plt.plot(time_hours, TC4)
    line6 = plt.plot(time_hours, TC5)
    plt.setp(line1, color = 'r', linewidth = linewidth, label = 'CuBot')
    plt.setp(line2, color = 'b', linewidth = linewidth, label = 'CellTop')
    plt.setp(line3, color = 'g', linewidth = linewidth, label = 'CellMid')
    plt.setp(line4, color = 'm', linewidth = linewidth, label = 'CellBot')
    plt.setp(line5, color = 'k', linewidth = linewidth, label = 'CuTop')
    plt.setp(line6, color = 'c', linewidth = linewidth, label = 'Ambient')
    plt.xlabel('Time [hours]')
    plt.ylabel('Temperature [K]')
    legend = plt.legend(loc='best', shadow = False)
    plt.savefig(tpath)
    print "printed %s" % tpath
    plt.clf()
    
    plt.figure(2)
    plt.title('Recent Temperature')
    plt.grid(b=True)
    rline1 = plt.plot(rtime, rTC0)
    rline2 = plt.plot(rtime, rTC1)
    rline3 = plt.plot(rtime, rTC2)
    rline4 = plt.plot(rtime, rTC3)
    rline5 = plt.plot(rtime, rTC4)
    rline6 = plt.plot(rtime, rTC5)
    plt.setp(rline1, color = 'r', linewidth = linewidth, label = 'CuBot')
    plt.setp(rline2, color = 'b', linewidth = linewidth, label = 'CellTop')
    plt.setp(rline3, color = 'g', linewidth = linewidth, label = 'CellMid')
    plt.setp(rline4, color = 'm', linewidth = linewidth, label = 'CellBot')
    plt.setp(rline5, color = 'k', linewidth = linewidth, label = 'CuTop')
    plt.setp(rline6, color = 'c', linewidth = linewidth, label = 'Ambient')
    plt.xlabel('Time [hours]')
    plt.ylabel('Temperature [K]')
    plt.legend(loc='best', shadow = False)
    plt.savefig(rtpath)
    print "printed %s" % rtpath
    plt.clf()
    
    if len(Vol) > 0:
      plt.figure(3)
      plt.grid(b=True)
      plt.title('Integrated mass flow (%.2f g of xenon)' % volume)
      uline1 = plt.plot(time_minutes, Vol)
      plt.setp(uline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [minutes]')
      plt.ylabel('Mass Flow [g of xenon]')
      plt.savefig(mfpath)
      print "printed %s" % mfpath
      plt.clf()
      
    plt.figure(4)
    plt.grid(b=True)
    plt.title('Valves / Heaters')
    vline1 = plt.plot(time_hours, PLN)
    #vline2 = plt.plot(time_hours, SLN)
    vline3 = plt.plot(time_hours, Heat)
    plt.setp(vline1, color = 'r', linewidth = 2.0, label = 'LN Valve', ls = '-')
    #plt.setp(vline2, color = 'b', linewidth = 2.0, label = 'LN Valve 2', ls = '--')
    plt.setp(vline3, color = 'g', linewidth = 2.0, label = 'Heater', ls = '--')
    plt.xlabel('Time [hours]')
    plt.legend(loc = 'center right', shadow = False)
    plt.axis([0, time_hours[-1]*1.1, -0.2, 1.2])
    plt.savefig(vpath)
    print "printed %s" % vpath
    plt.clf()
    
    plt.figure(5)
    plt.grid(b=True)
    plt.title('Pressure (10k Torr Baratron)')
    pline1 = plt.plot(time_hours, Pressure)
    plt.setp(pline1, color = 'b', linewidth = linewidth)
    plt.xlabel('Time [hours]')
    plt.ylabel('Pressure [Torr]')
    plt.savefig(ppath)
    print "printed %s" % ppath
    plt.clf()

    if len(Pressure2) > 0:
      plt.figure(6)
      plt.grid(b=True)
      plt.title('Pressure (1k Torr Baratron)')
      pline1 = plt.plot(time_hours, Pressure2)
      plt.setp(pline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [hours]')
      plt.ylabel('Pressure [Torr]')
      plt.savefig(ppath2)
      print "printed %s" % ppath2
      plt.clf()
      
    if len(MFR) > 0:
      plt.figure(7)
      plt.title('Mass Flow Rate')
      plt.grid(b=True)
      mfline1 = plt.plot(time_minutes, MFR)
      plt.setp(mfline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [minutes]')
      plt.ylabel('Rate [L/min xenon gas]')
      plt.savefig(mfrpath)
      print "printed %s" % mfrpath
      plt.clf()

    if len(ccg_Pressure) > 0:

        try:
            outfile.write("CC pressure [Torr]: %.2e \n" % ccg_Pressure[-1])
            plt.figure(8)
            plt.grid(b=True)
            plt.title('Cold Cathode Pressure')
            mfline1 = plt.plot(time_hours, ccg_Pressure)
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
            mfline1 = plt.plot(rtime, rccg_Pressure)
            plt.setp(mfline1, color = 'b', linewidth = linewidth)
            plt.yscale('log')
            plt.xlabel('Time [hours]')
            plt.ylabel('Pressure [Torr]')
            plt.savefig(rccgpath_log)
            print "printed %s" % rccgpath_log
            plt.clf()
        except ValueError:
            pass

        # convert to micro torr for the linear plot:
        for i in xrange(len(ccg_Pressure)): ccg_Pressure[i]*=1e6 
        for i in xrange(len(rccg_Pressure)): rccg_Pressure[i]*=1e6 

        plt.figure(10)
        plt.grid(b=True)
        plt.title('Cold Cathode Pressure')
        mfline1 = plt.plot(time_hours, ccg_Pressure)
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours]')
        plt.ylabel('Pressure [10^-6 Torr]')
        plt.savefig(ccgpath)
        print "printed %s" % ccgpath
        plt.clf()

        plt.figure(11)
        plt.grid(b=True)
        plt.title('Recent Cold Cathode Pressure')
        mfline1 = plt.plot(rtime, rccg_Pressure)
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
        mfline1 = plt.plot(time_hours, tcg_Pressure)
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
        mfline1 = plt.plot(time_hours, bottle_mass)
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
        mfline1 = plt.plot(time_hours, capacitance)
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours]')
        plt.ylabel('Capacitance [pF]')
        plt.savefig(capacitance_path)
        print "printed %s" % capacitance_path
        plt.clf()
        outfile.write("Xenon cell capacitance [pF]: %.3f \n" % capacitance[-1])


    outfile.write("1k Torr Baratron [Torr]: %.2f \n" % Pressure2[-1])
    outfile.write("10k Torr Baratron [Torr]: %.2f \n" % Pressure[-1])
    outfile.write("Cu bot [K]: %.3f \n" % TC0[-1])
    outfile.write("Cell top [K]: %.3f \n" % TC1[-1])
    outfile.write("Cell mid [K]: %.3f \n" % TC2[-1])
    outfile.write("Cell bot [K]: %.3f \n" % TC3[-1])
    outfile.write("Cu top [K]: %.3f \n" % TC4[-1])
    outfile.write("Ambient [K]: %.3f \n" % TC5[-1])
    outfile.write("Plotting script run time: %s \n" % plot_time)
    outfile.write("Last labview time stamp: %s \n" % datetime.datetime.fromtimestamp(time_stamps[-1]- 2082844800))
    outfile.close()


    print "done!!!!"
    
    # make a string that selects all plots that were produced:
    file_string = os.path.join(directory, "*%s.*" % basename)
    #print file_string
    return file_string
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "argument:  *.dat data file name"
        sys.exit()

    for filename in sys.argv[1:]:
        main(filename)
