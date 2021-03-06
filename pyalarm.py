"""
The environment variable LXEPASS should be set to the password for the gmail
account. 

** run this script with "python -u" to pipe output to a log file. Usually
something like this, in a screen session:
  python -u pyalarm.py >& py_log.out

This script sends email if one of these conditions is met: 
* Unable to ping IP address of Omega LN controller (power may be out)
* any temperate in the HFE dewar (on cell or Cu plate) is above threshold
* dP is above threshold
* LN mass is below threshold
* LN is predicted to last less than a minimum time
* Dropbox is not updating (this means we can't monitor the system)

To do: FIXME
* add absolute pressure alarm
* skipping LN hours left for now, it gives false alarms for a long time after
  dewar changes
* 12 May 2016 -- script hung while trying to send mail, I think internet was
  down. Printed text:

        --> sending mail...

           user: alexis:
            schubert.alexis@gmail.com
        trying to send mail...

Modified from Brian Mong's monitoring of EXO-200. 
05 May 2016
"""

import os
import sys
import time
import argparse
import datetime
import smtplib

PYTHON_VERSION = sys.version.split()[0][0]

if PYTHON_VERSION == '2':
    print('USING PYTHON2')
    import commands as process_provider
else:
    print('USING PYTHON3')
    import subprocess as process_provider

# options -- monitoring thresholds:
temperature_threshold = 220#300 # LXe & Cu operating threshold, K
dp_threshold = 50.0 # xenon - HFE, torr
ln_mass_threshold = 10#-10.0 # lbs of LN needed
ln_hours_left_threshold = -100000.0 # at least 1 hour of LN must remain! 
lookback_time_minutes = 12.0 # LabView plots shouldn't be older than this, minutes
sleep_seconds = 60*5 # sleep for this many seconds between tests
heartbeat_interval_hours = 1.0
cu_plate_in_threshold = 220#+3.0 # K, this is most sensitive to failures of cooling

is_fill = True
#temperature_threshold = 265.0
ln_in_thresh = 300.0#140.0
#ln_in_thresh = 220.0
#####################################
# SETTINGS FOR THE LONG TPC
#####################################
ln_in_thresh = 180 # K
pressure_1k_threshold = 970. # torr
pressure_10k_threshold = 915. # torr
pressure_1k_low_threshold = 830. # torr
cell_bot_temp_threshold = 167 # K
cell_mid_temp_threshold = 167 # K
cell_top_temp_threshold = 170.5 # K
temp_xe1_recirc_threshold = 300 # K
temp_xe2_recirc_threshold = 300 # K






def print_warning(warning):
    print("WARNING: {}".format(warning))


def load_gmail_info():
    gmail_user = "lxe.readout@gmail.com"
    gmail_pwd = os.environ["LXEPASS"] # password for this account
    return gmail_user, gmail_pwd


def filter_SMS(users):
    """ 
    return dict of users, with email-to-SMS removed
    * also remove alexis's gmail
    """
    new_dict = {}
    for user, addresses in users.items():
        new_addresses = []
        for address in addresses:
            #print "%s: %s" % (user, address)
            # skip SMS:
            if "tmomail" in address: continue # t-mobile
            if "sprintpcs" in address: continue # sprint
            if "vtext" in address: continue # verizon
            if "att" in address: continue # AT&T
            print("keeping {}: {}".format(user, address))
            new_addresses.append(address)
        if len(new_addresses) > 0: new_dict[user] = new_addresses
    return new_dict


class LXeMonitoring:

    def __init__(self):

        username1 = 'bgle'
        username2 = 'nardo@'
        host1 = 'gma'
        host2 = 'il'
        extension1 = '.co'
        extension2 = 'm'

        username1sx = 'shuo'
        username2sx = 'xing.wu@'

        #define users here:
        self.users = {
		'brian':['{}{}{}{}{}{}'.format(username1,username2,host1,host2,extension1,extension2)],
		'shuoxing':['{}{}{}{}{}{}'.format(username1sx,username2sx,host1,host2,extension1,extension2)]
            #'mike':[
            #    #'0000000000@txt.att.net', # cell
            #    '0000000000@mms.att.net',
            #    'mike@emailaddress.com', 
            #],
        }

    def main(self, do_debug, do_test, no_lxe):


        # trying to avoid UnboundLocalError 
        global temperature_threshold
        global cell_bot_temp_threshold
        global cell_mid_temp_threshold
        global cell_top_temp_threshold
        global pressure_10k_threshold
        global pressure_1k_threshold
        global temp_xe1_recirc_threshold
        global temp_xe2_recirc_threshold
        global ln_mass_threshold
        global ln_hours_left_threshold
        global dp_threshold
        global lookback_time_minutes
        global sleep_seconds
        global cu_plate_in_threshold

        self.do_test = do_test
        self.do_debug = do_debug
        self.lxe = not no_lxe

        start_time = datetime.datetime.now()

        if self.lxe:
            print('\n----> monitoring for LXe\n')
        else:
            print('===> WARNING: LXe is set to false!')
            print('\t LN mass, Cu & cell temps, will *NOT* be monitored')
        

        if self.do_test:
            print("====> doing test... changing thresholds so all alarms trigger")
            # change thresholds so all alarms will trigger:
            temperature_threshold = 0.0
            cu_plate_in_threshold = 0.0
            dp_threshold = -1e5
            ln_mass_threshold = -100
            ln_hours_left_threshold = -100
            lookback_time_minutes = -1.0
            self.do_debug = True
            self.lxe = True

        if self.do_test:
            print("===> this is a test... ")

        if self.do_debug:
            print("--> DEBUGGING")

        # check once to be sure this script is working ok
        self.self_checks() 

        n_issues = 0
        last_heartbeat = None
        # perform other checks in infinite loop!
        while True:

            now = datetime.datetime.now()
            print('===> starting monitoring loop {}'.format(now))

            try:
                self.do_ping() # ping the Omega LN controller
                num_checks=0
                while num_checks < 10:
                    if self.check_dropbox_data() < 0:
                        #Sleep for 30 seconds and try again
                        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ Failed to get LV data wait and try again {}".format(num_checks))
                        time.sleep(30)
                        num_checks+=1
                    else:
                        num_checks=0
                        break

                if num_checks==10:
                    self.send_messages("LV is not updating even after multiple tries. \n")

                # heartbeat info -- send a periodic email to show that things are
                # working
                if last_heartbeat == None or last_heartbeat < now - datetime.timedelta(hours=heartbeat_interval_hours):
                    print("--> heartbeat at:{}".format(now))
                    message = "heartbeat at: %s \n" % now
                    message += "there have been %i issues \n" % n_issues
                    message += "script has been running since: %s \n" % start_time
                    message += "heartbeat_interval_hours: %s \n" % heartbeat_interval_hours
                    if last_heartbeat:
                        message += "last heartbeat sent at %s \n" % last_heartbeat
                    else:
                        message += "this is the first heartbeat \n"


                    # add threshold info:
                    message += "\n"
                    message += "threshold info: \n"
                    message += "temperature_threshold: %.2f K \n" % temperature_threshold 
                    message += "cu_plate_in_threshold: %.2f K \n" % cu_plate_in_threshold 
                    message += "ln_mass_threshold: %.1f lbs LN left \n" % ln_mass_threshold 
                    message += "dp_threshold: %.1f torr \n" % dp_threshold 
                    message += "ln_hours_left_threshold: %.2f hours \n" % ln_hours_left_threshold 
                    message += "lookback_time_minutes: %.2f minutes \n" % lookback_time_minutes 
                    message += "heartbeat_interval_hours: %.2f hours between these emails\n" % heartbeat_interval_hours 
                    message += "sleep_seconds: %.2f seconds between script loops \n" % sleep_seconds 

                    last_heartbeat = now
                    #print message
                    filtered_users = filter_SMS(self.users) 
                    print("Filtered users {}".format(filtered_users))
                    self.send_messages(message, users=filtered_users, is_heartbeat=True)

                if self.do_test:
                    print("====> testing is done")
                    break

            #except smtplib.SMTPException:
            #    print "Meh not sure"
            except smtplib.SMTPHeloError:
                print("Hello Error")
            except smtplib.SMTPAuthenticationError:
                print("Authentication error")
            except:
                n_issues += 1
                print("There have been {} issues with script!".format(n_issues))
                for i in range(10):
                    print('\a') # audible alarm!

            now = datetime.datetime.now()
            print('===> done with monitoring cycle at {}'.format(now))

            print("---> sleeping for {} seconds".format(sleep_seconds))
            time.sleep(sleep_seconds) # sleep for sleep_seconds


    def self_checks(self):
        """ 
        before trying anything, test that we can:
        * send a single test message
        * loop over users and addresses
        """

        print("--> checking that mail info exists:")
        load_gmail_info()
        print("\t ok")

        # print list of active users & addresses to be sure we can loop over them:
        print("--> users and addresses:")
        for user, addresses  in self.users.items():
            print("\t{}:".format(user))
            for address in addresses:
                print("\t\t{}".format( address))


    def send_messages(self, msg, users=None, is_heartbeat=False):
        """ loop over all addresses for users and email message"""
        print("--> sending mail...")
        if not is_heartbeat: print('\a') # audible alarm!
        #print "\t message:", msg
        if users==None: users = self.users
        for user, addresses  in users.items():
            print("\t user: {}:".format(user))
            for address in addresses:
                print("\t\t{}".format( address))
                self.sendmail(msg, address, is_heartbeat)

    def do_ping(self, timeout=20):
        """ 
        ping the Omega LN controller to test for power outage 
        ping options:
          -o exit after 1st success
          -t exit after timeout of specified number of seconds
        """

        print("--> pinging Omega LN controller")
        if os.uname()[0] == "Darwin":
            cmd = "ping -o -t %i 171.64.56.58" % timeout # AGS Mac OSX
        else:
            cmd = "ping -c 1 -w %i 171.64.56.58" % timeout # SLAC rhel6-64
        output = process_provider.getstatusoutput(cmd)
        if self.do_debug: 
            print("\t{}".format( cmd))
            print(output[1])
        if output[0] != 0 or self.do_test:
            message = "Power outage? Cannot communicate with Omega LN controller \n"
            message += "command: %s \n" % cmd
            message += "output: \n"
            message += "%s \n" % output[0]
            message += output[1]

            print_warning(message)
            self.send_messages(message)
        else:
            print("\t success")


    def get_dropbox_data(self):
        """ download text file summary from dropbox currentPlots, parse for info """
        print("--> getting log file from dropbox:")
        
        file_name = "99-log.txt" # dropbox log file

        # remove old log file 
        # -f: don't complain if file doesn't exist
        cmd = 'rm %s' % file_name
        output = process_provider.getstatusoutput(cmd)
        if output[0] != 0 or self.do_debug:
            print("-- removing old file")
            print(cmd)
            print(output[1])
 
        #cmd = 'curl -L -o %s https://www.dropbox.com/sh/an4du1pzdnl4e5z/AADd6Xcdi78WinEMHz3XGEO1a/%s' % (
        #    file_name, file_name)
        #https://www.dropbox.com/s/67h27p2272g8ghw/99-log.txt?dl=0
        link_name = 'https://www.dropbox.com/s/67h27p2272g8ghw/'
        cmd = 'curl -L -o %s %s/%s ' % (file_name,link_name,file_name)
        
        output = process_provider.getstatusoutput(cmd)
        if output[0] != 0 or self.do_debug:
            print("--> trying to download log file from dropbox:")
            message = "Trouble downloading file from dropbox \n"
            message += "command: %s \n" % cmd
            message += "output: %s \n " % output[1]
            print_warning(message)
            self.send_messages(message)
        else:
            print("\t success")

        data = {}

        print("--> parsing file...")
        # open the file and read it:
        log_file = open(file_name)
        for line in log_file:

            if 'dP' in line:
                dP_torr = float(line.split(":")[1])
                data['dP_torr'] = dP_torr
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  dP_torr))

            if 'LN mass' in line:
                ln_mass_lbs = float(line.split(':')[1])
                data['ln_mass_lbs'] = ln_mass_lbs
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  ln_mass_lbs))

            if 'Last LabView time stamp' in line:
                LV_time= (':').join(line.split(':')[1:])
                LV_time = (" ").join(LV_time.split()) # get rid of trailing characters
                data['LV_time'] = LV_time
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0], LV_time))

            if 'LN time remaining' in line:
                ln_hours_left = float(line.split(':')[1])
                data['ln_hours_left'] = float(line.split(':')[1])
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  ln_hours_left))

            if 'Cu top [K]' in line:
                cu_top = float(line.split(':')[1].split()[0])
                data['cu_top'] = cu_top
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  cu_top))

            if 'Cu bot [K]' in line:
                cu_bot = float(line.split(':')[1])
                data['cu_bot'] = cu_bot
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  cu_bot))

            if 'Cell top [K]' in line:
                cell_top = float(line.split(':')[1])
                data['cell_top'] = cell_top
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  cell_top))

            if 'Cell bot [K]' in line:
                cell_bot = float(line.split(':')[1])
                data['cell_bot'] = cell_bot
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  cell_bot))

            if 'Cell mid [K]' in line:
                cell_mid = float(line.split(':')[1])
                data['cell_mid'] = cell_mid
                if self.do_debug: print("\t{}: {}".format( line.split(":")[0],  cell_mid))

            if 'inlet' in line:
                ln_in_temp = float(line.split(':')[1])
                data['ln_in_temp'] = ln_in_temp

            if 'Xe 1 recirc [K]' in line:
                xe_1_recirc = float(line.split(':')[1])
                data['xe_1_recirc'] = xe_1_recirc

            if 'Xe 2 recirc [K]' in line:
                xe_2_recirc = float(line.split(':')[1])
                data['xe_2_recirc'] = xe_2_recirc

            if 'XP5 Vacuum system pressure (1k Torr Baratron) [Torr]' in line:
                pressure_1k = float(line.split(':')[1])
                data['pressure_1k'] = pressure_1k

            if 'XP3 Xenon system pressure (10k Torr Baratron) [Torr]' in line:
                pressure_10k = float(line.split(':')[1])
                data['pressure_10k'] = pressure_10k
                
        print("\t done")
        return data


    def check_dropbox_data(self):
        """ check dropbox data against thresholds """
        data = self.get_dropbox_data()
        print("--> checking dropbox data:")

        if self.do_debug: 
            print("--> dropbox data:")
            for key, value in data.items():
                print("\t{} {}".format( key, value))

        messages = []

        #if data['dP_torr'] > dp_threshold:
        #    message = "dP = %.1f torr" % data['dP_torr']
        #    messages.append(message)
        #    print_warning(message)

        if self.lxe:

            # check time until LN runs out:
            if data['ln_hours_left'] < ln_hours_left_threshold:
                message = "hours of LN remaining: %.2f" % data['ln_hours_left']
                messages.append(message)
                print_warning(message)

            # check remaining LN mass:
            if data['ln_mass_lbs'] < ln_mass_threshold:
                message = "LN mass dangerously low: %.2f lbs" % data['ln_mass_lbs']
                messages.append(message)
                print_warning(message)

            # check temps in HFE dewar:
#            temps = ['cu_top', 'cu_bot', 'cell_top', 'cell_mid', 'cell_bot']
#            for key in temps:
#                if data[key] > temperature_threshold:
#                    message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], temperature_threshold)
#                    messages.append(message)
#                    print_warning(message)
            
            key = 'cu_top'
            if data[key] > cu_plate_in_threshold:
                message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], cu_plate_in_threshold)
                messages.append(message)
                print_warning(message)


            key = 'ln_in_temp'
            if data[key] > ln_in_thresh and is_fill:
                message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], ln_in_thresh)
                messages.append(message)
                print_warning(message)

            key = 'xe_1_recirc'
            if data[key] > temp_xe1_recirc_threshold:
                message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], temp_xe1_recirc_threshold)
                messages.append(message)
                print_warning(message)

            key = 'xe_2_recirc'
            if data[key] > temp_xe2_recirc_threshold:
                message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], temp_xe2_recirc_threshold)
                messages.append(message)
                print_warning(message)

            key = 'pressure_1k'
            if data[key] > pressure_1k_threshold:
                message = "%s = %.1f Torr (threshold=%.1f)" % (key, data[key], pressure_1k_threshold)
                messages.append(message)
                print_warning(message)

            key = 'pressure_1k'
            if data[key] < pressure_1k_low_threshold:
                message = "%s = %.1f Torr (threshold=%.1f)" % (key, data[key], pressure_1k_low_threshold)
                messages.append(message)
                print_warning(message)

            key = 'pressure_10k'
            if data[key] > pressure_10k_threshold:
                message = "%s = %.1f Torr (threshold=%.1f)" % (key, data[key], pressure_10k_threshold)
                messages.append(message)
                print_warning(message)

            key = 'cell_top'
            if data[key] > cell_top_temp_threshold:
                message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], cell_top_temp_threshold)
                messages.append(message)
                print_warning(message)

            key = 'cell_mid'
            if data[key] > cell_mid_temp_threshold:
                message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], cell_mid_temp_threshold)
                messages.append(message)
                print_warning(message)

            key = 'cell_bot'
            if data[key] > cell_bot_temp_threshold:
                message = "%s = %.1f K (threshold=%.1f)" % (key, data[key], cell_bot_temp_threshold)
                messages.append(message)
                print_warning(message)

        else:
            print("Warning: LXe is set to false -- not checking cell temps or LN remaining")

        # check how old the labview time stamp is:
        LV_time = data['LV_time']
        LV_time =  datetime.datetime.strptime(LV_time,"%Y-%m-%d %H:%M:%S.%f")
        if self.do_debug: print("LV_time: {}".format( LV_time))
        now  = datetime.datetime.now()
        time_elapsed =  now - LV_time
        if self.do_debug: print("time_elapsed: {}".format( time_elapsed))
        if LV_time < now - datetime.timedelta(minutes=lookback_time_minutes):
            time_elapsed =  now - LV_time
            
            # This occasionally glitches and looks at the wrong file
            # I think a cutoff of 20hrs makes sense.  Since this is either a glitch or you 
            # haven't paid attention for awhile.
            if time_elapsed.total_seconds()/(60*60) < 20:   
                message = "time elapsed since last LV time stamp: %s (hrs = %.2f)" %  (time_elapsed, time_elapsed.total_seconds()/(60.*60.))
                print_warning(message)
                messages.append(message)
            else:
                return -1

        #print (now-LV_time)
        #print dir((now-LV_time))
        #print (now-LV_time).total_seconds()/(60.*60.), (now-LV_time).seconds/(60.*60.)
        #raw_input("PAUSE")

        if len(messages) > 0:
            print("{} warnings".format( len(messages)))
            message = "\n".join(messages)
            self.send_messages(message)

        print("\t done")
        return 1

    def sendmail(self,message,address,is_heartbeat=False):
        """ send a message to a user """
        print("trying to send mail to {}...".format( address))
        gmail_user, gmail_pwd = load_gmail_info()
        smtpserver = smtplib.SMTP("smtp.gmail.com",587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo()
        print("Login info: {} {}".format( gmail_user, gmail_pwd))
        print("Doing the login")
        smtpserver.login(gmail_user, gmail_pwd)
        print("Done login")
        subject = "Stanford LXe System Alarm!"
        if self.do_test: subject = "TEST of " + subject
        if is_heartbeat: subject = "Stanford LXe system heartbeat from %s %s" % (
            os.uname()[0], os.uname()[1])
        header = 'To:' + address + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:%s \n' % subject
        print(header)
        info = "time: %s  \n" % datetime.datetime.now()
        info += "user: %s \n" % os.getlogin()
        info += "system info: %s \n" % " ".join(os.uname())
        msg = header + '\n%s\n%s\n' % (info, message)
        smtpserver.sendmail(gmail_user, address, msg)
        print('done! sending mail')
        smtpserver.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--no-lxe', action='store_true')
    args = parser.parse_args()

    monitor = LXeMonitoring()
    monitor.main(do_debug=args.debug, do_test=args.test, no_lxe=args.no_lxe)

