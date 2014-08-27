#Runs the TPMLog script every 10 minutes for new plots
import glob, os, threading
import TPMLog

def datalog():
    flist = glob.glob('C://Users//xenon//Dropbox//LabViewData//*.dat')
    testfile = flist[-1]
    print testfile
    TPMLog.main(testfile)
    threading.Timer(600, datalog).start()

datalog()