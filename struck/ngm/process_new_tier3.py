
import os
import sys
import inspect
import commands

from struck import generateTier3Files


def process_files(filenames):

    script_name = "%s.py" % os.path.splitext(inspect.getfile(generateTier3Files))[0]

    for i, filename in enumerate(filenames):
        
        print "--> processing file %i of %i: %s" % (i, len(filenames), filename)

        basename = os.path.basename(filename) # drop the directory structure
        basename = "_".join(basename.split("_")[1:])  # drop the tier1_
        tier3_name = "tier3_%s" % basename

        # if tier3 file doesn't exist, create it:
        if os.path.isfile(tier3_name):
            print "==> skipping"

        else:
            filename = os.path.abspath(filename)
            log_name = "log_%s.out" % os.path.splitext(tier3_name)[0]
            print "processing!"
            cmd = "nice python %s %s > %s 2>&1" % (script_name, filename, log_name)
            print cmd
            output = commands.getstatusoutput(cmd)
            if output[0] != 0:
                print output[1]

            # this still leaks memory
            #generateTier3Files.process_file(filename) # do tier1 conversion
            

if __name__ == "__main__":

    process_files(sys.argv[1:])
