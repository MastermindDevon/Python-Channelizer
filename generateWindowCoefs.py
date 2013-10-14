#!/usr/bin/python
# generate coefficients from window function
# specify type of window
# write coefficients to file as unsigned integers

# command line Arguments:
# ----------------------------------------------------------------------------------------- #
# 																							#
# -p file_path 		= destination directory of coef_file 									#
# -l window_length 	= length of window 														#
# -w window 		= window function type (string)											#
# -n numPoints 		= number of data points in input 										#
#																							#
# ----------------------------------------------------------------------------------------- #


# --------------------------------Example Commandline-------------------------------------- #
#																							#
#	./generateWindowCoefs.py -l 35 -w 'boxcar' -n 4096 -p ~/project_dir 					# 
#																							#
# --------------------------------Example Commandline-------------------------------------- #



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

def generate_window_coefs(window,window_length,file_path,numPoints):
	print '\nGenerating {} window of length {}...'.format(window,window_length)

	# specify total bits and fractional bits for fixed point input:
	n_bits = 16
	n_frac_bits = 15
	
	if (window=='boxcar'):
		coefs=signal.boxcar(window_length)
	elif (window=='hamming'):
		coefs=signal.hamming(window_length)
	elif (window=='hann'):
		coefs=signal.hann(window_length)
	elif (window=='blackman'):
		coefs=signal.blackman(window_length)
	else:
		coefs=signal.boxcar(window_length)

	#Write out hex file for VHDL
	intData=np.zeros(numPoints)
	nintData=np.uint16(coefs*(2**n_bits-1))
	paddingFrac=4


	if (window_length==numPoints):
		intData=coefs
	else:	
		for i in range(len(coefs)):
			intData[int(numPoints/paddingFrac)+i]=coefs[i]
	

	intData = [ID*(2**n_bits-1) for ID in intData]
	intData=np.hstack([intData,intData])

	with open(str(file_path)+'/fpgaCoefData'+str(numPoints)+'_'+str(window)+'.txt','w') as FID:
		FID.write('\n'.join(['{}'.format(int(x)) for x in intData]))

	with open(str(file_path)+'/macCoefData'+str(numPoints)+'_'+str(window)+'.txt','w') as FID:
		FID.write('signal myCoef : input_array32 :=(')
		FID.write(','.join(['x"{0:08X}"'.format(int(x)) for x in intData])+');')

def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-w','--window',dest='window',type=str,help='Type of window function (boxcar,hamming,hann,blackman)\ndefault=boxcar')
   parser.add_argument('-l','--win_length',dest='winLen',type=int,help='Length of window function')
   parser.add_argument('-n','--numPoints',dest='numPoints',type=int,help='Number of points')
   parser.add_argument('-p','--file_path',dest='fpath',type=str,help='Project file path')
   args = parser.parse_args()

   # function call in main:
   generate_window_coefs(args.window,args.winLen,args.fpath,args.numPoints)
   # Display inputs:
   print 'Window chosen for signal of {} points'.format(args.numPoints)
   print 'Writing results to {} directory...\n'.format(str(args.fpath))
if __name__ == "__main__":
   main(sys.argv[1:])
