import ROOT
import numpy as np
import matplotlib.pyplot as plt
import datetime

#tree->Draw("baseline_rms[25]*(2000/2^14):(file_start_time + time_stamp_msec*1.e-3)","nfound_channels==30")

def IntegrateMass(times, mass_flow_rate):
    mass = 0.0
    total_mass = []
    mass_flow_rate_offset = 173.0/(20*60) #- (55.0/(39*60))
    #mass_flow_rate_offset = 0.0
    xenon_gas_density = 5.89
    xenon_density_ratio = xenon_gas_density/5.3612


    for (i_time, second_time) in enumerate(times):
        delta_time_minutes  = 0.0 
        if i_time > 0:                                      
            delta_time_minutes = (second_time - times[i_time-1])/60.
                                                                    
        mass += (mass_flow_rate[i_time] - mass_flow_rate_offset)*delta_time_minutes                           
        total_mass.append(mass)
    return np.array(total_mass)


def Process():
    tfile = ROOT.TFile("tier3_recovery_all.root")
    #tfile  = ROOT.TFile("testadd.root")
    tree = tfile.Get("tree")
    tree.SetEstimate(tree.GetEntries())

    cut = "nfound_channels==30"
    dcmd = "baseline_rms[25]*(2000/2^14):(file_start_time + time_stamp_msec*1.e-3)"
    tree.Draw(dcmd,cut,"goff")
    n = tree.GetSelectedRows()
    
    baseline_rms = np.array([tree.GetV1()[i] for i in xrange(n)])
    posix_time   = np.array([tree.GetV2()[i] for i in xrange(n)])

    posix_time -= 28800

    time_since_start_hours = (posix_time - np.min(posix_time) )/(3600.)
    print "Minimum time is ", datetime.datetime.fromtimestamp(np.min(posix_time)).strftime('%Y-%m-%d %H:%M:%S')
    print "Maximum time is ", datetime.datetime.fromtimestamp(np.max(posix_time)).strftime('%Y-%m-%d %H:%M:%S')

    xmin = 7.5
    xmax = 9.5
    
    f, (ax1,ax2,ax3) = plt.subplots(3, sharex=True, figsize=(10,7))
    
    #print baseline_rms
    ax1.plot(time_since_start_hours, baseline_rms, marker='o', linestyle='None', c='r')
    ax1.set_ylabel("RMS Noise Ch 25 [mV]")
    #ax1.set_ylim(0.)

    #Now do LabView Stuff
    lv_to_unix_time = 2082844800
    time_lv, mass_flow = np.loadtxt("test_20171127_123414.dat", unpack=True, usecols=(0,21))
    xenon_gas_density = 5.89
    xenon_density_ratio = xenon_gas_density/5.3612
    mass_flow *= xenon_density_ratio

    total_mass = IntegrateMass(time_lv, mass_flow)

    time_unix = time_lv - lv_to_unix_time
    #plt.figure(4)
    #plt.plot((time_unix-np.min(time_unix))/3600., total_mass, marker='o', linestyle='-')
    
    use_times = np.logical_and(time_unix > np.min(posix_time), time_unix < np.max(posix_time))
    total_mass = total_mass[use_times]

    time_unix_hours = (time_unix[use_times] - np.min(posix_time))/3600.0
    plt.xlim(xmin,xmax)

    #Total Remaining Mass
    ax2.plot(time_unix_hours, total_mass/1.e3,  marker='o', linestyle='None', c='b')
    ax2.set_ylabel("Mass in Cell [kg]")
    ax2.set_ylim(0.0,1.5)

    #Mass to height guess
    r_behind = 5.0 #cm
    xe_den =   3.0 #g/cm^3 in liquid
    height_behind_sipms = total_mass/(np.pi*r_behind*r_behind*xe_den)
    ax3.plot(time_unix_hours, height_behind_sipms, marker='o', linestyle='None', c='g')
    ax3.axhline(4.379, c='k', linewidth=2.0, linestyle='--')
    ax3.set_ylim(0.0,6.0)
    ax3.set_ylabel("Height Left [cm]")


    plt.xlim(xmin,xmax)
    f.subplots_adjust(hspace=0.05)
    plt.xlabel("Hours Since Refill Start at %s" % datetime.datetime.fromtimestamp(np.min(posix_time)).strftime('%Y-%m-%d %H:%M:%S'))
    plt.savefig("noise_vs_mass.png")
    plt.show()


if __name__ == "__main__":
    Process()




