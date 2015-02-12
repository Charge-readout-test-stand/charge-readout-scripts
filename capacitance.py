import math
import matplotlib.pyplot as plt
import numpy as np

eps = 1e-5
anode_cathode_distance = 0.0248286 # m
LXeH = np.arange(eps, anode_cathode_distance-eps, 0.00004)
cpct = []

for z in LXeH:
    lxe_dielectric_constant = 1.96
    gxe_dielectric_constant = 1.0
    vacuum_permittivity = 8.854e-12
    
    
    c1 = lxe_dielectric_constant*vacuum_permittivity*anode_cathode_distance/z
    c2 = gxe_dielectric_constant*vacuum_permittivity*anode_cathode_distance/(anode_cathode_distance-z)
    
    # total capacitance (add in series, convert to pF)
    cpct.append(10**12*(1/(1/c1 + 1/c2)))
    
print "capacitance with no LXe [pF]", cpct[0]
print "capacitance full of LXe [pF]", cpct[-1]

plt.plot(LXeH, cpct)
plt.grid(b=True)
plt.title('Capacitance vs. Height')
plt.xlabel('LXe height from cathode in m')
plt.ylabel('Capacitance in pF')
plt.savefig("capacitance.jpg")
print "printed"
plt.clf()
    
# stuff below here is not used    

def LXe_height(volume):
    if volume > 0.00126:
        return (volume - 0.00126)/(0.02482866)
    else:
        return 0 

def LXe_cpct(height):
    if height != 0:
         C1 = 1.96*8.854*(10**-12)*0.0248286/height
         C2 = 1*8.854*(10**-12)*0.0248286/(0.02464-height)
         return 10**12*(1/(1/C1 + 1/C2))
    else:
        return 8.92