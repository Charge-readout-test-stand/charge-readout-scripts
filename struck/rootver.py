import ROOT


print ROOT.module.__version__


import subprocess
root_version = subprocess.check_output(['root-config --version'],shell=True)
print root_version

