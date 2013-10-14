#!/usr/bin/python

# Script to grab module information from 
# top_level design, select signals,
# insert signals into test_bench


# command line Arguments:
# ----------------------------------------------------------------------------------------- #
# 																							#
# -o options 		= fgpa/isim 			 												#
# 																							#
# -p project_dir	= output destination for input signal (project directory) 				#
# -t top_level_file = file name of top level module											#
#																							#
#																							#
# -m module 		= vhdl module to plot (Demod,FIRFilter,IIRFilter)						#
# ----------------------------------------------------------------------------------------- #


# --------------------------------Example Commandline--------------------------------------------------- #
#																								 		 #
#	./testbenchGen -p ~/project_dir -t my_top.vhd									 					 # 
#																								 		 #
# --------------------------------Example Commandline--------------------------------------------------- #


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

def select_modules(top_level_file):
	match_ent = regex.compile('entity work.*')
	module_files = [regex.sub('^entity work\..*?')]

