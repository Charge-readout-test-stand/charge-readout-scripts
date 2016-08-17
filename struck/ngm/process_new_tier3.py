
import os
import sys

from struck import generateTier3Files


def process_files(filenames):

    for i, filename in enumerate(filenames):
        
        print "--> processing file %i of %i: %s" % (i, len(filenames), filename)

        basename = os.path.basename(filename) # drop the directory structure
        basename = "_".join(basename.split("_")[1:])  # drop the tier1_
        tier3_name = "tier3_%s" % basename
        print tier3_name

        # if tier3 file doesn't exist, create it:
        if os.path.isfile(tier3_name):
            print "==> skipping"

        else:
            print "processing!"
            generateTier3Files.process_file(filename) # do tier1 conversion
            

if __name__ == "__main__":

    process_files(sys.argv[1:])
