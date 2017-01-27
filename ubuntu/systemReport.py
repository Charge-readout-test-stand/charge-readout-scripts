#!/usr/bin/env python

"""
This script is run by a cron job on the Ubuntu DAQ computer. 

There is a soft link to this script in the ubuntu DAQ Dropbox, 
/home/teststand/Dropbox/ubuntuDaq

Edit data_dir in main()

"""


import os
import sys
import time
import datetime
import commands
import matplotlib
matplotlib.use('Agg') # batch mode!
import matplotlib.pyplot as plt


def get_disk_space():
    """
    print info about remaining disk space
    """
    
    print "---> getting disk space info"
    # options
    max_lines = 1000 # limit length of file
    filename = "/home/teststand/Dropbox/ubuntuDaq/disk_space.txt"
    directory = os.path.dirname(filename)

    # calculate total/used/available disk space
    output = commands.getstatusoutput('df / | grep sda1')
    if output[0] != 0:
        print output[1]
        return
    total_space = float(output[1].split()[1])/1e6
    used_space = float(output[1].split()[2])/1e6
    available_space = float(output[1].split()[3])/1e6
    info = "space [GB]: total=%i | used=%i | available=%i" % (total_space, used_space, available_space)
    print "\t %s" % info

    # append recent info to file
    now = datetime.datetime.now()
    now_stamp = time.mktime(now.timetuple())
    log_file = open(filename,"a")
    log_file.write("%i %s \n" % (now_stamp, output[1]))

    # fill lists from file
    log_file = open(filename,"r")
    time_hours = []
    total_pts = []
    available_pts = []
    used_pts = []
    #print "lines in file"
    for i_line, line in enumerate(log_file):
        #print "\t %i %s" % (i_line, line)
        if i_line == 0: start_stamp = int(line.split()[0])
        time_hours.append((float(line.split()[0])- start_stamp)/60.0/60.0)
        total_pts.append(float(line.split()[2])/1e6)
        used_pts.append(float(line.split()[3])/1e6)
        available_pts.append(float(line.split()[4])/1e6)

    # if the file is too long, only keep the last max_lines lines
    if i_line > max_lines:
        print "\t ==> file too long! (%i > %i)" % (i_line, max_lines)
        temp_file = "%s/temp.out" % os.path.dirname(filename)
        output = commands.getstatusoutput("tail -n %i %s > %s; mv -f %s %s" % (max_lines, filename, temp_file, temp_file, filename))
        if output[0] != 0: print output[1]

    # plot data
    print "\t plotting %i points" % len(time_hours)
    plt.figure()
    plt.xlabel("Time [hours] %s to %s (%i data points)" % (
        datetime.datetime.fromtimestamp(start_stamp).strftime("%m-%d-%y %I:%M %p"), 
        now.strftime("%m-%d-%y %I:%M %p"), 
        len(time_hours),
    ))
    plt.ylabel("Disk space [GB]")

    total = plt.plot(time_hours, total_pts)
    plt.setp(total, color='b', label = "{:,.0f} GB total".format(total_space))

    available = plt.plot(time_hours, available_pts)
    plt.setp(available, color='g', label = "{:,.0f} GB free".format(available_space))

    used = plt.plot(time_hours, used_pts)
    plt.setp(used, color='r', label = "{:,.0f} GB used".format(used_space))

    plt.grid(b=True)
    #plt.legend(loc='best', shadow=False, ncol=3)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow=False, ncol=3)
    plt.savefig("%s/monitoring_plots/diskSpace.jpg" % directory)
    print "---> done with disk space info \n"



def get_data_files(data_dir):
    """
    print info about remaining disk space
    """

    # options
    filename = "/home/teststand/Dropbox/ubuntuDaq/data_dir.txt"
    directory = os.path.dirname(filename)
    max_lines = 1000

    #file_type = ".root"
    file_type = ".bin"

    print "---> getting data dir info from %s" % data_dir

    # append recent info to file
    output = commands.getstatusoutput("du %s" % data_dir)
    data_dir_size = int(output[1].split()[0])
    if output[0]:
        print output[1]

    #output = commands.getstatusoutput("ls -1 %s | grep .bin | wc -l" % data_dir)
    output = commands.getstatusoutput("ls -1 %s | grep %s | wc -l" % (data_dir, file_type))
    n_files = int(output[1])
    if output[0]:
        print output[1]

    now = datetime.datetime.now()
    now_stamp = time.mktime(now.timetuple())
    log_file = open(filename,"a")
    log_file.write("%i %i %i \n" % (now_stamp, n_files, data_dir_size))

    # fill lists from file
    log_file = open(filename,"r")
    time_hours = []
    n_files_pts = []
    data_dir_pts = []
    #print "lines in file"
    for i_line, line in enumerate(log_file):
        #print "\t %i %s" % (i_line, line)
        if i_line == 0: start_stamp = int(line.split()[0])
        time_hours.append((float(line.split()[0])- start_stamp)/60.0/60.0)

        n_files_pts.append(int(line.split()[1]))
        data_dir_pts.append(float(line.split()[2])/1e6)

    # if the file is too long, only keep the last max_lines lines
    if i_line > max_lines:
        print "\t ==> file too long! (%i > %i)" % (i_line, max_lines)
        temp_file = "%s/temp.out" % os.path.dirname(filename)
        output = commands.getstatusoutput("tail -n %i %s > %s; mv -f %s %s" % (max_lines, filename, temp_file, temp_file, filename))
        if output[0] != 0:
            print output[1]

    # plot data
    print "\t plotting %i points | %i %s files %.2f GB" % (len(time_hours), n_files_pts[-1], file_type, data_dir_pts[-1])
    plt.figure()

    plt.xlabel("Time [hours] %s to %s (%i data points)" % (
        datetime.datetime.fromtimestamp(start_stamp).strftime("%m-%d-%y %I:%M %p"), 
        now.strftime("%m-%d-%y %I:%M %p"), 
        len(time_hours),
    ))
    plt.ylabel("files in %s" % data_dir)

    total = plt.plot(time_hours, n_files_pts)
    plt.setp(total, color='b', label = "{:,} *{} files".format(n_files_pts[-1], file_type))

    pts = plt.plot(time_hours, data_dir_pts)
    plt.setp(pts, color='r', label = "{:,.1f} GB".format(data_dir_pts[-1]))

    plt.grid(b=True)
    #plt.legend(loc='best', shadow=False, ncol=3)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow=False, ncol=3)
    plt.savefig("%s/monitoring_plots/dataDir.jpg" % directory)
    print "---> done with data dir info \n"


def get_struck_temperature(data_dir):
    """
    print info about Struck temperature
    """
    print "---> getting temp info from", data_dir

    # options
    filename = "/home/teststand/Dropbox/ubuntuDaq/struck_temps.txt"
    directory = os.path.dirname(filename)
    max_lines = 1000000 # lines of sisreadthread.log to grep

    cmd = "tail -n %i %s/sisreadthread.log | grep Temperature > %s" % (max_lines, data_dir, filename)
    #print cmd
    output = commands.getstatusoutput(cmd)
    if output[0]:
        print output[1]

    now = datetime.datetime.now()
    now_stamp = time.mktime(now.timetuple())
    log_file = open(filename, "r")

    # fill lists from file
    temperatures = []
    runs = []
    #print "lines in file"
    for i_line, line in enumerate(log_file):
        #print "\t %i %s" % (i_line, line)
        try:
            temperature = float(line.split()[2])
            temperatures.append(temperature)
            runs.append(i_line)
        except:
            print "\t %i %s" % (i_line, line)
            continue

    # plot data
    plt.figure()

    plt.xlabel("Data point (%i data points)" % (
        len(temperatures),
    ))
    #plt.ylabel("Temperature [C] \n(from sisreadthread.log in %s)" % data_dir)
    plt.ylabel("Temperature [C] (from sisreadthread.log)")

    now = datetime.datetime.now()
    label = "latest temperature: %.1f C at %s" % (
        temperatures[-1],
        now.strftime("%m-%d-%y %I:%M %p"), 
    )

    pts = plt.plot(runs, temperatures)
    plt.setp(pts, color='r', label=label)

    plt.grid(b=True)
    #plt.legend(loc='best', shadow=False, ncol=3)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), shadow=False, ncol=3)
    plt.savefig("%s/monitoring_plots/struckTemperatures.jpg" % directory)

    #plt.yscale('log')
    #plt.savefig("%s/monitoring_plots/struckTemperatures_log.jpg" % directory)

    ymin, ymax = plt.gca().get_ylim()
    if ymax > 60.0: ymax = 60.0
    plt.gca().set_ylim([ymin,ymax]) # reset axes to original
    plt.savefig("%s/monitoring_plots/struckTemperatures_zoom.jpg" % directory)

    print "---> done with temperature info \n"




def main():

    #-------------------------------------------------------------------------------
    # options
    #-------------------------------------------------------------------------------

    #data_dir = os.getenv("DATADIR") # doesn't work since cron job doesn't have this env var set
    #data_dir = "/home/teststand/2016_08_13_pmt_testing/"
    #data_dir = "/home/teststand/2016_08_14_PMTDuringCooldown/"
    #data_dir = "/home/teststand/2016_08_15_8th_LXe/tier0/"
    #data_dir = "/home/teststand/2016_08_15_8th_LXe_overnight/tier3/"
    #data_dir = "/home/teststand/2016_09_19_overnight/tier0/"
    #data_dir = "/home/teststand/2017_01_10_10th_LXe/tier0/"
    data_dir = "/home/teststand/11th_LXe/2017_01_24_tests/tier0/"

    #-------------------------------------------------------------------------------

    print "logging info..."

    directory = '/home/teststand/Dropbox/ubuntuDaq/'
    cmd = 'mkdir -p %s/monitoring_plots' % directory
    output = commands.getstatusoutput(cmd)
    if output[0] != 0:
        print cmd
        print output[1]
    print "\t data_dir =", data_dir
    if data_dir is None:
        return

    # run all of the functions:
    get_disk_space()
    get_data_files(data_dir)
    get_struck_temperature(data_dir)


if __name__ == "__main__":
    main()


