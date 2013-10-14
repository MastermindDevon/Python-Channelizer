#!/usr/bin/python

# Shelve this for now, come back if time permits 
# 9/20/13

# Regex to parse top level module and generate plotting
# Automated testing for modules with time domain signals
# Updates testbench to output desired signals

import sys
import itertools
import argparse
import numpy as np
import math 
import matplotlib.pyplot as plt
import matplotlib.mlab as mylab
import csv
import Verilog_VCD
from scipy import signal
from scipy.optimize import curve_fit
import FixedPoint as fp
import re as regex


# parse top level module and obtain the module names:

def get_module_names(project_dir,top_level):
	# regex substitute:           ('pattern','replace',string)
	project_dir_stripped=regex.sub('^.*\/','',project_dir)
	top=str(project_dir)+'/'+str(top_level)

	modules=regex.match('\: entity\g',top)