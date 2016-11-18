"""
This script plots temperature, recent temperature, mass flow, pressure, and
valve status

The main function returns a string that can be used with glob to select all
plots that are produced.

Plot names = DataType_Date_Index*.jpeg

*.dat file columns:
0: time [seconds]
1: TC0 Cu Bot [K]
2: TC1 Cell Top
3: TC2 Cell Mid
4: TC3 Cell Bot
5: TC4 Cu Top (control TC)
6: T_ambient
7: LN F/T inlet TC [K]
8: LN F/T outlet TC [K]
9: Xe recovery bottle [K]
10: T_min set point
11: T_max set point
12: TC15 on valve XV5 [K] (for t > 3500502750)
13: TC10, regulator temperature [K] (for t > 3500502750)
14: Omega temp (t > 3520358622, added 21 July 2015)

15: LN valve status
16: LN enabled (enabled instead of "secondary" t > 3520358622, 21 July 2015)
17: Heater status
18: Mass flow  (uncorrected)
    old 18: Mass flow rate [grams per minute Xe gas] (removed for t > 3520358622, 21 July 2015)
19: Pressure from 10k Torr baratron [Torr]
20: Pressure from 1k Torr baratron [Torr]
21: Cold cathode gauge [micro Torr]
22: LN mass (minus hooks and dewar tare weight) [lbs]
23: Xenon Bottle mass [kg]
24: Capacitance [pF]
25: T_max set point offset [K]
26: T_min set point offset [K]
27: HFE pressure
28: LN tare mass (hooks + dewar tare) [lbs]
29: Recovery LN valve after 30 Sept 2016 (RMS noise [mV] from 19 Mar 2015 to 30 Sept 2016)
30: mass flow valve closed
"""


import os
import sys
import datetime
import matplotlib
matplotlib.use('Agg') # batch mode
import matplotlib.pyplot as plt
import numpy as np
from optparse import OptionParser

def compare_isochoric(data_path, plot_dir, basename, temp_top, temp_mid,
    temp_bot, press_obs, press_obs2, time_hours):

    linewidth = 2
    temp, press = np.loadtxt(str(data_path)+"/vapor_pressure_data.txt",unpack=True, usecols = (0,1))
    plt.figure(1)
    plt.title("NIST Isochoric Xenon Data (9kg / 3.3L = 2.727 g/mL)")
    plt.xlabel("Temp [K]")
    plt.ylabel("Pressure [torr]")
    plt.grid(b=True)
    iso_data = plt.plot(temp, press)
    plt.setp(iso_data, color = 'c', linewidth = linewidth, label = 'Data')
    #legend = plt.legend(loc='best', shadow = False, fontsize='medium', ncol=2)
    plt.savefig(plot_dir+"50-Comp-Isochoric_"+basename+".jpeg")
    print "printed", plot_dir+"50-Comp-Isochoric_"+basename+".jpeg"
    plt.clf()
    
    # loop over baratron data, find corresponding pressure data from NIST
    calc_temp = []
    for p in press_obs:
        if np.min(press) < p < np.max(press): 
            index = (np.abs(press-p)).argmin() # find closest NIST value
            calc_temp.append(temp[index])
        else:
            calc_temp.append(161.4) # freezing 
    calc_temp2 = []
    for p in press_obs2:
        if np.min(press) < p < np.max(press): 
            index = (np.abs(press-p)).argmin() # find closest NIST value
            calc_temp2.append(temp[index])
        else:
            calc_temp2.append(161.4) # freezing 
            
    plt.figure(2)
    plt.title("Isochoric Temp: Baratrons vs Thermocouples", y=1.15)
    plt.xlabel("Time [hours]")
    plt.ylabel("Temp [K]")
    plt.grid(b=True)
    iso_top = plt.plot(time_hours, temp_top)
    iso_calc = plt.plot(time_hours, calc_temp)
    iso_mid = plt.plot(time_hours, temp_mid)
    iso_calc2 = plt.plot(time_hours, calc_temp2)
    iso_bot = plt.plot(time_hours, temp_bot)
    plt.setp(iso_calc, color = 'k', linewidth = linewidth, label = 'Baratron XP3 (%.1fK)' % calc_temp[-1])
    plt.setp(iso_calc2, color = 'c', linewidth = linewidth, label = 'Baratron XP5/7 (%.1fK)' % calc_temp2[-1])
    plt.setp(iso_top, color = 'r', linewidth = linewidth, label = 'Cell Top (%.1fK)' % temp_top[-1])
    plt.setp(iso_mid, color = 'b', linewidth = linewidth, label = 'Cell Mid (%.1fK)' % temp_mid[-1])
    plt.setp(iso_bot, color = 'g', linewidth = linewidth, label = 'Cell Bot (%.1fK)' % temp_bot[-1])

    # shrink plot height to create space for legend
    subplt = plt.subplot(111)
    box = subplt.get_position()
    subplt.set_position([box.x0, box.y0, box.width, box.height*0.9])
    legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=2)
    plt.savefig(plot_dir+"10-Temp-Isochoric_" + basename + ".jpeg")
    print "printed", plot_dir+"10-Temp-Isochoric_" + basename +".jpeg"
    plt.clf()
        
      
    # loop over baratron data, find corresponding pressure data from NIST
    # subtract 2K from cell temps
    calc_press_top = []
    for cell_temp in temp_top:
        #if np.min(temp) < cell_temp < np.max(temp): 
        index = (np.abs(temp-cell_temp+2)).argmin() # find closest NIST value
        calc_press_top.append(press[index])
    calc_press_mid = []
    for cell_temp in temp_mid:
        #if np.min(temp) < cell_temp < np.max(temp): 
        index = (np.abs(temp-cell_temp+2)).argmin() # find closest NIST value
        calc_press_mid.append(press[index])
    calc_press_bot = []
    for cell_temp in temp_bot:
        #if np.min(temp) < cell_temp < np.max(temp): 
        index = (np.abs(temp-cell_temp+2)).argmin() # find closest NIST value
        calc_press_bot.append(press[index])
           
    plt.figure(2)
    plt.title("Isochoric Pressure: Baratrons vs Thermocouples - 2K", y=1.15)
    plt.xlabel("Time [hours]")
    plt.ylabel("Pressure [Torr]")
    plt.grid(b=True)
    iso_top = plt.plot(time_hours, calc_press_top)
    iso_calc = plt.plot(time_hours, press_obs)
    iso_mid = plt.plot(time_hours, calc_press_mid)
    iso_calc2 = plt.plot(time_hours, press_obs2)
    iso_bot = plt.plot(time_hours, calc_press_bot)
    plt.setp(iso_calc, color = 'k', linewidth = linewidth, 
        label = 'Bar. XP3 (%i torr)' % press_obs[-1])
    plt.setp(iso_calc2, color = 'c', linewidth = linewidth, 
        label = 'Bar. XP5/7 (%i torr)' % press_obs2[-1])
    plt.setp(iso_top, color = 'r', linewidth = linewidth, 
        label = 'Cell Top (%i torr)' % (calc_press_top[-1]))
    plt.setp(iso_mid, color = 'b', linewidth = linewidth, 
        label = 'Cell Mid (%i torr)' % (calc_press_mid[-1]))
    plt.setp(iso_bot, color = 'g', linewidth = linewidth, 
        label = 'Cell Bot (%i torr)' % (calc_press_bot[-1]))

    # shrink plot height to create space for legend
    #plt.title(title, y=1.3)
    subplt = plt.subplot(111)
    box = subplt.get_position()
    subplt.set_position([box.x0, box.y0, box.width, box.height*0.9])
    legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=3)
    plt.savefig(plot_dir+"10-Press-Isochoric_" + basename + ".jpeg")
    print "printed", plot_dir+"10-Press-Isochoric_" + basename +".jpeg"
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
    T_Xe_bottle=None, T_max_set=None, T_min_set=None, T_omega=None,first_index=0, last_index=-1):

    """
    This function makes a temperature plot
    """

    linewidth=1
    start_time_hold = datetime.datetime.fromtimestamp(time_stamps[first_index]- 2082844800)
    end_time_hold = datetime.datetime.fromtimestamp(time_stamps[last_index]- 2082844800)
    
    start_time = start_time_hold.strftime("%m-%d-%y %I:%M %p")
    end_time = end_time_hold.strftime("%m-%d-%y %I:%M %p")

    plt.figure(1)
    plt.grid(b=True)

    # plot the lines
    # html color names can be used, as defined here:
    # http://www.w3schools.com/tags/ref_colornames.asp

    kelvin_offset = 273.15
    if TC0 and len(TC0) > 0:
        line1 = plt.plot(time_hours[first_index:last_index], TC0[first_index:last_index])
        plt.setp(line1, color = 'r', linewidth = linewidth, label = 'Cu Bot (%.1fK = %.1fC)' % (TC0[last_index], TC0[last_index]-kelvin_offset))

    if TC1 and len(TC1) > 0:
        line2 = plt.plot(time_hours[first_index:last_index], TC1[first_index:last_index])
        plt.setp(line2, color = 'b', linewidth = linewidth, label = 'Cell Top (%.1fK = %.1fC)' % (TC1[last_index], TC1[last_index]-kelvin_offset))

    if TC2 and len(TC2) > 0:
        line3 = plt.plot(time_hours[first_index:last_index],
        TC2[first_index:last_index])
        plt.setp(line3, color = 'g', linewidth = linewidth, label = 'Cell Mid (%.1fK = %.1fC)' % (TC2[last_index], TC2[last_index]-kelvin_offset))

    if TC3 and len(TC3) > 0:
        line4 = plt.plot(time_hours[first_index:last_index],
        TC3[first_index:last_index])
        plt.setp(line4, color = 'm', linewidth = linewidth, label = 'Cell Bot (%.1fK = %.1fC)' % (TC3[last_index], TC3[last_index]-kelvin_offset))

    if TC4 and len(TC4) > 0:
        line5 = plt.plot(time_hours[first_index:last_index],
        TC4[first_index:last_index])
        plt.setp(line5, color = 'k', linewidth = linewidth, label = 'Cu Top (%.1fK = %.1fC)' % (TC4[last_index], TC4[last_index]-kelvin_offset))

    if T_omega and len(T_omega) > 0:
        line5 = plt.plot(time_hours[first_index:last_index],
        T_omega[first_index:last_index])
        plt.setp(line5, color = 'c', linewidth = linewidth, label = 'Cu Top Omega (%.1fK = %.1fC)' % (T_omega[last_index], T_omega[last_index]-kelvin_offset))

    if T_ambient and len(T_ambient) > 0:
        line6 = plt.plot(time_hours[first_index:last_index],
        T_ambient[first_index:last_index])
        plt.setp(line6, color = 'c', linewidth = linewidth, label = 'Ambient (%.1fK = %.1fC)' % (T_ambient[last_index], T_ambient[last_index]-kelvin_offset))

    if T_LN_in and len(T_LN_in) > 0 and len(T_LN_in) == len(T_ambient):
        line7 = plt.plot(time_hours[first_index:last_index],
        T_LN_in[first_index:last_index])
        plt.setp(line7, color = 'purple', linewidth = linewidth, label = 'LN in (%.1fK = %.1fC)' % (T_LN_in[last_index], T_LN_in[last_index]-kelvin_offset))

    if T_LN_out and len(T_LN_out) > 0 and len(T_LN_out) == len(T_ambient):
        line8 = plt.plot(time_hours[first_index:last_index],
        T_LN_out[first_index:last_index])
        plt.setp(line8, color = 'royalblue', linewidth = linewidth, label = 'LN out (%.1fK = %.1fC)' % (T_LN_out[last_index], T_LN_out[last_index]-kelvin_offset))

    if T_Xe_bottle and len(T_Xe_bottle) > 0 and len(T_Xe_bottle) == len(T_ambient):
        line8 = plt.plot(time_hours[first_index:last_index],
        T_Xe_bottle[first_index:last_index])
        plt.setp(line8, color = 'magenta', linewidth = linewidth, label = 'Xe bottle (%.1fK = %.1fC)' % (T_Xe_bottle[last_index], T_Xe_bottle[last_index]-kelvin_offset))

        
    if TC15 and len(TC15) > 0:
        line11 = plt.plot(time_hours[first_index:last_index],
        TC15[first_index:last_index])
        plt.setp(line11, color = 'k', linewidth = linewidth, label = 'XV5 (%.1fK = %.1fC)' % (TC15[last_index], TC15[last_index]-kelvin_offset))
    
    if TC10 and len(TC10) > 0:
        line12 = plt.plot(time_hours[first_index:last_index],
        TC10[first_index:last_index])
        plt.setp(line12, color = 'g', linewidth = linewidth, label = 'Reg (%.1fK = %.1fC)' % (TC10[last_index], TC10[last_index]-kelvin_offset))

    # figure out what the plot limits are before we plot T_min & T_max:
    ymin, ymax = plt.gca().get_ylim()

    if T_max_set and len(T_max_set) > 0 and len(T_max_set) == len(TC0):
        line9 = plt.plot(time_hours[first_index:last_index],
        T_max_set[first_index:last_index])
        plt.setp(line9, color = 'r', linewidth = linewidth, label = 'T_max (%.1fK = %.1fC)' % (T_max_set[last_index], T_max_set[last_index]-kelvin_offset), ls = '--')

    if T_min_set and len(T_min_set) > 0 and len(T_min_set) == len(TC0):
        line10 = plt.plot(time_hours[first_index:last_index],
        T_min_set[first_index:last_index])
        plt.setp(line10, color = 'b', linewidth = linewidth, label = 'T_min (%.1fK = %.1fC)' % (T_min_set[last_index], T_min_set[last_index]-kelvin_offset), ls = '--')
    plt.xlabel('Time [hours] : '  + str(start_time) + "  -  " + str(end_time))
    plt.ylabel('Temperature [K]')

    plt.gca().set_ylim([ymin,ymax])

    # shrink plot height to create space for legend
    y = 1.22
    height = 0.87
    ncol = 2
    subplt = plt.subplot(111)
    if len(subplt.lines) > 8:
        ncol = 3
        y=1.3
        height=0.8
    plt.title(title, y=y)
    box = subplt.get_position()
    subplt.set_position([box.x0, box.y0, box.width, box.height*height])
    
    legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='small', ncol=ncol)
    plt.savefig(filename)
    print "printed %s" % filename
    plt.clf()
 

def main(
    filename,   # *.dat file to process
    start_time=None, # start time, in hours, other than first time in file
    stop_time=None,   # stop time, in hours, other than last time in file
    recovery_start=None, # recovery start time, in hours
    recovery_stop=None, # revovery stop time, in hours
    fill_start=None, # fill start time, in hours
    fill_stop=None, # fill stop time, in hours
):
    
    # options
    recent_time_span = 3600.0 # seconds to use for "recent" plots

    # print some status info 
    print "--> processing", filename
    if start_time != None:
        print "\t using start time of %.2f hours" % start_time
    if stop_time != None:
        print "\t using stop time of %.2f hours" % stop_time
    if recovery_start:
        print "\t recovery_start: %.2f hours" % recovery_start
    if recovery_stop:
        print "\t recovery_stop: %.2f hours" % recovery_stop
    if fill_start:
        print "\t fill_start: %.2f hours" % fill_start
    if fill_stop:
        print "\t fill_stop: %.2f hours" % fill_stop

    # choose an output directory for these files

    # construct a base name for plots, based on the input file name
    basename = os.path.basename(filename)
    basename = os.path.splitext(basename)[0]
    basename = basename.split("test_")[-1]


    # on the windows DAQ machine:
    directory = 'C://Users//xenon//Dropbox//labViewPlots/'
    if not os.path.isdir(directory):
        print "trying alexis' path..."
        #directory = '/Users/alexis/stanford-Dropbox/Dropbox/labViewPlots/'
        directory = '/Users/alexis/Downloads/%s/' % basename
        cmd = "mkdir -p %s" % directory
        import commands
        output = commands.getstatusoutput(cmd)
        if output[0]: print output[1]

        if not os.path.isdir(directory):
            print "trying mikes path.."
            directory = "C://Users//Michael//Documents//EXO//plots//"
            if not os.path.isdir(directory):
                directory = "."
    # offset, in grams/minute, for the mass flow meter (we can never exactly zero  the mass flow meter, so
    # we compensate for this)
    # compensation from test_20150609_173311.dat
    mass_flow_rate_offset = 0.0 
    #mass_flow_rate_offset = 30.0/60.0 + 12.0/16.0/60.0 
    #mass_flow_rate_offset = 326.33/897.16 

    
    # construct file names of plots
    filetype = 'jpeg'    
    mfpath = os.path.join(directory, "09-MassFlow_%s.%s" % (basename, filetype))
    vpath = os.path.join(directory, "03-ValveStates_%s.%s" % (basename, filetype))
    ppath = os.path.join(directory, "90-Pressure-10kTorr_%s.%s" % (basename, filetype))
    ppath2 = os.path.join(directory, "90-Pressure-1kTorr_%s.%s" % (basename, filetype))
    ppath3 = os.path.join(directory, "04-Pressure-Baratrons_%s.%s" % (basename, filetype))
    ppath4 = os.path.join(directory, "04-Pressure-Baratrons-Recent_%s.%s" % (basename, filetype))
    mfrpath = os.path.join(directory, "09-MassFlowRate_%s.%s" % (basename, filetype))
    ccgpath = os.path.join(directory, "91-CCGauge_%s.%s" % (basename, filetype))
    rccgpath = os.path.join(directory, "91-CCGauge-recent_%s.%s" % (basename, filetype))
    ccgpath_log = os.path.join(directory, "92-CCGauge-log_%s.%s" % (basename, filetype))
    rccgpath_log = os.path.join(directory, "92-CCGauge-log-recent_%s.%s" % (basename, filetype))
    lnpath = os.path.join(directory, "02-LN-Mass_%s.%s" % (basename, filetype))
    rlnpath = os.path.join(directory, "02-LN-Mass-recent_%s.%s" % (basename, filetype))
    bottle_mass_path = os.path.join(directory, "07-BottleMass_%s.%s" % (basename, filetype))
    capacitance_path = os.path.join(directory, "08-Capacitance_%s.%s" % (basename, filetype))
    hfep_path = os.path.join(directory, "06-HFE-Pressure_%s.%s" % (basename, filetype))
    dp_path = os.path.join(directory, "05-dP-Pressure_%s.%s" % (basename, filetype))

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
    T_omega = []
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
    recovery_LN_valve = []
    mass_flow_valve_closed = []

    # open the input file
    testfile = file(filename)

    # a column_offset to handle changes to LabView project
    column_offset = 0
    do_warning = True

    # keep track of max capacitance, for plotting purposes
    capacitance_max = 0.0

    # The mass_flow_rate value saved by LabView is the uncorrected (not scaled
    # by the dial) output of the mass flow meter, multiplied by 5.28. 
    # xenon correction factor: 1.32 [MKS 1479 manual page 50]
    # xenon gas density at 0 C: 5.894 g/L [MKS 1479 manual page 50]

    xenon_density = 5.89 # density of Xe gas [g/L at 0C]
    # xenon density at 300K: 5.3612 g / mL
    # correction for what alexis put in labview:
    xenon_density_ratio = xenon_density / 5.3612 # xenon density correction
    #print "xenon_density_ratio: ", xenon_density_ratio

    xenon_gas_correction_factor = 1.32
    argon_gas_correction_factor = 1.39
    argon_density = 1.782 # g/L
    #nitrogen_density = 1.25

    correction_factor = 1.0
    argon_factor = argon_density / xenon_density / xenon_gas_correction_factor * argon_gas_correction_factor

    # read values from input file:
    for (i_line, line) in enumerate(testfile):
        split_line = line.split()
        data = []
        try:
            time_stamp = float(split_line[0])
        except ValueError:
            print "====> problem with line %i, skipping rest of lines in file...  !!!" % i_line
            continue

        time_stamps.append(time_stamp)

        if i_line == 0:
            print "first time stamp:", time_stamp

            if time_stamp >= 3530657409:
                mass_flow_rate_offset = 493.0/16.0/60.0 # 500 grams in 16 hours

            if time_stamp >= 3539732526:
                mass_flow_rate_offset = 100.0/15.0/60.0 # 100 grams in 15 hours

            if time_stamp >= 3553816731.0:
                print "during/after 8th LXe"
                mass_flow_rate_offset = 170.0/15.0/60.0 # 100 grams in 15 hours

            print "mass_flow_rate_offset: [grams/minute]", mass_flow_rate_offset

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
            #print "tstamp:  ", time_stamp
            do_warning = False     

        full_mass_integral = 8760.0

        full_capacitance = 38.7
        empty_capacitance = 25

        full_bottle_mass = 94.83
        empty_bottle_mass = 86.0 # not really empty, but when the cell is full
        if time_stamp > 3532111093: # 6th LXe
            full_mass_integral = 8300
            empty_bottle_mass = full_bottle_mass - full_mass_integral/1e3
            full_capacitance = 38.2
            empty_capacitance = 24.5

        if time_stamp > 3540210950: # 7th LXe
            empty_capacitance = 24.46
            full_capacitance = 34.9
            empty_bottle_mass = 88.35 # not really empty, but when the cell is full
            full_mass_integral = 6437.6 # when cell is "full"


        if time_stamp >= 3553816731:
            empty_capacitance = 23.7
            full_capacitance = 34.0
            full_bottle_mass = 94.6
            empty_bottle_mass = full_bottle_mass - 6.5

        if time_stamp > 3562286046: # after new hanging bottles
            full_bottle_mass = 55.05
            empty_bottle_mass = full_bottle_mass - 8.75

        TC0.append(float(split_line[1]))
        TC1.append(float(split_line[2]))
        TC2.append(float(split_line[3]))
        TC3.append(float(split_line[4]))
        TC4.append(float(split_line[5]))
        T_ambient.append(float(split_line[6]))

        # when we access the omega controller over the internet, it sometimes
        # reads 0V to the NI readout device, which is ~ 120K. Check for this:
        omega_temp = float(split_line[14])
        # if we have a weird data point, try substituting the previous data
        # point:
        if omega_temp  < 150:
            try:
                omega_temp = T_omega[-1]
            except:
                pass
                
        T_omega.append(omega_temp)

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
        
        column_offset_2 = 0

        # this offset occurred when the Omega temperature controller replaced the mass flow rate (corrected by knob)
        # the output from AI0 was added to the block of temperature data and removed from the element-by-element data stream
        if time_stamp > 3520358622:
            column_offset_2 = 1       
        
        PLN.append(float(split_line[7+column_offset + column_offset_2]))
        SLN.append(float(split_line[8+column_offset + column_offset_2]))
        Heat.append(float(split_line[9+column_offset + column_offset_2]))

        xenon_mass_flow = float(split_line[10+column_offset+column_offset_2])*xenon_density_ratio
        # correct for offset in mass flow meter
        mass_flow_rate.append(xenon_mass_flow - mass_flow_rate_offset)
        #mass_flow_rate.append(xenon_mass_flow)

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
            if capacitance[-1] > capacitance_max: capacitance_max = capacitance[-1]
                
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

        try:
            recovery_LN_valve.append(float(split_line[22+column_offset]))
        except:
            pass

        try:
            mass_flow_valve_closed.append(float(split_line[23+column_offset]))
        except:
            pass

        # end loop over lines in input file

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
                #print "last_hour_to_consider", last_hour_to_consider
                #print "\t found last hour time stamp  at i = %i of %i, t= %.2f hours" % (i, len(time_stamps),  seconds_elapsed/3600.0)
                #print "\t last timestamp = %.2f, diff = %.2f" % (last_time_stamp, last_time_stamp - start_time_stamp_of_last_hour )
                #print "\t %i recent time stamps" % (len(time_stamps) - start_index_of_last_hour - 1)

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
    outfile = file("%s/99-log_%s.txt" % (directory, basename), 'w')
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

          if i_time >= first_index:
              mass += mass_flow_rate[i_time]*delta_time_minutes 
          Vol.append(mass)

          #if i_time % 100 == 0: # debugging
          #  print "i: %i | time [min]: %.1f | delta_time_minutes: %.2f | rate [g/min]:%.2e | mass %.2f g" % (
          #  i_time, minute_time, delta_time_minutes, mass_flow_rate[i_time], mass)

      print "done with integral"
      #print "integrated mass: %.2f g in %.2f minutes" % (mass, time_minutes[-1])

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
    filename = os.path.join(directory, "11-Temp_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'Temperature', time_hours, time_stamps, TC0,
    TC1, TC2, TC3, TC4, TC15, TC10, T_ambient, T_LN_in, T_LN_out, T_Xe_bottle,
    T_max_set, T_min_set, T_omega, first_index, last_index)

    # plot recent temperatures
    filename = os.path.join(directory, "11-Temp-recent_%s.%s" % (basename, filetype)) 
    plot_temperatures(filename, 'Recent Temperature', time_hours,
    time_stamps, TC0, TC1, TC2, TC3, TC4, TC15, TC10, T_ambient, T_LN_in,
    T_LN_out, T_Xe_bottle, T_max_set=T_max_set, T_min_set=T_min_set,
    T_omega=T_omega, first_index=start_index_of_last_hour, last_index=last_index)

    # plot LXe cell and Cu plate temperatures
    filename = os.path.join(directory, "01-Temp-cell_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'LXe cell and Cu plate temperature', time_hours,
    time_stamps, TC0, TC1, TC2, TC3, TC4, T_max_set=T_max_set, T_min_set=T_min_set,
    T_omega=T_omega, first_index=first_index, last_index=last_index)

    # plot LXe cell and Cu plate recent temperatures
    filename = os.path.join(directory, "01-Temp-cell-recent_%s.%s" % (basename, filetype))
    plot_temperatures(filename, 'Recent LXe cell and Cu plate temperature',
    time_hours,time_stamps, TC0, TC1, TC2, TC3, TC4, T_max_set=T_max_set,
    T_min_set=T_min_set, T_omega=T_omega, first_index=start_index_of_last_hour, last_index=last_index)
    
    #plot Ambient Temperature vs. xenon bottle mass
    #filename = os.path.join(directory, "Ambient_Only_%s.%s" % (basename, filetype))
    #plot_temp_vs_lmass(filename, 'Bottle Mass vs Ambient Temp', time_hours, time_stamps, T_ambient, bottle_mass)

    linewidth=1
   

    if len(Vol[first_index:last_index]) > 0:

      lxe_density = 2.978 # kg/L
      xenon_volume = Vol[last_index]/lxe_density/1e3
      plt.figure(3)
      plt.grid(b=True)
      title = 'Integrated mass flow\nxenon: %.1f g = %.2f L LXe' % (Vol[last_index], xenon_volume)
      title += '  (argon: %.1f g  = %.1f L gAr)' % (Vol[last_index]*argon_factor, Vol[last_index]/argon_density)
          
      plt.title(title)
      uline1 = plt.plot(time_hours[first_index:last_index],
      Vol[first_index:last_index])
      plt.setp(uline1, color = 'b', linewidth = linewidth)

      # add indicator line without changing plot y axes:
      ymin, ymax = plt.gca().get_ylim()
      plt.axhline(y=full_mass_integral, color='black', linestyle="--")
      plt.gca().set_ylim([ymin,ymax]) # reset axes to original

      # draw LXe fill box:
      if fill_start and fill_stop:
          plt.axvspan(fill_start, fill_stop, color='blue', alpha=0.3)

      # draw recovery box:
      if recovery_start and recovery_stop:
          plt.axvspan(recovery_start, recovery_stop, color='red', alpha=0.3)

      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Mass Flow [g of xenon]')
      plt.savefig(mfpath)
      print "printed %s" % mfpath
      plt.clf()
      
    plt.figure(4)
    plt.grid(b=True)
    plt.title('LN and Heaters')

    # moving average to plot duty cycle:
    n = 60 # number of data points to convolve (60 x ~10s = ~1min)
    duty_cycle = np.convolve(PLN, np.ones((n,))/n, mode='valid')

    # plot the lines:
    vline1 = plt.plot(time_hours[first_index:last_index], PLN[first_index:last_index])
    vline2 = plt.plot(time_hours[first_index:last_index], SLN[first_index:last_index])
    vline3 = plt.plot(time_hours[first_index:last_index], Heat[first_index:last_index])
    try:
        length = len(duty_cycle[first_index:last_index])
        vline4 = plt.plot(time_hours[last_index-length:last_index], duty_cycle[first_index:last_index])
        plt.setp(vline4, color = 'black', linewidth = 2.0, label = 'LN duty cycle: %.1f' % duty_cycle[-1])
    except:
        print "--> issue with plotting LN duty cycle"

    # plot the fill areas:
    plt.fill_between(time_hours[first_index:last_index],PLN[first_index:last_index], color='b')
    plt.fill_between(time_hours[first_index:last_index],Heat[first_index:last_index], color='r')
    plt.setp(vline1, color = 'b', linewidth = 2.0, label = 'LN valve: %i' % PLN[last_index])
    plt.setp(vline2, color = 'g', linewidth = 2.0, label = 'LN enabled: %i' % SLN[last_index])
    plt.setp(vline3, color = 'r', linewidth = 2.0, label = 'Heaters: %i' % Heat[last_index])
    plt.xlabel('Time [hours] %s' % time_string)
    plt.legend(loc = 'best', shadow = False, ncol=2)
    plt.ylim(0.0, 1.2)
    plt.savefig(vpath)
    print "printed %s" % vpath
    plt.clf()
    
    plt.figure(5)
    plt.grid(b=True)
    plt.title("XP3 Xenon system pressure (10k Torr Baratron) [Torr]: %.2f \n" % Pressure[-1])
    pline1 = plt.plot(time_hours[first_index:last_index],
    Pressure[first_index:last_index])
    plt.setp(pline1, color = 'b', linewidth = linewidth)

    # add red zone without changing plot y axes:
    ymin, ymax = plt.gca().get_ylim()
    plt.axhspan(ymin=760*2, ymax=ymax, color='red', alpha=0.5)
    plt.gca().set_ylim([ymin,ymax])

    # draw LXe fill box:
    if fill_start and fill_stop:
        plt.axvspan(fill_start, fill_stop, color='blue', alpha=0.3)

    # draw recovery box:
    if recovery_start and recovery_stop:
        plt.axvspan(recovery_start, recovery_stop, color='red', alpha=0.3)

    plt.xlabel('Time [hours] %s' % time_string)
    plt.ylabel('Pressure [Torr]')
    plt.savefig(ppath)
    print "printed %s" % ppath
    plt.clf()


    if len(Pressure2) > 0:
      # 2nd baratron plot:
      plt.figure(6)
      plt.grid(b=True)
      plt.title("XP5 Vacuum system pressure (1k Torr Baratron) [Torr]: %.2f \n" % Pressure2[-1])
      pline1 = plt.plot(time_hours[first_index:last_index], Pressure2[first_index:last_index])
      plt.setp(pline1, color = 'b', linewidth = linewidth)
      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Pressure [Torr]')
      plt.savefig(ppath2)
      print "printed %s" % ppath2
      plt.clf()
      
      
      # both baratrons plot:
      plt.grid(b=True)
      pline1 = plt.plot(time_hours[first_index:last_index], Pressure[first_index:last_index],
          label = "XP3 Xe system: %.1f Torr" % Pressure[last_index])
      pline2 = plt.plot(time_hours[first_index:last_index], Pressure2[first_index:last_index], 
          label = "XP5 Vac (XP7 Xe): %.1f Torr" % Pressure2[last_index])
      plt.setp(pline1, color = 'b', linewidth = linewidth)
      plt.setp(pline2, color = 'r', linewidth = linewidth)
      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Pressure [Torr]')


      # add red zone without changing plot y axes:
      ymin, ymax = plt.gca().get_ylim()
      plt.axhspan(ymin=760*2, ymax=ymax, color='red', alpha=0.5)
      plt.gca().set_ylim([ymin,ymax])

      # draw LXe fill box:
      if fill_start and fill_stop:
          plt.axvspan(fill_start, fill_stop, color='blue', alpha=0.3)

      # draw recovery box:
      if recovery_start and recovery_stop:
          plt.axvspan(recovery_start, recovery_stop, color='red', alpha=0.3)

      legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=2)
      plt.savefig(ppath3)
      print "printed %s" % ppath3
      plt.clf()
      
      # recent both baratrons plot:
      plt.grid(b=True)
      pline1 = plt.plot(recent_time, Pressure[start_index_of_last_hour:],
          label = "XP3 Xe system: %.1f Torr" % Pressure[last_index])
      pline2 = plt.plot(recent_time, Pressure2[start_index_of_last_hour:], 
          label = "XP5 Vac (XP7 Xe): %.1f Torr" % Pressure2[last_index])
      plt.setp(pline1, color = 'b', linewidth = linewidth)
      plt.setp(pline2, color = 'r', linewidth = linewidth)
      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Pressure [Torr]')

      # draw LXe fill box:
      if fill_start and fill_stop:
          plt.axvspan(fill_start, fill_stop, color='blue', alpha=0.3)

      # draw recovery box:
      if recovery_start and recovery_stop:
          plt.axvspan(recovery_start, recovery_stop, color='red', alpha=0.3)

      legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=2)
      plt.savefig(ppath4)
      print "printed %s" % ppath4
      plt.clf()

      
    if len(mass_flow_rate) > 0:
      plt.figure(7)
      plt.grid(b=True)
      mfline1 = plt.plot(time_hours[first_index:last_index],
      mass_flow_rate[first_index:last_index])
      plt.setp(mfline1, color = 'b', linewidth = linewidth, 
      label="Mass flow rate: %.2f g/min" % mass_flow_rate[last_index])
      ymin, ymax = plt.gca().get_ylim() # record y axis limits now
      label_val = mass_flow_valve_closed[last_index]
      mass_flow_valve_closed = np.array(mass_flow_valve_closed[first_index:last_index])
      mass_flow_valve_closed[ mass_flow_valve_closed==0 ] = np.nan #if valve state is closed, set to nan so point won't be drawn
      mfline1 = plt.plot(time_hours[first_index:last_index],np.array(mass_flow_rate[first_index:last_index])*mass_flow_valve_closed)
      plt.setp(mfline1, color = 'r', linewidth = linewidth*4, label="valve closed: %i" % label_val)
      plt.xlabel('Time [hours] %s' % time_string)
      plt.ylabel('Rate [grams/minute xenon gas]')

      # add red zone without changing plot y axes:
      plt.axhspan(ymin=ymin, ymax=-25.0, color='red', alpha=0.5)
      plt.gca().set_ylim([ymin,ymax])

      legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=2)

      plt.savefig(mfrpath)
      print "printed %s" % mfrpath
      plt.clf()

    if len(ccg_Pressure) > 0:

        try:
            outfile.write("XP4 (cold cathode gauge) pressure [Torr]: %.2e \n" % ccg_Pressure[-1])
            plt.figure(8)
            plt.grid(b=True)
            plt.title('XP4 Cold Cathode Pressure (last value: %.2e Torr)' % ccg_Pressure[-1])
            mfline1 = plt.plot(time_hours[first_index:last_index],
            ccg_Pressure[first_index:last_index])
            plt.setp(mfline1, color = 'b', linewidth = linewidth)
            plt.yscale('log')
            ymin, ymax = plt.gca().get_ylim()
            if ymax > 1e-3: ymax = 1e-3
            plt.gca().set_ylim([ymin,ymax]) # reset axes to original
            plt.xlabel('Time [hours] %s' % time_string)
            plt.ylabel('Pressure [Torr]')
            plt.savefig(ccgpath_log)
            print "printed %s" % ccgpath_log
            plt.clf()

            plt.figure(9)
            plt.grid(b=True)
            plt.title('Recent XP4 Cold Cathode Pressure (last value: %.2e Torr)' % ccg_Pressure[-1])
            mfline1 = plt.plot(recent_time, ccg_Pressure[start_index_of_last_hour:])
            plt.setp(mfline1, color = 'b', linewidth = linewidth)
            plt.yscale('log')
            ymin, ymax = plt.gca().get_ylim()
            if ymax > 1e-3: ymax = 1e-3
            plt.gca().set_ylim([ymin,ymax]) # reset axes to original
            plt.xlabel('Time [hours] %s' % time_string)
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
        plt.title('XP4 Cold Cathode Pressure (last value: %.2e Torr)' % (ccg_Pressure[-1]*1e-6))
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
        plt.title('Recent XP4 Cold Cathode Pressure (last value: %.2e Torr)' % (ccg_Pressure[-1]*1e-6))
        mfline1 = plt.plot(recent_time, ccg_Pressure[start_index_of_last_hour:])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('Pressure [10^-6 Torr]')
        plt.savefig(rccgpath)
        print "printed %s" % rccgpath
        plt.clf()
   
    if len(ln_mass) > 0:
        ln_density = 1.78 # lb / Liter

        fit = np.polyfit(recent_time, ln_mass[start_index_of_last_hour:], 1)
        fit_fn = np.poly1d(fit) 
        ln_slope_lbs_per_hour = fit[0] 
        ln_intercept_hours = fit[1]

        # ln_mass is total mass (dewar tare weight + hooks + LN)

        # old estimate:
        #old_amt_ln = ln_mass[start_index_of_last_hour] - ln_tare_mass[start_index_of_last_hour]
        new_amt_ln = ln_mass[last_index] - ln_tare_mass[last_index]
        #print "old amt ln [lb]:", old_amt_ln
        #print "new amt ln [lb]:", new_amt_ln
        #print "recent time span:", recent_time_span
        #ln_consumption_rate = (old_amt_ln - new_amt_ln) / (recent_time_span/3600.0)

        ln_consumption_rate = -ln_slope_lbs_per_hour
        ln_consumption_rate_info = "LN consumption rate [lb / hour]: %.2f" %  ln_consumption_rate
        #print ln_consumption_rate_info
        #print "LN consumption rate [L / hour]:", ln_consumption_rate/ln_density
        try: 
            ln_hours_remaining = (new_amt_ln)/ ln_consumption_rate
        except ZeroDivisionError:
            ln_hours_remaining = 999.99
            
        #print "LN time remaining: [hours]", ln_hours_remaining
        outfile.write("LN time remaining [hours]: %.2f \n" % ln_hours_remaining)
        outfile.write("LN consumption rate [lb/hour]: %.2f \n" % ln_consumption_rate)
        outfile.write("LN consumption rate [L/hour]: %.2f \n" % (ln_consumption_rate/ln_density))

        # estimate when LN dewar will be empty
        empty_time = datetime.datetime.fromtimestamp(
          time_stamps[last_index]- 2082844800 + ln_hours_remaining*3600.0)

        plt.grid(b=True)
        title="LN mass (should run out in %.1f hours, at %s) \n " % (
            ln_hours_remaining,
            empty_time.strftime("%m-%d-%y %I:%M%p"),
        )
        title += "LN mass = %.1f lb (%.1f  L), %.1f lb/hr (%.1f L/hr) in past hour" % ( 
            new_amt_ln,
            new_amt_ln/ln_density,
            ln_consumption_rate,
            ln_consumption_rate/ln_density,
        )
        plt.title(title, y=1.1)
        ln_line = plt.plot(time_hours[first_index:last_index],
            ln_mass[first_index:last_index], 
            label = "Total mass: %.1f lb" % (new_amt_ln + ln_tare_mass[last_index]) )
        ln_tare_line = plt.plot(time_hours[first_index:last_index],
            ln_tare_mass[first_index:last_index], 
            label = "Tare (dewar + hooks): %.1f lb" % ln_tare_mass[last_index])
        plt.setp(ln_line, color = 'b', linewidth = linewidth)
        plt.setp(ln_tare_line, color = 'red', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('total mass = LN mass + tare weight [lb]')

        # shrink plot height to create space for legend
        #plt.title(title, y=1.3)
        subplt = plt.subplot(111)
        box = subplt.get_position()
        subplt.set_position([box.x0, box.y0, box.width, box.height*0.9])
        legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=2)
        plt.savefig(lnpath)
        print "printed %s" % lnpath
        plt.clf()
        outfile.write("LN total mass [lb]: %.3f \n" % ln_mass[-1])
        outfile.write("LN tare mass [lb]: %.3f \n" % ln_tare_mass[-1])
        outfile.write("LN mass [lb]: %.3f \n" % (ln_mass[-1] - ln_tare_mass[-1])) 


        plt.grid(b=True)
        title="LN mass (should run out in %.1f hours, at %s) \n " % (
            ln_hours_remaining,
            empty_time.strftime("%m-%d-%y %I:%M%p"),
        )
        title += "LN mass = %.1f lb (%.1f  L), %.1f lb/hr (%.1f L/hr) in past hour" % ( 
            new_amt_ln,
            new_amt_ln/ln_density,
            ln_consumption_rate,
            ln_consumption_rate/ln_density,
        )
        plt.title(title, y=1.1)
        ln_line = plt.plot( recent_time,
            ln_mass[start_index_of_last_hour:], 
            label = "Total mass: %.1f lb" % (new_amt_ln + ln_tare_mass[last_index]) )
        #ln_tare_line = plt.plot( recent_time,
        #    ln_tare_mass[start_index_of_last_hour:], 
        #    label = "Tare (dewar + hooks): %.1f lb" % ln_tare_mass[last_index])
        fit_line = plt.plot(recent_time, fit_fn(recent_time), '--k', label="fit to past hour")
        plt.setp(ln_line, color = 'b', linewidth = linewidth)
        plt.setp(ln_tare_line, color = 'red', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('total mass = LN mass + tare weight [lb]')

        # shrink plot height to create space for legend
        #plt.title(title, y=1.3)
        subplt = plt.subplot(111)
        box = subplt.get_position()
        subplt.set_position([box.x0, box.y0, box.width, box.height*0.9])
        legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=2)
        plt.savefig(rlnpath)
        print "printed %s" % rlnpath
        plt.clf()
        outfile.write("LN total mass [lb]: %.3f \n" % ln_mass[-1])
        outfile.write("LN tare mass [lb]: %.3f \n" % ln_tare_mass[-1])
        outfile.write("LN mass [lb]: %.3f \n" % (ln_mass[-1] - ln_tare_mass[-1])) 



    if len(bottle_mass) > 0:
        plt.figure(13)
        plt.grid(b=True)
        mfline1 = plt.plot(time_hours[first_index:last_index], bottle_mass[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth, 
        label="Xe bottle mass: %.2f kg (%.1f kg in cell)" % (bottle_mass[-1], full_bottle_mass - bottle_mass[last_index]))

        ymin, ymax = plt.gca().get_ylim() # record y axes now

        label_val = recovery_LN_valve[-1] # store this valuve before we do anything else
        recovery_LN_valve = np.array(recovery_LN_valve[first_index:last_index])
        recovery_LN_valve[recovery_LN_valve==0 ] = np.nan #if valve state is closed, set to nan so point won't be drawn
        mfline1 = plt.plot(time_hours[first_index:last_index], recovery_LN_valve*np.array(bottle_mass[first_index:last_index]))
        plt.setp(mfline1, color = 'r', linewidth = linewidth*4, 
        label="recovery LN open: %i" % label_val)

        # add indicator lines without changing plot y axes:
        plt.axhline(y=full_bottle_mass, color='black', linestyle="--")
        plt.axhline(y=empty_bottle_mass, color='black', linestyle="--")
        plt.gca().set_ylim([ymin,ymax]) # reset axes to original

        # draw LXe fill box:
        if fill_start and fill_stop:
            plt.axvspan(fill_start, fill_stop, color='blue', alpha=0.3)

        # draw recovery box:
        if recovery_start and recovery_stop:
            plt.axvspan(recovery_start, recovery_stop, color='red', alpha=0.3)

        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('Mass [kg]')

        legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow = False, fontsize='medium', ncol=2)


        plt.savefig(bottle_mass_path)
        print "printed %s" % bottle_mass_path
        plt.clf()
        outfile.write("Xenon bottle mass [kg]: %.3f \n" % bottle_mass[-1])
        total_mass = 0.0
        for mass in bottle_mass[first_index:last_index]:
            total_mass += mass
        average_mass = total_mass / len(bottle_mass[first_index:last_index])
        #print "average xenon bottle mass in this time period: %.3f kg" % average_mass

    if len(capacitance) > 0:
        plt.figure(14)
        plt.grid(b=True)
        plt.title("Xenon cell capacitance [pF]: %.2f" % capacitance[last_index])
        mfline1 = plt.plot(time_hours[first_index:last_index],
            capacitance[first_index:last_index])

        # add indicator line without changing plot y axes:
        ymin, ymax = plt.gca().get_ylim()
        plt.axhline(y=full_capacitance, color='black', linestyle="--")
        plt.axhline(y=empty_capacitance, color='black', linestyle="--")
        if capacitance_max > 23.0: ymin = 23.0
        plt.gca().set_ylim([ymin,ymax]) # reset axes to original max, a reasonable min

        # draw LXe fill box:
        if fill_start and fill_stop:
            plt.axvspan(fill_start, fill_stop, color='blue', alpha=0.3)

        # draw recovery box:
        if recovery_start and recovery_stop:
            plt.axvspan(recovery_start, recovery_stop, color='red', alpha=0.3)

        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('Capacitance [pF]')
        plt.savefig(capacitance_path)
        print "printed %s" % capacitance_path
        plt.clf()
        outfile.write("Xenon cell capacitance [pF]: %.3f \n" % capacitance[-1])

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
            title = 'dP = Xenon XP3 - HFE HP2 = %.1f torr (keep |dP| < 760 torr)' % (dP[last_index]) 
            plt.title(title)
            dP_line = plt.plot(time_hours[first_index:last_index], dP[first_index:last_index])

            # add red zone without changing y axes:
            ymin, ymax = plt.gca().get_ylim()
            plt.axhspan(ymin=760, ymax=ymax, color='red', alpha=0.5)
            plt.axhspan(ymin=ymin, ymax=-1000, color='red', alpha=0.5)
            plt.gca().set_ylim([ymin,ymax])

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


    compare_isochoric(os.path.dirname(os.path.realpath(sys.argv[0])), directory,
    basename, TC1[first_index:last_index], TC2[first_index:last_index],
    TC3[first_index:last_index], Pressure[first_index:last_index],
    Pressure2[first_index:last_index], time_hours[first_index:last_index])
    
    outfile.write("Xenon mass in cell (integrated mass flow) [g]: %.4f \n" % mass)
    outfile.write("XP5 Vacuum system pressure (1k Torr Baratron) [Torr]: %.2f \n" % Pressure2[-1])
    outfile.write("XP3 Xenon system pressure (10k Torr Baratron) [Torr]: %.2f \n" % Pressure[-1])
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
    parser.add_option("--recovery-start",dest="recovery_start",type="float",default=None,
        help="recovery start time, in hours, for plots (None by default)")
    parser.add_option("--recovery-stop",dest="recovery_stop",type="float",default=None,
        help="recovery stop time, in hours, for plots (None by default)")
    parser.add_option("--fill-start",dest="fill_start",type="float",default=None,
        help="fill start time, in hours, for plots (None by default)")
    parser.add_option("--fill-stop",dest="fill_stop",type="float",default=None,
        help="fill stop time, in hours, for plots (None by default)")
    options,args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        parser.error("==> Wrong number of arguments!")

    for filename in args:
        main(
            filename=filename, 
            start_time=options.start, 
            stop_time=options.stop, 
            recovery_start=options.recovery_start,
            recovery_stop=options.recovery_stop,
            fill_start=options.fill_start,
            fill_stop=options.fill_stop,
        )
        


