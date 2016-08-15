
import os
import sys
import toRoot


def process_files(filenames):

    for filename in filenames:
        
        print "--> processing", filename

        basename = os.path.basename(filename) # drop the directory structure
        basename = os.path.splitext(basename)[0] # drop the extension
        tier1_name = "tier1_%s-ngm.root" % basename

        # if tier1 file doesn't exist, create it:
        if not os.path.isfile(tier1_name):
            toRoot.toRoot(filename) # do tier1 conversion
            

if __name__ == "__main__":

    process_files(sys.argv[1:])
