import RalphWF 
import numpy as np
import matplotlib.pyplot as plt

sampling_period  = RalphWF.sampling_period
driftV           = RalphWF.drift_velocity

x = 4.5
y = 0
z = 0
E = 1
ch = 16
maxSamp = int((33.23/driftV)/sampling_period)

sl10 = 0.1
sl1  = 0.01
sh = 0.95

#for E in [0.9, 1.0]:
for E in [1.0]:
    plt.figure(1)
    plt.clf()
   
    plt.figure(11)
    plt.clf()

    risetime10=[]
    risetime1 =[]
    trueRise =[]
    trueZ    =[]
    collQ    =[]
    
    for z in np.arange(0.0, 31.0, 1.0):
        wfm = RalphWF.make_WF(x,y,z, E, ch, 33.23, sampling_period*driftV, 800)

        print "Z-Start %.2f Collect time %.2f us" % (z, (33.23-z)/driftV)
    
        collect_time =  (33.23-z)/driftV
        collect_sample = int(collect_time/sampling_period)
    
        new_wfm = np.zeros_like(wfm)
        new_wfm[(maxSamp-collect_sample):maxSamp] = wfm[0:collect_sample]
        new_wfm[maxSamp:] = np.max(wfm)

        val99 = np.argmin(np.abs(sh*np.max(new_wfm) - new_wfm))
        val10  = np.argmin(np.abs(sl10*np.max(new_wfm) - new_wfm))
        val1  = np.argmin(np.abs(sl1*np.max(new_wfm) - new_wfm))

        sample_times = np.arange(len(wfm))*sampling_period
    
        risetime10.append( sample_times[val99] - sample_times[val10])
        risetime1.append( sample_times[val99] - sample_times[val1])
        trueZ.append(z)
        trueRise.append(collect_time)
        collQ.append(np.max(new_wfm))

        if z%10 == 0:
            plt.figure(1)
            plt.plot(sample_times, new_wfm, label='Drift=%.2fmm'%(33.23-z))
            plt.ylim(-0.1, 1.1)
            plt.plot([sample_times[val10], sample_times[val99]], [new_wfm[val10], new_wfm[val99]],marker='o',
                        ms=10, color='k', linestyle="None")
            plt.title("Risetime 10%", fontsize=17)
            plt.xlim(10,20)

            plt.figure(11)
            plt.plot(sample_times, new_wfm, label='Drift=%.2fmm'%(33.23-z))
            plt.ylim(-0.1, 1.1)
            plt.plot([sample_times[val1], sample_times[val99]], [new_wfm[val1], new_wfm[val99]],marker='o',
                        ms=10, color='k', linestyle="None")
            plt.title("Risetime 1%", fontsize=17)
            plt.xlim(2,20)

    plt.figure(1)
    plt.legend(loc="upper left")
    plt.figure(11)
    plt.legend(loc="upper left")

    plt.figure(2)
    plt.plot(trueZ, np.asarray(risetime10)*1.e3, label='E=%.2f' % E)
    #plt.legend(loc='lower left')
    plt.title("Risetime 10%", fontsize=17)
    plt.ylabel("Risetime [ns]" , fontsize=17)
    plt.xlabel("Z [mm]", fontsize=17)
 
    plt.figure(20)
    plt.plot(trueRise, np.asarray(risetime10)*1.e3, label='E=%.2f' % E)
    plt.title("Risetime 10%", fontsize=17)
    plt.ylabel("Risetime [ns]" , fontsize=17)
    plt.xlabel("Collect Time [us]", fontsize=17)


    plt.figure(22)
    plt.plot(trueZ, np.asarray(risetime1)*1.e3, label='E=%.2f' % E)
    #plt.legend(loc='lower left')
    plt.title("Risetime 1%", fontsize=17)
    plt.ylabel("Risetime [ns]" , fontsize=17)
    plt.xlabel("Z [mm]", fontsize=17)


    #plt.figure(3)
    #plt.plot(trueZ, collQ,  label='E=%.2f' % E)
    #plt.legend(loc='lower left')
    #plt.xlabel("Energy [keV]", fontsize=17)
    #plt.ylabel("Z [mm]", fontsize=17)



wfm1 = RalphWF.make_WF(x,y,0.0, 0.5, ch, 33.23, sampling_period*driftV, 800)
wfm_sum = wfm1
sample_times = np.arange(len(wfm_sum))*sampling_period
val99  = np.argmin(np.abs(sh*np.max(wfm_sum) - wfm_sum))
val10  = np.argmin(np.abs(sl10*np.max(wfm_sum) - wfm_sum))
val1   = np.argmin(np.abs(sl1*np.max(wfm_sum) - wfm_sum))

print sample_times[val99] - sample_times[val10],
print sample_times[val99] - sample_times[val1]

wfm2 = RalphWF.make_WF(x,y,1.0, 0.5, ch, 33.23, sampling_period*driftV, 800)
wfm_sum = wfm1 + wfm2
sample_times = np.arange(len(wfm_sum))*sampling_period
val99  = np.argmin(np.abs(sh*np.max(wfm_sum) - wfm_sum))
val10  = np.argmin(np.abs(sl10*np.max(wfm_sum) - wfm_sum))
val1   = np.argmin(np.abs(sl1*np.max(wfm_sum) - wfm_sum))

print sample_times[val99] - sample_times[val10],
print sample_times[val99] - sample_times[val1]



plt.figure(9)

plt.plot(wfm1*2)
plt.plot(wfm_sum)

plt.ylim(-0.1, 1.1)
plt.xlim(0, 600)

plt.show()
raw_input()


