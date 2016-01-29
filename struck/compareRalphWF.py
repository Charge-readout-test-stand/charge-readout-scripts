
import numpy as np
import matplotlib.pyplot as plt

from RalphWF import make_WF


if __name__ == "__main__":
    
    plt.figure(1)
    #Collection signal on channel X16
    WF = make_WF(1.5, 0.0, 0.0, 1, 15)
    plt.plot(WF)
    plt.ylim([-0.1,1.1])


    plt.figure(2)
    #Induction signal X15
    WF = make_WF(1.5, 0.0, 0.0, 1, 14)
    plt.plot(WF)
    plt.ylim([-0.1,1.1])
    
    
    plt.figure(3)
    #Induction signal Y16
    WF = make_WF(1.5, 0.0, 0.0, 1, 45)
    plt.plot(WF)
    plt.ylim([-0.1,1.1])
    plt.show()

   

