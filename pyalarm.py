"""
The environment variable LXEPASS should be set to the password for the gmail
account. 

This script sends email if one of these conditions is met: 
* Unable to ping IP address of Omega LN controller (power may be out)
* any temperate in the HFE dewar (on cell or Cu plate) is above threshold
* dP is above threshold
* LN mass is below threshold
* LN is predicted to last less than a minimum time
* Dropbox is not updating (this means we can't monitor the system)

Modified from Brian Mong's monitoring of EXO-200. 
05 May 2016
"""

import os
import sys
import time
import argparse
import datetime
import commands
import smtplib

# options -- monitoring thresholds:
temperature_threshold = 168.0 # LXe & Cu operating threshold, K
dp_threshold = 400.0 # xenon - HFE, torr
ln_mass_threshold = 70.0 # lbs of LN needed
ln_hours_left_threshold = 1.0 # at least 1 hour of LN must remain! 
lookback_time_minutes = 6.0 # minutes
sleep_seconds = 60*5 # sleep for this many seconds between tests

def print_warning(warning):
    print "WARNING:", warning

def load_gmail_info():
    gmail_user = "lxe.readout@gmail.com"
    gmail_pwd = os.environ["LXEPASS"]
    return gmail_user, gmail_pwd

class LXeMonitoring:

    def __init__(self):

        #define users here:
        self.users = {
            'alexis':[
                'schubert.alexis@gmail.com', 
                'agschube@gmail.com',
                '2064121866@tmomail.net', # cell phone
            ],
        }

    def main(self, do_debug, do_test, lxe):

        self.do_test = do_test
        self.do_debug = do_debug
        self.lxe = lxe

        if self.lxe:
            print 'monitoring for LXe'
        else:
            print '===> WARNING: LXe is set to false!'
            print '\t LN mass, Cu & cell temps, will *NOT* be monitored'
        

        if self.do_test:
            # change thresholds so all alarms will trigger:
            temperature_threshold = 0.0
            dp_threshold = -1e5
            ln_mass_threshold = -100
            ln_hours_left_threshold = -100
            lookback_time_minutes = -1.0
            self.do_debug = True
            self.lxe = True

        if self.do_test:
            print "===> this is a test... "

        if self.do_debug:
            print "--> DEBUGGING"

        # check once to be sure this script is working ok
        self.self_checks() 

        # perform other checks in infinite loop!
        while True:

            now = datetime.datetime.now()
            print '==> starting test loop', now

            self.do_ping() # ping the Omega LN controller
            self.check_dropbox_data()

            if self.do_test:
                print "====> testing is done"
                break

            print "sleeping for %i seconds" % sleep_seconds
            time.sleep(sleep_seconds) # sleep for sleep_seconds


    def self_checks(self):
        """ 
        before trying anything, test that we can:
        * send a single test message
        * loop over users and addresses
        """

        print "--> checking that mail info exists:"
        load_gmail_info()
        print "\t ok"

        # print list of active users & addresses to be sure we can loop over them:
        print "--> users and addresses:"
        for user, addresses  in self.users.items():
            print "\t%s:" % user
            for address in addresses:
                print "\t\t", address


    def send_messages(self, msg, users):
        """ loop over all addresses for users and email message"""
        print "--> sending mail..."
        print('\a')
        print "\tmessage:", msg
        for user, addresses  in self.users.items():
            print "\tuser: %s:" % user
            for address in addresses:
                print "\t\t", address
                self.sendmail(msg, address)

    def do_ping(self, timeout=3):
        """ 
        ping the Omega LN controller to test for power outage 
        ping options:
          -o exit after 1st success
          -t exit after timeout of specified number of seconds
        """

        print "--> pinging Omega LN controller"
        cmd = "ping -o -t %i 171.64.56.58" % timeout
        output = commands.getstatusoutput(cmd)
        if self.do_debug: 
            print "\t", cmd
            print output[1]
        if output[0] != 0 or self.do_test:
            message = "Power outage? Cannot communicate with Omega LN controller \n"
            message += "command: %s \n" % cmd
            message += "output: \n"
            message += "%s \n" % output[0]
            message += output[1]

            print_warning(message)
            self.send_messages(message, self.users)
        else:
            print "\t success"


    def get_dropbox_data(self):
        """ download text file summary from dropbox currentPlots, parse for info """
        print "--> getting log file from dropbox:"
        
        file_name = "99-log.txt" # dropbox log file

        # remove old log file 
        # -f: don't complain if file doesn't exist
        cmd = 'rm %s' % file_name
        output = commands.getstatusoutput(cmd)
        if output[0] != 0 or self.do_debug:
            print "-- removing old file"
            print cmd
            print output[1]
 
        cmd = 'curl -L -o 99-log.txt https://www.dropbox.com/sh/an4du1pzdnl4e5z/AADd6Xcdi78WinEMHz3XGEO1a/%s' % file_name
        output = commands.getstatusoutput(cmd)
        if output[0] != 0 or self.do_debug:
            print "--> trying to download log file from dropbox:"
            print cmd
            print output[1]
        else:
            print "\t success"

        data = {}

        print "--> parsing file..."
        # open the file and read it:
        log_file = file(file_name)
        for line in log_file:

            if 'dP' in line:
                dP_torr = float(line.split(":")[1])
                data['dP_torr'] = dP_torr
                if self.do_debug: print "\t", line.split(":")[0] + ":",  dP_torr

            if 'LN mass' in line:
                ln_mass_lbs = float(line.split(':')[1])
                data['ln_mass_lbs'] = ln_mass_lbs
                if self.do_debug: print "\t", line.split(":")[0] + ":",  ln_mass_lbs

            if 'Last LabView time stamp' in line:
                LV_time= (':').join(line.split(':')[1:])
                LV_time = (" ").join(LV_time.split()) # get rid of trailing characters
                data['LV_time'] = LV_time
                if self.do_debug: print "\t", line.split(":")[0] + ":", LV_time

            if 'LN time remaining' in line:
                ln_hours_left = float(line.split(':')[1])
                data['ln_hours_left'] = float(line.split(':')[1])
                if self.do_debug: print "\t", line.split(":")[0] + ":", ln_hours_left

            if 'Cu top [K]' in line:
                cu_top = float(line.split(':')[1].split()[0])
                data['cu_top'] = cu_top
                if self.do_debug: print "\t", line.split(":")[0] + ":", cu_top

            if 'Cu bot [K]' in line:
                cu_bot = float(line.split(':')[1])
                data['cu_bot'] = cu_bot
                if self.do_debug: print "\t", line.split(":")[0] + ":", cu_bot

            if 'Cell top [K]' in line:
                cell_top = float(line.split(':')[1])
                data['cell_top'] = cell_top
                if self.do_debug: print "\t", line.split(":")[0] + ":", cell_top

            if 'Cell bot [K]' in line:
                cell_bot = float(line.split(':')[1])
                data['cell_bot'] = cell_bot
                if self.do_debug: print "\t", line.split(":")[0] + ":", cell_bot

            if 'Cell mid [K]' in line:
                cell_mid = float(line.split(':')[1])
                data['cell_mid'] = cell_mid
                if self.do_debug: print "\t", line.split(":")[0] + ":", cell_mid

        print "\t done"
        return data


    def check_dropbox_data(self):
        """ check dropbox data against thresholds """
        data = self.get_dropbox_data()
        print "--> checking dropbox data:"

        if self.do_debug: 
            print "--> dropbox data:"
            for key, value in data.items():
                print "\t", key, value

        messages = []

        if data['dP_torr'] > dp_threshold:
            message = "dP = %.1f torr" % data['dP_torr']
            messages.append(message)
            print_warning(message)

        if self.lxe:

            if data['ln_hours_left'] < ln_hours_left_threshold:
                message = "hours of LN remaining: %.2f" % data['ln_hours_left']
                messages.append(message)
                print_warning(message)

            if data['ln_mass_lbs'] < ln_mass_threshold:
                message = "hours of LN remaining: %.2f" % data['ln_mass_lbs']
                messages.append(message)
                print_warning(message)

            # check temps in HFE dewar:
            temps = ['cu_top', 'cu_bot', 'cell_top', 'cell_mid', 'cell_bot']
            for key in temps:
                if data[key] > temperature_threshold:
                    message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], temperature_threshold)
                    messages.append(message)
                    print_warning(message)

        else:
            print "Warning: LXe is set to false -- not checking cell temps or LN remaining"

        # check how old the labview time stamp is:
        LV_time = data['LV_time']
        LV_time =  datetime.datetime.strptime(LV_time,"%Y-%m-%d %H:%M:%S.%f")
        if self.do_debug: print "LV_time", LV_time
        now  = datetime.datetime.now()
        time_elapsed =  now - LV_time
        if self.do_debug: print "time_elapsed", time_elapsed
        if LV_time < now - datetime.timedelta(minutes=lookback_time_minutes):
            time_elapsed =  now - LV_time
            message = "time elapsed since last LV time stamp: %s" %  time_elapsed
            print_warning(message)
            messages.append(message)

        if len(messages) > 0:
            print "%i warnings" % len(messages)
            message = "\n".join(messages)
            self.send_messages(message, self.users)

        print "\t done"


    def sendmail(self,message,address):
        """ send a message to a user """
        print "trying to send mail..."
        gmail_user, gmail_pwd = load_gmail_info()
        smtpserver = smtplib.SMTP("smtp.gmail.com",587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo
        smtpserver.login(gmail_user, gmail_pwd)
        subject = "Stanford LXe System Alarm!"
        if self.do_test: subject = "TEST of " + subject
        header = 'To:' + address + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:%s \n' % subject
        print header
        info = "time: %s  \n" % datetime.datetime.now()
        info += "user: %s \n" % os.getlogin()
        msg = header + '\n%s\n%s\n' % (info, message)
        smtpserver.sendmail(gmail_user, address, msg)
        print 'done!'
        smtpserver.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--lxe', action='store_true')
    args = parser.parse_args()

    monitor = LXeMonitoring()
    monitor.main(do_debug=args.debug, do_test=args.test, lxe=args.lxe)

