
#-------------------------------------------------------------------------------
# Borax commands
#-------------------------------------------------------------------------------

# TBB -- for Jason N.'s NGM code
source  /g/g17/alexiss/software/tbb44_20160526oss/bin/tbbvars.sh intel64 linux auto_tbbroot

export ROOTSYS=/usr/gapps/cern/root_v6.08.02/toss_3_x86_64-install
source $ROOTSYS/bin/thisroot.sh

# Jason N.'s NGM code: 
export NGM=/g/g17/alexiss/software/ngm_sw/install_ngm_daq
export LD_LIBRARY_PATH=$NGM/lib:$LD_LIBRARY_PATH

unset EXOOUT
unset EXOLIB

#-------------------------------------------------------------------------------
# old Aztec commands
#-------------------------------------------------------------------------------


# FOR NGM code:

# TBB -- for Jason N.'s NGM code
#source  /g/g17/alexiss/software/tbb44_20160526oss/bin/tbbvars.sh intel64 linux auto_tbbroot

#export ROOTSYS=/usr/gapps/cern/root_v6.04.06/chaos_5_x86_64
#source $ROOTSYS/bin/thisroot.sh


# Jason N.'s NGM code: 
#export NGM=/g/g17/alexiss/software/ngm_sw/install_ngm_daq
#export LD_LIBRARY_PATH=$NGM/lib:$LD_LIBRARY_PATH

#unset EXOOUT
#unset EXOLIB
