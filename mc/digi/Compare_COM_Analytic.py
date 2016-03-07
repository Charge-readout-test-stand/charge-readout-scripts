import COMSOLWF
import RalphWF
import numpy as np
import matplotlib.pyplot as plt


if __name__ == "__main__":
    sample_times = np.arange(800)*40*1e-3

    pcdx= 1.5
    pcdy = 0.0
    pcdz = 0.0

    plt.figure(1)
    #Collection signal on channel X16
    plt.title("Collection siganl X16 COMSOL vs Analytic")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WFA = RalphWF.make_WF(pcdx, pcdy, pcdz, 1, 15)
    WFC = COMSOLWF.make_WF(pcdx, pcdy, pcdz, 1, 15)
    plt.plot(sample_times, WFA, c='r', label="Analytic")
    plt.plot(sample_times, WFC, c='b', label="COMSOL")
    plt.ylim([-np.max(WFA)*0.1, np.max(WFA)*1.1])
    legend = plt.legend(loc='upper left',shadow=True)
    plt.savefig("./plots/collect_X16_compare.png")

    plt.figure(2)
    #Induction signal X15
    plt.title("Induciton siganl X15 COMSOL vs Analytic")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WFA = RalphWF.make_WF(pcdx, pcdy, pcdz, 1, 14)
    WFC = COMSOLWF.make_WF(pcdx, pcdy, pcdz, 1, 14)
    plt.plot(sample_times, WFA, c='r', label="Analytic")
    plt.plot(sample_times, WFC, c='b', label="COMSOL")
    plt.ylim([-np.max(WFA)*0.1, np.max(WFA)*1.1])
    legend = plt.legend(loc='upper left',shadow=True)
    plt.savefig("./plots/induct_X15_compare.png")

    plt.figure(3)
    #Induction signal Y16
    plt.title("Induction siganl Y16 COMSOL vs Analytic")
    plt.xlabel("Time[$\mu$s]")
    plt.ylabel("Q/Qtotal")
    WFA = RalphWF.make_WF(pcdx, pcdy, pcdz, 1, 45)
    WFC = COMSOLWF.make_WF(pcdx, pcdy, pcdz, 1, 45)
    plt.plot(sample_times, WFA, c='r', label="Analytic")
    plt.plot(sample_times, WFC, c='b', label="COMSOL")
    plt.ylim([-np.max(WFA)*0.1, np.max(WFA)*1.1])
    legend = plt.legend(loc='upper left',shadow=True)
    plt.savefig("./plots/induct_Y16_compare.png")

    plt.show()
    raw_input()


