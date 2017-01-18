# modified from /usr/gapps/nexo/setup_nEXO.sh

#-------------------------------------------------------------------------------
# Borax commands
#-------------------------------------------------------------------------------

# SET UP ROOT 5
export ROOTSYS=/usr/gapps/cern/root_v5.34.36/toss_3_x86_64/
source $ROOTSYS/bin/thisroot.sh


#-------------------------------------------------------------------------------
# old Aztec commands
#-------------------------------------------------------------------------------

# Use newish compiler
#source /usr/local/tools/dotkit/init.sh
#use gcc-4.9.3p 
#use python
#export CC=gcc
#export CXX=g++

#unset LD_LIBRARY_PATH
#export LD_LIBRARY_PATH=/usr/apps/gnu/4.9.3/lib64/ # 09 Sep 2016 -- per Samuele

# SET UP ROOT 5
#export ROOTSYS=/usr/gapps/cern/root_v5.34.03/chaos_5_x86_64
#source $ROOTSYS/bin/thisroot.sh

# SET UP GEANT4v10
#export G4INSTALL=/usr/gapps/cern/geant4.10.02/ # AGS 19 May 2016 -- per Samuele
#source $G4INSTALL/chaos_5_x86_64-install/bin/geant4.sh
#export Geant4_DIR=/usr/gapps/cern/geant4.10.02/chaos_5_x86_64-install/lib64/Geant4-10.2.0
#export G4_V10=1

# SET UP nEXO
#export PATH=/usr/gapps/nexo/nEXO_MC-build/:$PATH

# LOAD FULL PYTHON with additional packages
#use python
#source /usr/gapps/nexo/py-nEXO/bin/activate

# needed for VGM:
#source /usr/gapps/cern/CLHEP.2310/setup

# EXO-200 offline, needed for tier3 wfm processing with root 5:
#export EXOOUT=$HOME/software/offline/build
#source $EXOOUT/setup.sh

# EXO offline configure commands:
# ./configure --disable-viewer3d --disable-display --without-mysql
# --without-geant4 --disable-curl --without-exobinary CXXFLAGS=-std=c++11
# skips CLHEP, which is ok!

