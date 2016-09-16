"""
This script calls takeData.takeData() in a loop. 
"""

import time
import takeData

# take struck data in a loop!
takeData.takeData(doLoop=True,n_hours=50.0) # set up the digitizer, take data

