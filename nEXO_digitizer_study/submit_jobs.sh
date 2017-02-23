#!/bin/bash

# run this from the command line for testing. To really run jobs, use
# loopSubmitJobs.py



#-------------------------------------------------------------------------------
# options ----
#-------------------------------------------------------------------------------


# define these vars:
# NEXOANALYSIS -- defined in .cshrc

umask 027 # owner=read+write+execute, group=read+execute, all=none
source $HOME/setup_nEXO.sh

# base output directory 
export nEXODataDir=$PWD
export NEXOANALYSIS=$HOME/software/digitizer_study/nEXO_analysis_charge_digitizer_study

# nEXO MC build:
export NEXOMCBUILD="$HOME/software/digitizer_study/build_nEXO_MC/"

# nEXO MC:
export NEXOMC="$HOME/software/digitizer_study/nEXO_MC/"

# charge-readout-scripts
export CHARGEREADOUTSCRIPTS="$HOME/software/charge-readout-scripts/nEXO_digitizer_study/"


TYPE=nEXO_bb0n
    
# from the command line, just do tests:
#DIFF=50 
DIFF=0 # for testing
j=1
last_job=$j # run one job

# if a command-line argument is supplied, provide it to j
if [ $# -gt 0 ] 
  then
    j=$1
    last_job=$j # loopSubmitJobs_v2.py
    #last_job=`expr $j + 199 ` # run up to 200 jobs at LLNL
    DIFF=53 
fi


echo "j:" $j
echo "last_job:" $last_job

#exit # debugging

#-------------------------------------------------------------------------------

export OUT_DIR=$nEXODataDir/${TYPE}_dcoeff${DIFF}
echo "OUTDIR:"
echo $OUT_DIR

mkdir -p $OUT_DIR/mc
mkdir -p $OUT_DIR/digitization_dcoeff$DIFF
mkdir -p $OUT_DIR/tier3
mkdir -p $OUT_DIR/log
mkdir -p $OUT_DIR/jobs_hold
mkdir -p $OUT_DIR/log

while test $j -le $last_job;
do
  echo $j

  sed -e "s/SEQNUM/$j/g" \
      -e "s/DIFF/$DIFF/g"  \
      -e "s/TYPE/$TYPE/g"  doall.script > $OUT_DIR/jobs_hold/doall${j}.script

  sed -e "s/SEQNUM/$j/g" \
      -e "s/TYPE/$TYPE/g"  $TYPE.in > $OUT_DIR/jobs_hold/run${j}.in

  sed -e "s/SEQNUM/$j/g"  \
      -e "s/TYPE/$TYPE/g"  \
      -e "s/SEED/10$j/g" mc.script > $OUT_DIR/jobs_hold/mc${j}.script

  sed -e "s/SEQNUM/$j/g"  \
      -e "s/TYPE/$TYPE/g"  \
      -e "s/DIFF/$DIFF/g"  \
      -e "s/SEED/10$j/g" digi.script > $OUT_DIR/jobs_hold/digi${j}.script

  chmod 755 $OUT_DIR/jobs_hold/mc${j}.script
  chmod 755 $OUT_DIR/jobs_hold/doall${j}.script
  chmod 755 $OUT_DIR/jobs_hold/digi${j}.script

  # SLAC:
  #bsub -R rhel60 -J mc$j -oo $OUT_DIR/log/blog_$DIFF.job${j} -q long -W 12:00 $OUT_DIR/jobs_hold/doall${j}.script
  #sleep 1.0

  # LLNL:
  msub -A afqn -m abe -V -N mc$j -o $OUT_DIR/log/blog_$DIFF.job${j} -j oe -q pbatch -l walltime=4:00:00 $OUT_DIR/jobs_hold/doall${j}.script

  #sleep 2.0
  #sleep 10

  j=`expr $j + 1 `
done


