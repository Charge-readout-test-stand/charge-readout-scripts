import os,sys
import glob


file_list = glob.glob("log_tier3*.out")

script = open("sub_failed.sh","w")
runcmd = "python submitNewTier1And3Jobs.py"

deletecmd = ""

for gfile in file_list:
    if ("Exceed" in open(gfile).read()) or ("Error in <TBasket::ReadBasketBuffers>" in open(gfile).read()):
        bname = os.path.basename(gfile)
        path  = os.path.dirname(gfile)
        tier1_name = bname.replace("log_tier3_","")
        tier1_name = tier1_name.replace(".out",".root")
        tier1_name = os.path.join("../tier1", tier1_name)
        tier3_name = tier1_name.replace("tier1","tier3") 
        
        tier0_name = os.path.basename(tier1_name)
        tier0_name = tier0_name.replace("tier1_", "")
        tier0_name = tier0_name.replace("-ngm.root", ".bin")
        tier0_name  = os.path.join("../tier0", tier0_name)
        
        print os.path.isfile(tier0_name), tier0_name
        print os.path.isfile(tier1_name), tier1_name
        print os.path.isfile(tier3_name), tier3_name

        #This will remove the bad files
        #if os.path.isfile(tier1_name):
        #    os.remove(tier1_name)
        #if os.path.isfile(tier3_name):
        #    os.remove(tier3_name)
        
        #script.write(" %s " % tier0_name)
        runcmd += " %s  " % tier0_name
        deletecmd += "rm -f %s \n" % gfile
        deletecmd += "rm -f %s \n" % tier1_name
        deletecmd += "rm -f %s \n" % tier3_name

file_list = glob.glob("out*.out")
for gfile in file_list:
    if "slurmstepd: error:" in open(gfile).read():
        bname = os.path.basename(gfile)
        tier1_name = bname.replace("out_","")
        tier1_name = tier1_name.replace(".out", ".root")
        tier0_name = tier1_name.replace("tier1_","")
        tier0_name = tier0_name.replace("-ngm.root",".bin")
        tier0_name = os.path.join("../tier0/",tier0_name)
        tier1_name = os.path.join("../tier1/",tier1_name)
        tier3_name = tier1_name.replace("tier1","tier3")
        
        print os.path.isfile(tier0_name), tier0_name
        print os.path.isfile(tier1_name), tier1_name
        print os.path.isfile(tier3_name), tier3_name
        
        #script.write(" %s " % tier0_name)
        runcmd += " %s  " % tier0_name
        deletecmd += "rm -f %s \n" % gfile
        deletecmd += "rm -f %s \n" % tier1_name
        deletecmd += "rm -f %s \n" % tier3_name

script.write("\n")
script.write(deletecmd)
script.write("\n")
script.write(runcmd)
script.write("\n")
script.close()

        
        
        
    
