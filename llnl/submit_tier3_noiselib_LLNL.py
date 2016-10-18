import ROOT
import os
import sys
import subprocess
import glob,random,stat

def main(indir,nproc):

    globname = "tier1*.root"
    globname = os.path.join(indir, globname)
    filelist = glob.glob(globname)
    random.shuffle(filelist)

    hours = 2
    mins = 0
    time = 'walltime=%02i:%02i:00' % (hours, mins)
    queue = "pbatch"
    #gentier3 = "/g/g19/jewell6/software/charge-readout-scripts/struck/generateTier3Files.py"
    gentier3 = "generateTier3Files.py"
    
    scriptdir = "scripts/"
    if not os.path.isdir(scriptdir):
        os.mkdir(scriptdir) 

    libdir = "noiselib/"
    if not os.path.isdir(libdir):
        os.mkdir(libdir)

    for filename in filelist[:nproc]:
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        
        batch_script_name = "script_%s.sh" % basename
        batch_script_name = os.path.join(scriptdir, batch_script_name)
        batch_script = open(batch_script_name,'w')
        batch_script.write("#!/bin/bash \n")
        batch_script.write('source ~/setup_NGM.sh \n')
        batch_script.write('printenv \n')
        batch_script.write('pwd \n')
        batch_script.write('time python %s --Noise -D %s %s \n' % (gentier3, libdir, filename))
        batch_script.close()
        print "batch_script_name:", batch_script_name  

        #Get current permissions
        st = os.stat(batch_script_name)
        os.chmod(batch_script_name, st.st_mode | stat.S_IXUSR)

        out = "out_%s.out" % basename
        out = os.path.join(scriptdir, out)

        #msub -A afqn -m abe -V -N test -o test.out -j oe -q pbatch -l walltime=01:00:00 -l ttc=1 scripts/script_tier1_SIS3316Raw_20160922125621_9thLXe_126mvDT_cath_1700V_100cg_overnight__1-ngm.sh
        cmd = ['msub', '-A', 'afqn', '-m', 'abe', '-V', '-N', basename, 
               '-o', out, '-j' , 'oe', '-q', queue, '-l', time, 
               '-l', 'ttc=1', batch_script_name]

        
        #process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
        #process.stdin.close()

        process = subprocess.Popen(cmd)
        process.wait()
        print process.returncode
        print "Done"
        #if process.wait() != 0:
        #    print "There were some errors"


if __name__ == "__main__":
    
    #/g/g19/jewell6/alexiss/9thLXe/2016_09_19_overnight/tier1/

    if len(sys.argv) < 2:
        print "arguments: [directory with tier1 files] [number to proc]"
        print "/g/g19/jewell6/alexiss/9thLXe/2016_09_19_overnight/tier1/"
        sys.exit(1)

    indir = sys.argv[1]
    nproc = int(sys.argv[2])

    if not os.path.isdir(indir):
        print "arguments: [directory with tier1 files]"
        sys.exit(1)

    main(indir, nproc)
