import os
import sys
import datetime
import matplotlib.pyplot as plt
import numpy as np
from optparse import OptionParser

def compare_isochoric(data_path, plot_dir, basename, temp_top, temp_mid, temp_bot, press_obs, time_hours):
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
    plt.savefig(plot_dir+"Nist-Isochoric_"+basename+".jpeg")
    print "printed", plot_dir+"Comp-Isochoric_"+basename+".jpeg"
    plt.clf()
    
    calc_temp = []
    for p in press_obs:
        if np.min(press) < p < np.max(press): 
            index = (np.abs(press-p)).argmin()
            calc_temp.append(temp[index])
        else:
            calc_temp.append(161.4) # freezing 
            
    plt.figure(2)
    plt.title("Isochoric Temp Cell vs Thermocouples")
    plt.xlabel("Time [hours]")
    plt.ylabel("Temp [K]")
    plt.grid(b=True)
    iso_calc = plt.plot(time_hours, calc_temp)
    iso_top = plt.plot(time_hours, temp_top)
    iso_mid = plt.plot(time_hours, temp_mid)
    iso_bot = plt.plot(time_hours, temp_bot)
    plt.setp(iso_calc, color = 'k', linewidth = linewidth, label = 'Baratron (%.1fK)' % calc_temp[-1])
    plt.setp(iso_top, color = 'r', linewidth = linewidth, label = 'Cell Top (%.1fK)' % temp_top[-1])
    plt.setp(iso_mid, color = 'b', linewidth = linewidth, label = 'Cell Mid (%.1fK)' % temp_mid[-1])
    plt.setp(iso_bot, color = 'g', linewidth = linewidth, label = 'Cell Bot (%.1fK)' % temp_bot[-1])
    legend = plt.legend(loc='best', shadow = False, fontsize='medium', ncol=2)
    plt.savefig(plot_dir+"Temp-Isochoric_" + basename + ".jpeg")
    print "printed", plot_dir+"Temp-Isochoric_" + basename +".jpeg"
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
    
    start_time = start_time_hold.strftime("%m-%d-%y %I:%M %p")
    end_time = end_time_hold.strftime("%m-%d-%y %I:%M %p")

    plt.figure(1)
    plt.title(title)
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

    if T_max_set and len(T_max_set) > 0 and len(T_max_set) == len(T_ambient):
        line9 = plt.plot(time_hours[first_index:last_index],
        T_max_set[first_index:last_index])
        plt.setp(line9, color = 'r', linewidth = linewidth, label = 'T_max (%.1fK = %.1fC)' % (T_max_set[last_index], T_max_set[last_index]-kelvin_offset), ls = '--')

    if T_min_set and len(T_min_set) > 0 and len(T_min_set) == len(T_ambient):
        line10 = plt.plot(time_hours[first_index:last_index],
        T_min_set[first_index:last_index])
        plt.setp(line10, color = 'b', linewidth = linewidth, label = 'T_min (%.1fK = %.1fC)' % (T_min_set[last_index], T_min_set[last_index]-kelvin_offset), ls = '--')
        
    if TC15 and len(TC15) > 0:
        line11 = plt.plot(time_hours[first_index:last_index],
        TC15[first_index:last_index])
        plt.setp(line11, color = 'k', linewidth = linewidth, label = 'XV5 (%.1fK = %.1fC)' % (TC15[last_index], TC15[last_index]-kelvin_offset))
    
    if TC10 and len(TC10) > 0:
        line12 = plt.plot(time_hours[first_index:last_index],
        TC10[first_index:last_index])
        plt.setp(line12, color = 'g', linewidth = linewidth, label = 'Reg (%.1fK = %.1fC)' % (TC10[last_index], TC10[last_index]-kelvin_offset))

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

    # offset, in grams/minute, for the mass flow meter (we can never exactly zero  the mass flow meter, so
    # we compensate for this)
    # compensation from test_20150609_173311.dat
    mass_flow_rate_offset = 326.33/897.16 
    print "mass_flow_rate_offset", mass_flow_rate_offset

    
    # construct file names of plots
    filetype = 'jpeg'    
    
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
    rms_noise = []

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
            rms_noise.append(float(split_line[22+column_offset]))
        except:
            pass

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
      print "integrated mass: %.2f g in %.2f minutes" % (mass, time_minutes[-1])

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
    
    print "--> starting plot..."

    #plot just Ambient Temperature
    #filename = os.path.join(directory, "Ambient_Only_%s.%s" % (basename, filetype))
    #plot_temp_vs_lmass(filename, 'Bottle Mass vs Ambient Temp', time_hours, time_stamps, T_ambient, bottle_mass)

    linewidth=1

# find initial mass
    for last_index in range(len(time_hours)):
	if time_hours[last_index] > 2: break;
##    plt.figure(135)
##    plt.grid(b=True)
##    plt.title("Xenon bottle mass [kg]: %.2f \n" % bottle_mass[-1])
##    mfline1 = plt.plot(time_hours[:last_index],
##    bottle_mass[:last_index])
##    plt.setp(mfline1, color = 'b', linewidth = linewidth)
##    plt.xlabel('Time [h]')
##    plt.ylabel('Mass [kg]')
##    plt.show()
    initialmass = np.average(bottle_mass[:last_index])
    print "Initial mass = ", initialmass

# zoom in on mass plot
    bottle_mass_zoomin_path = os.path.join(directory, "BottleMass_zoomin_%s.%s" % (basename, filetype))
    for first_index in range(len(time_hours)):
	if time_hours[first_index] > 2.7: break;
    for last_index in range(len(time_hours)):
	if time_hours[last_index] > 6.8: break;
    if len(bottle_mass) > 0:
        plt.figure(131)
        plt.grid(b=True)
        plt.title("Xenon bottle mass [kg]: %.2f \n" % bottle_mass[-1])
        mfline1 = plt.plot(time_hours[first_index:last_index],
        bottle_mass[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [h]')
        plt.ylabel('Mass [kg]')
        plt.savefig(bottle_mass_zoomin_path)
        print "printed %s" % bottle_mass_zoomin_path
        plt.clf()
        outfile.write("Xenon bottle mass [kg]: %.3f \n" % bottle_mass[-1])

# zoom in on capacitance plot
    capacitance_zoomin_path = os.path.join(directory, "Capacitance_zoomin_%s.%s" % (basename, filetype))
    if len(capacitance) > 0:
        plt.figure(132)
        plt.grid(b=True)
        plt.title("Xenon cell capacitance [pF]: %.2f \n" % capacitance[-1])
        mfline1 = plt.plot(time_hours[first_index:last_index],
        capacitance[first_index:last_index])
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Time [hours] %s' % time_string)
        plt.ylabel('Capacitance [pF]')
        plt.savefig(capacitance_zoomin_path)
        print "printed %s" % capacitance_zoomin_path
        plt.clf()
        outfile.write("Xenon cell capacitance [pF]: %.3f \n" % capacitance[-1])    

# bottle mass vs capacitance plot
    bottle_mass_vs_capacitance_path = os.path.join(directory, "BottleMass_vs_Capacitance_%s.%s" % (basename, filetype))
    if len(bottle_mass) > 0:
	capacitance1 = []
	mass1 = []
	for index in range(first_index,last_index):
	    if capacitance[index]>30 and initialmass - bottle_mass[index]>1:
		capacitance1.append(capacitance[index])
		mass1.append(initialmass - bottle_mass[index])
	plt.figure(133)
        plt.grid(b=True)
        plt.title("Xenon mass vs capacitance \n")
	mfline1 = plt.plot(mass1,capacitance1)
        plt.setp(mfline1, color = 'b', linewidth = linewidth)
        plt.xlabel('Mass [kg]')
        plt.ylabel('Capacitance [pF]')
        plt.savefig(bottle_mass_vs_capacitance_path)
        print "printed %s" % bottle_mass_vs_capacitance_path
        outfile.write("Xenon bottle mass [kg]: %.3f \n" % bottle_mass[-1])
##        # curve fitting
##        from scipy.optimize import curve_fit
##        def func(x,a,b,c): return a*np.exp(-b*x) + c
##        popt, pcov = curve_fit(func, mass1, capacitance1, p0=[8.5,0.35,39])
##        print popt
##        mass1_new = np.linspace(min(mass1),max(mass1),1000)
##        capacitance1_new = func(mass1_new,popt[0],popt[1],popt[2])
##        plt.plot(mass1_new,capacitance1_new,'r')
##        plt.clf()

# bottle mass vs mass flow plot
##    bottle_mass_vs_flow_path = os.path.join(directory, "BottleMass_vs_MassFlow_%s.%s" % (basename, filetype))
##    if len(bottle_mass) > 0:
##	massflow1 = []
##	mass1 = []
##	for index in range(first_index,last_index):
##	    if capacitance[index]>30:
##		massflow1.append(Vol[index])
##		mass1.append(initialmass - bottle_mass[index])
##	plt.figure(134)
##        plt.grid(b=True)
##        plt.title("Xenon mass vs mass flow \n")
##	mfline1 = plt.plot(massflow1,mass1)
##        plt.setp(mfline1, color = 'b', linewidth = linewidth)
##        plt.xlabel('Mass flow [g of Xenon]')
##        plt.ylabel('Mass [kg]')
##        plt.savefig(bottle_mass_vs_flow_path)
##        print "printed %s" % bottle_mass_vs_flow_path
##        outfile.write("Xenon bottle mass [kg]: %.3f \n" % bottle_mass[-1])
##        # curve fitting
##        def func(x,a,b): return a*x + b
##        popt, pcov = curve_fit(func, mass1, massflow1)
##        print popt
##        mass1_new = np.linspace(min(mass1),max(mass1),1000)
##        massflow1_new = func(mass1_new,popt[0],popt[1])
##        plt.plot(massflow1_new,mass1_new,'r')
##        plt.show()
##        plt.clf()

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
