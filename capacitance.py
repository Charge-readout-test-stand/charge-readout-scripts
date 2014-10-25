import math
import matplotlib.pyplot as plt
import numpy as np

LXeH = np.arange(0.0004, 0.0246, 0.00004)
cpct = []

for i in LXeH:
    c1 = 1.96*8.854*(10**-12)*0.0248286/i
    c2 = 1*8.854*(10**-12)*0.0248286/(0.02464-i)
    cpct.append(10**12*(1/(1/c1 + 1/c2)))

plt.plot(LXeH, cpct)
plt.title('Capacitance vs. Height')
plt.xlabel('LXe height in m')
plt.ylabel('Capacitance in pF')
plt.show()

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