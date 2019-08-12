import numpy as np
import matplotlib.pyplot as plt

def get_res(ene, field, e0, lam=0.3, Fqs=1.0, sigQ=2*200):
    
    if ene==570 and field==1000:
        #NEST Light/Charge yields for 570keV Gamma (1kV/cm)
        Q = 30000.0
        S = 13000.0
    elif ene==570 and field==400:
        #NEST Light/Charge yields for 570keV Gamma (400V/cm)
        Q = 23000.0
        S = 20000.0
    elif ene==1000 and field==1000:
        #NEST Light/Charge yields for 570keV Gamma (1kV/cm)
        Q = 57000.0
        S = 22000.0
    elif ene==1000 and field==400:
        #NEST Light/Charge yields for 570keV Gamma (400V/cm)
        Q = 45000.0
        S = 33000.0
    elif ene==2450 and field==400:
        #NEST Light/Charge yield for QBB at 400V/cm
        Q = 114000.0
        S = 69000.0
    elif ene==2450 and field==1000:
        Q= 140000.0
        S=45000.0
    else:
        print "Not a field/E option" 
        return
    
    A = e0*S*(1 + lam)
    O = Q + A/(e0*(1 + lam))

    sigO = Fqs*O + sigQ**2 + ((1+lam)*(1+lam)*e0*(1 - e0)*S + e0*lam*S)/(e0*e0*(1+lam)*(1+lam)) #+ sigS**2
    sigO = np.sqrt(sigO)

    #print sigO, O, sigO/O
    return (sigO*100)/O

if __name__ == "__main__":

    e0=np.arange(0.0, 0.05, 0.0001)
    res_e570_f1kV  = get_res(ene=570,field=1000, e0=e0)
    res_e570_f400V = get_res(ene=570,field=400, e0=e0)
    
    res_e1000_f1kV  = get_res(ene=1000,field=1000, e0=e0)
    res_e1000_f400V = get_res(ene=1000,field=400, e0=e0)
    
    plt.figure(1)

    plt.plot(e0*100,res_e570_f1kV,  color='r', linewidth=2, label='Pred: 1kV/cm')
    plt.plot(e0*100,res_e570_f400V, color='g', linewidth=2, label='Pred: 400V/cm')

    plt.title("Predicted Resolution 570keV Peak", fontsize=17)
    plt.xlabel("Collection Efficency [%]", fontsize=17)
    plt.ylabel("Predicted Resolution [%]", fontsize=17)


    plt.xlim(0.01, 3)
    plt.ylim(0.5,8.0)

    plt.axhline(3.7,color='r', linewidth=4.0, linestyle='--', label='Obs:1kV/cm')
    plt.axhline(4.8,color='g', linewidth=4.0, linestyle='--', label='Obs:400V/cm')
    plt.grid(True)
    plt.legend()

    plt.savefig("res_pred_570.png")

    plt.figure(2)

    plt.title("Predicted Resolution 1064keV Peak", fontsize=17)

    plt.plot(e0*100,res_e1000_f1kV,  color='r', linewidth=2, label='Pred: 1kV/cm')
    plt.plot(e0*100,res_e1000_f400V, color='g', linewidth=2, label='Pred: 400V/cm')

    plt.xlabel("Collection Efficency [%]", fontsize=17)
    plt.ylabel("Predicted Resolution [%]", fontsize=17)


    plt.xlim(0.01, 3)
    plt.ylim(0.5,8.0)

    plt.axhline(2.7,color='r', linewidth=4.0, linestyle='--', label='Obs:1kV/cm')
    plt.axhline(3.3,color='g', linewidth=4.0, linestyle='--', label='Obs:400V/cm')
    plt.grid(True)
    plt.legend()

    plt.savefig("res_pred_1000.png")


    plt.figure(4)
    res_eQ_f400V = get_res(ene=2450,field=400, e0=e0)
    res_eQ_f1V   = get_res(ene=2450,field=1000, e0=e0)

    

    plt.plot(e0*100, res_eQ_f400V,  color='g', linewidth=2, label='(Qval, 400V/cm)')
    plt.plot(e0*100, res_eQ_f1V,    color='r', linewidth=2, label='(Qval,1kV/cm)')

    plt.xlim(0.01, 3)
    plt.ylim(0.5,8.0)

    plt.grid(True)
    plt.xlabel("Collection Efficency [%]", fontsize=17)
    plt.ylabel("Predicted Resolution [%]", fontsize=17)
    plt.legend()


    plt.show()


