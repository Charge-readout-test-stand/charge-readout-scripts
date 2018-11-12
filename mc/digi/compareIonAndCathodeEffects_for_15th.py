import RalphWF
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

fig_size  = (10,6)
lfont_size = 20
lw = 3.0

def AddCollectedCharge(cathodeToAnodeDistance = 33.2, posion = False, cathsupress = False, lifetime=None):
    RalphWF.cathodeToAnodeDistance = cathodeToAnodeDistance
    RalphWF.posion = posion
    RalphWF.cathsupress = cathsupress
    RalphWF.lifetime = lifetime
    
    x = 1.5 # mm
    y = 0.0 # mm
    q = 1.0 # arbitrary
    z = 0 # distance from cathode
    wfm_length = 1000
    dz = (cathodeToAnodeDistance - z)/100.0

    collected_charge = []
    zpos = []

    while z <= cathodeToAnodeDistance+dz*0.5:
        WF = RalphWF.make_WF(x, y, z, q, 15,
                             cathodeToAnodeDistance=cathodeToAnodeDistance,
                             dZ=dz, wfm_length=wfm_length)
        zpos.append(cathodeToAnodeDistance-z)
        collected_charge.append(WF[-1])
        z+=dz
    
    return np.array(zpos), np.array(collected_charge)

def RunCollectedCharge():
    c2A = 1000.0
    c2A = 33.2

    zpos1, Q1 = AddCollectedCharge(cathodeToAnodeDistance = 33.2, posion = False, cathsupress = False)
    zpos2, Q2 = AddCollectedCharge(cathodeToAnodeDistance = 33.2, posion = True, cathsupress = False)
    zpos3, Q3 = AddCollectedCharge(cathodeToAnodeDistance = 33.2, posion = True, cathsupress = True)
    zpos4, Q4 = AddCollectedCharge(cathodeToAnodeDistance = 33.2, posion = True, cathsupress = True,lifetime=10)

    fig = plt.figure(figsize=fig_size)
    plt.plot(zpos4, Q4,ls='-', lw=lw, marker='None', color='b', label='No Screening or Cathode Effects')
    plt.plot(zpos3, Q3,ls='--', lw=lw, marker='None', color='k', label='Ion Screening + Cathode Effect')
    plt.plot(zpos2, Q2,ls='-.', lw=4.0, marker='None', color='r', label='Ion Screening Only')

    print "Test"
    for zz,xx in zip(zpos3, Q3): print zz,xx

    plt.axvline(33.2, ls='--', lw=lw, color='k')
    plt.ylim(0.0,1.1)
    plt.xlim(0.0,35.0)

    plt.ylabel("Fraction of Collected Charge", fontsize=lfont_size)
    plt.xlabel("Distance From Anode [mm]", fontsize=lfont_size)
    #plt.legend(numpoints=1, ncol=1, fontsize=lfont_size, bbox_to_anchor=(0.6,0.8), loc='center')
    lgd = plt.legend(numpoints=1, bbox_to_anchor=(0.0,1.02,1.0,0.102), loc=3, mode='expand', borderaxespad=0., ncol=2, fontsize=16)
    #plt.tight_layout()
    plt.grid()
    plt.tick_params(axis='both',which='major',labelsize=18)
    plt.show()
    fig.subplots_adjust(top=0.85)
    plt.savefig("frac_collected_3mm_teststand.pdf", bbbox_inches='tight', bbox_extra_artists=(lgd))
    raw_input()

def RunWeightPot():
    RalphWF.cathodeToAnodeDistance = 33.2
    RalphWF.posion = True
    RalphWF.cathsupress = True
    
    cathodeToAnodeDistance = RalphWF.cathodeToAnodeDistance

    x = 1.5 # mm
    y = 0.0 # mm
    q = 1.0 # arbitrary
    z = 0 # distance from cathode
    wfm_length = 1000
    dz = (cathodeToAnodeDistance - z)/1000.0

    WF = RalphWF.make_WF(x, y, z, q, 15,
                         cathodeToAnodeDistance=cathodeToAnodeDistance,
                         dZ=dz, wfm_length=wfm_length)
    zplot = cathodeToAnodeDistance - np.arange(len(WF))*dz


    RalphWF.cathodeToAnodeDistance = 6.0
    RalphWF.posion = True
    cathodeToAnodeDistance = RalphWF.cathodeToAnodeDistance
    WFFrisch = RalphWF.make_WF(x, y, z, q, 15,
                               cathodeToAnodeDistance=cathodeToAnodeDistance,
                               dZ=dz, wfm_length=wfm_length)
    zplotFrisch = cathodeToAnodeDistance - np.arange(len(WFFrisch))*dz

    plane_frisch = np.polyval([-1/6.0, 1.0],zplot)
    plane_frisch[zplot>6.0] = 0.0

    print zplot.size
    print WF.size
    fig=plt.figure(figsize=fig_size)
    plt.plot(zplot,WF, ls='-', lw=lw, marker='None', color='b', label='Tile Design, 3mm strip pitch, no Grid')
    plt.plot(zplotFrisch, WFFrisch, ls='--', lw=lw, marker='None', color='k', label='Tile Design, 3mm strip pitch, with Grid')
    plt.plot(zplot,plane_frisch, ls='-.', lw=lw, marker='None', color='r', label='Planar Anode, with Grid')
    
    plt.axvline(33.2, ls='--', lw=lw, color='k')
    plt.ylim(0.0,1.1)
    plt.xlim(0.0,35.0)
    plt.ylabel("Weighting Potential", fontsize=lfont_size)
    plt.xlabel("Distance From Anode [mm]", fontsize=lfont_size)
    plt.legend(numpoints=1, bbox_to_anchor=(0.0,1.02,1.0,0.102), loc=3, mode='expand', borderaxespad=0., ncol=2)
    #plt.legend(numpoints=1, ncol=1, fontsize=lfont_size, bbox_to_anchor=(0.6,0.8), loc='center')
    fig.subplots_adjust(top=0.85)
    plt.grid()
    plt.show()
    plt.savefig("weighting_potential_3mm_teststand_grids.pdf", bbbox_inches='tight')
    raw_input()

if __name__ == "__main__":
    RunCollectedCharge()
    #RunWeightPot()

