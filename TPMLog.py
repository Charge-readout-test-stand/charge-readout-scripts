"""
This script plots temperature, recent temperature, mass flow, pressure, and
valve status

The main function returns a string that can be used with glob to select all
plots that are produced.

Plot names = DataType_Date_Index*.jpeg

*.dat file columns:
1: time [seconds]
2: TC0 [K]
3: TC1
4: TC2 
5: TC3 
6: TC4
7: TC5
8: PLN valve status
9: SLN valve status
10: Heater 
11: UncorrMFR
12: MFR
13: Pressure from 10k Torr baratron [Torr]
14: Pressure from 1k Torr baratron [Torr]
"""

import os
import sys
import matplotlib.pyplot as plt
import numpy as np


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
    
    filetype = 'jpeg'    
    tpath = os.path.join(directory, "Temp_%s.%s" % (basename, filetype))
    rtpath = os.path.join(directory, "rTemp_%s.%s" % (basename, filetype))
    mfpath = os.path.join(directory, "MassFlow_%s.%s" % (basename, filetype))
    vpath = os.path.join(directory, "ValveStates_%s.%s" % (basename, filetype))
    ppath = os.path.join(directory, "Pressure-10kTorr_%s.%s" % (basename, filetype))
    ppath2 = os.path.join(directory, "Pressure-1kTorr_%s.%s" % (basename, filetype))
    mfrpath = os.path.join(directory, "MassFlowRate_%s.%s" % (basename, filetype))

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
    Vol = []
    PLN = []
    SLN = []
    Heat = []
    Pressure = []
    Pressure2 = []

    # read values from input file:
    for line in testfile:
        split_line = line.split()
        data = []
        time_stamps.append(float(split_line[0]))
        TC0.append(float(split_line[1]))
        TC1.append(float(split_line[2]))
        TC2.append(float(split_line[3]))
        TC3.append(float(split_line[4]))
        TC4.append(float(split_line[5]))
        TC5.append(float(split_line[6]))
        MFR.append(float(split_line[10]))
        PLN.append(0.8*float(split_line[7]))
        SLN.append(float(split_line[8]))
        Heat.append(1.2*float(split_line[9]))
        Pressure.append(float(split_line[12]))
        Pressure2.append(float(split_line[13]))
    

    start_index_of_last_hour = None
    start_time_stamp_of_last_hour = None
    last_time_stamp = time_stamps[-1]
    for (i, time_stamp) in enumerate(time_stamps):
        seconds_elapsed = round(time_stamp - time_stamps[0])
        time_hours.append(float(seconds_elapsed/3600)) # time in hours
        time_minutes.append(float(seconds_elapsed/60)) # time in minutes
        # find time stamp from one hour ago:
        if start_index_of_last_hour == None:
            if last_time_stamp - time_stamp <= 3600:
                start_index_of_last_hour = i
                start_time_stamp_of_last_hour = time_stamp
                print "found most recent time at i = %i of %i, t= %.2f" % (i, len(time_stamps),  start_time_stamp_of_last_hour)
                print "last timestamp = %.2f, diff = %.2f" % (last_time_stamp, last_time_stamp - start_time_stamp_of_last_hour )
                print "%i recent time stamps" % (len(time_stamps) - start_index_of_last_hour - 1)

    # if the run is too short, recent times start at t0:
    if start_time_stamp_of_last_hour == None:
        start_index_of_last_hour = 0
        start_time_stamp_of_last_hour = time_stamps[0]

    rtime = time_hours[start_index_of_last_hour:-1]
    # subtract off t0 from every time
    #rtime[:] = [x - time_minutes[0] for x in rtime]

    rTC0 = TC0[-len(rtime):]
    rTC1 = TC1[-len(rtime):]
    rTC2 = TC2[-len(rtime):]
    rTC3 = TC3[-len(rtime):]
    rTC4 = TC4[-len(rtime):]
    rTC5 = TC5[-len(rtime):]
    rMFR = MFR[-len(rtime):]
    rPLN = PLN[-len(rtime):]
    rSLN = SLN[-len(rtime):]
    rHeat = Heat[-len(rtime)-1:-1]
    rPressure = Pressure[-len(rtime)-1:-1]

    for i in time_minutes:
        if i == time_minutes[-1]:
            volume = np.trapz(MFR, time_minutes, 0.5)
            Vol.append(volume)
        else:
            volume = np.trapz(MFR[0:time_minutes.index(i)+1],time_minutes[0:time_minutes.index(i)+1], 0.5)
            Vol.append(volume)

    sum_mass_flow_rate = 0.0
    for rate in MFR: sum_mass_flow_rate += rate
    average_flow_rate = sum_mass_flow_rate / len(MFR)
    print "average flow rate: %.4f L/min" % average_flow_rate
    
    linewidth=1
    plt.figure(1)
    plt.title('Temperature')
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
    plt.xlabel('Time in hrs')
    plt.ylabel('Temperature [K]')
    legend = plt.legend(loc='best', shadow = False)
    plt.savefig(tpath)
    plt.clf()
    
    plt.figure(2)
    plt.title('Recent Temperature')
    rline1 = plt.plot(rtime, rTC0, linewidth=linewidth)
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
    plt.xlabel('Time [minutes]')
    plt.ylabel('Temperature [K]')
    plt.legend(loc='best', shadow = False)
    plt.savefig(rtpath)
    plt.clf()
    
    plt.figure(3)
    plt.title('Integrated mass flow (%.2f L of xenon gas)' % volume)
    uline1 = plt.plot(time_minutes, Vol)
    plt.setp(uline1, color = 'b', linewidth = 0.4)
    plt.xlabel('Time [minutes]')
    plt.ylabel('Mass Flow [L of xenon gas]')
    plt.savefig(mfpath)
    plt.clf()
    
    plt.figure(4)
    plt.title('Valves')
    vline1 = plt.plot(time_hours, PLN)
    vline2 = plt.plot(time_hours, SLN)
    vline3 = plt.plot(time_hours, Heat)
    plt.setp(vline1, color = 'r', linewidth = 2.0, label = 'PLN Valve', ls = '-')
    plt.setp(vline2, color = 'b', linewidth = 2.0, label = 'SLN Vavle', ls = '--')
    plt.setp(vline3, color = 'g', linewidth = 2.0, label = 'Heater', ls = '--')
    plt.xlabel('Time in hrs')
    plt.legend(loc = 'center right', shadow = False)
    plt.axis([0, time_hours[-1]*1.1, -0.2, 1.2])
    plt.savefig(vpath)
    plt.clf()
    
    plt.figure(5)
    plt.title('Pressure (10k Torr Baratron)')
    pline1 = plt.plot(time_hours, Pressure)
    plt.setp(pline1, color = 'b', linewidth = 0.4)
    plt.xlabel('Time [hrs]')
    plt.ylabel('Pressure [Torr]')
    plt.savefig(ppath)
    plt.clf()

    plt.figure(6)
    plt.title('Pressure (1k Torr Baratron)')
    pline1 = plt.plot(time_hours, Pressure2)
    plt.setp(pline1, color = 'b', linewidth = 0.4)
    plt.xlabel('Time [hrs]')
    plt.ylabel('Pressure [Torr]')
    plt.savefig(ppath2)
    plt.clf()
    
    plt.figure(7)
    plt.title('Mass Flow Rate')
    mfline1 = plt.plot(time_minutes, MFR)
    plt.setp(mfline1, color = 'b', linewidth = 0.4)
    plt.xlabel('Time [minutes]')
    plt.ylabel('Rate [L/min xenon gas]')
    plt.savefig(mfrpath)
    plt.clf()

    print "done!!!!"
    
    # make a string that selects all plots that were produced:
    file_string = os.path.join(directory, "*%s*.%s" % (basename, filetype))
    #print file_string
    return file_string
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "argument:  *.dat data file name"
        sys.exit()
    filename = sys.argv[1]
    main(filename)
