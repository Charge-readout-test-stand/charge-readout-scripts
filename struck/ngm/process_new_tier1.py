"""
Produce tier1 from tier0, only if tier1 doesn't exist already
"""

import os
import sys
import toRoot


def process_files(filenames):

    for i, filename in enumerate(filenames):
        
        print "--> processing file %i of %i: %s" % (i, len(filenames), filename)

        basename = os.path.basename(filename) # drop the directory structure
        basename = os.path.splitext(basename)[0] # drop the extension
        tier1_name = "tier1_%s-ngm.root" % basename

        # if tier1 file doesn't exist, create it:
        if not os.path.isfile(tier1_name):
            toRoot.toRoot(filename) # do tier1 conversion
            

if __name__ == "__main__":

    process_files(sys.argv[1:])
