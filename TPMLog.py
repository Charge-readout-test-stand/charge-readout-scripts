#Plots temperature, recent temperature, mass flow, pressure, and valve record in to separate files
#Plot name = DataType_Date_Index
#*.dat columns:
#1: time
#2: TC0 
#3: TC1
#4: TC2 
#5: TC3 
#6: TC4
#7: TC5
#8: PLN valve status
#9: SLN valve status
#10: Heater 
#11: UncorrMFR
#12: MFR
#13: Pressure

import os, glob, sys
import matplotlib.pyplot as plt
import numpy as np

def main(filename):
    testfile = file(filename)
    print "--> processing", filename
    # on the windows computer:
    directory = 'C://Users//xenon//Dropbox//labViewPlots/'
    if not os.path.isdir(directory):
        print "trying alexis' path..."
        
    tFile = "Temp_%s.%s" % (os.path.split(filename)[1][5:-4], 'jpeg')
    rtFile = "rTemp_%s.%s" % (os.path.split(filename)[1][5:-4], 'jpeg')
    mfFile = "MassFlow_%s.%s" % (os.path.split(filename)[1][5:-4], 'jpeg')
    vFile = "Vavle_%s.%s" %(os.path.split(filename)[1][5:-4], 'jpeg')
    pFile = "Pressure_%s.%s" %(os.path.split(filename)[1][5:-4], 'jpeg')
    mfrFile = "MassFlowRate_%s.%s" % (os.path.split(filename)[1][5:-4], 'jpeg')
    tpath = os.path.join(directory,tFile)
    rtpath = os.path.join(directory,rtFile)
    mfpath = os.path.join(directory,mfFile)
    vpath = os.path.join(directory,vFile)
    ppath = os.path.join(directory,pFile)
    mfrpath = os.path.join(directory, mfrFile)

    time = []
    time_1 = []
    time_2 = []
    time_3 = []
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
    for  line in testfile:
        split_line = line.split()
        data = []
        time.append(float(split_line[0]))
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
    
    for i in time:
        i = round(i - time[0])
        time_1.append(float(i/3600))
    for i in time_1:
        time_3.append(float(i*60))
    for i in time_1:
        if time_1[-1]-i < 1:
            time_2.append(-(float(i)-time_1[-1]))
        else: None    
    for i in time_2:
        rtime.insert(0, i*60)    
    if len(rtime) > 300:
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
    else:
        rTC0 = TC0
        rTC1 = TC1
        rTC2 = TC2
        rTC3 = TC3
        rTC4 = TC4
        rTC5 = TC5
        rMFR = MFR
        rPLN = PLN
        rSLN = SLN
        rHeat = Heat
        rPressure = Pressure    
    
    for i in time_3:
        if i == time_3[-1]:
            volume = np.trapz(MFR, time_3, 0.5)
            Vol.append(volume)
        else:
            volume = np.trapz(MFR[0:time_3.index(i)+1],time_3[0:time_3.index(i)+1], 0.5)
            Vol.append(volume)
    
    plt.figure(1)
    plt.title('Temperature')
    line1 = plt.plot(time_1, TC0)
    line2 = plt.plot(time_1, TC1)
    line3 = plt.plot(time_1, TC2)
    line4 = plt.plot(time_1, TC3)
    line5 = plt.plot(time_1, TC4)
    line6 = plt.plot(time_1, TC5)
    plt.setp(line1, color = 'r', linewidth = 0.5, label = 'CuBot')
    plt.setp(line2, color = 'b', linewidth = 0.5, label = 'CellTop')
    plt.setp(line3, color = 'g', linewidth = 0.5, label = 'CellMid')
    plt.setp(line4, color = 'm', linewidth = 0.5, label = 'CellBot')
    plt.setp(line5, color = 'k', linewidth = 0.5, label = 'CuTop')
    plt.setp(line6, color = 'c', linewidth = 0.5, label = 'Ambient')
    plt.xlabel('Time in hrs')
    legend = plt.legend(loc='center right', shadow = False)
    plt.savefig(tpath)
    plt.clf()
    
    plt.figure(2)
    plt.title('Recent Temperature')
    rline1 = plt.plot(rtime, rTC0)
    rline2 = plt.plot(rtime, rTC1)
    rline3 = plt.plot(rtime, rTC2)
    rline4 = plt.plot(rtime, rTC3)
    rline5 = plt.plot(rtime, rTC4)
    rline6 = plt.plot(rtime, rTC5)
    plt.setp(rline1, color = 'r', linewidth = 0.5, label = 'CuBot')
    plt.setp(rline2, color = 'b', linewidth = 0.5, label = 'CellTop')
    plt.setp(rline3, color = 'g', linewidth = 0.5, label = 'CellMid')
    plt.setp(rline4, color = 'm', linewidth = 0.5, label = 'CellBot')
    plt.setp(rline5, color = 'k', linewidth = 0.5, label = 'CuTop')
    plt.setp(rline6, color = 'c', linewidth = 0.5, label = 'Ambient')
    plt.xlabel('Time in mins')
    legend = plt.legend(loc='center right', shadow = False)
    plt.savefig(rtpath)
    plt.clf()
    
    plt.figure(3)
    plt.title('Mass Flow in L')
    uline1 = plt.plot(time_3, Vol)
    plt.setp(uline1, color = 'b', linewidth = 0.4)
    plt.xlabel('Time in mins')
    plt.savefig(mfpath)
    plt.clf()
    
    plt.figure(4)
    plt.title('Valves')
    vline1 = plt.plot(time_1, PLN)
    vline2 = plt.plot(time_1, SLN)
    vline3 = plt.plot(time_1, Heat)
    plt.setp(vline1, color = 'r', linewidth = 2.0, label = 'PLN Valve', ls = '-')
    plt.setp(vline2, color = 'b', linewidth = 2.0, label = 'SLN Vavle', ls = '--')
    plt.setp(vline3, color = 'g', linewidth = 2.0, label = 'Heater', ls = '--')
    plt.xlabel('Time in hrs')
    plt.legend(loc = 'center right', shadow = False)
    plt.axis([0, time_1[-1]*1.1, -0.2, 1.2])
    plt.savefig(vpath)
    plt.clf()
    
    plt.figure(5)
    plt.title('Pressure in torr')
    pline1 = plt.plot(time_1, Pressure)
    plt.setp(pline1, color = 'b', linewidth = 0.4)
    plt.xlabel('Time in hrs')
    plt.savefig(ppath)
    plt.clf()
    
    plt.figure(6)
    plt.title('Mass Flow Rate in L/min')
    mfline1 = plt.plot(time_3, MFR)
    plt.setp(mfline1, color = 'b', linewidth = 0.4)
    plt.xlabel('Time in mins')
    plt.savefig(mfrpath)
    plt.clf()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "argument:  *.dat data file name"
        sys.exit()
    filename = sys.argv[1]
    main(filename)