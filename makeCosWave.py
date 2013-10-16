#!/usr/bin/python
# Input Sinusoid Signal Generator

# command line Arguments:
# ----------------------------------------------------------------------------------------- #
# 																							#
# 																							#
# -c cosFreq 		= input frequency (MHz) 												#
# -s samplingFreq 	= sampling rate (Hz) 													#
# -r resolution 	= frequency resolution in Hz 											#
# 																							#
# -n numPoints 		= number of data points in input 										#
# -d decimFactor 	= decimation factor of FIR filter 										#
# -p file_path 		= output destination for input signal (project directory) 				#
# 																							#
# -z zero_pad 		= bool to enable/disable input zero padding 							#
# -g gauss 			= gaussian noise distribution (gauss/none)								#
#																							#
# ----------------------------------------------------------------------------------------- #


# --------------------------------Example Commandline-------------------------------------- #
#																							#
#	./makeCosWave.py -c 10 -s 500e06 -n 2048 -d 4 -p ~/project_dir -r 1e05 -z yes -g gauss	# 
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

#--------------------------------------------------------------------------------------------#
#				Conversion Functions to Fixed Point Representation 							 #
#--------------------------------------------------------------------------------------------#

def binaryToFixedPoint(strVal,totBits,fracBits):
	binVal = int(strVal,2)
	fixedVal = fp.FXnum(binVal, fp.FXfamily(n_bits=totBits))
	fixedVal.family.integer_bits=totBits-fracBits
	fixedVal.family.fraction_bits=fracBits
	return fixedVal

def intToFixedPoint(intVal,totBits,fracBits):
	fixedVal = fp.FXnum(intVal, fp.FXfamily(n_bits=totBits))
	fixedVal.family.integer_bits=totBits-fracBits
	fixedVal.family.fraction_bits=fracBits
	return fixedVal

#--------------------------------------------------------------------------------------------#
#				Generate test inputs for iSim in x"_ _ _ _" format 							 #
#--------------------------------------------------------------------------------------------#

def make_cos_wave(cosFreq, samplingFreq, numPoints, decimFactor, file_path, resolution, zero_pad, gauss):
	cosFreq = cosFreq*1e06
	timeStep = 1.0/samplingFreq
	timePts = np.arange(0,numPoints*timeStep,timeStep) 
	cosData = np.cos(2*np.pi*cosFreq*timePts) 
	sinData = np.sin(2*np.pi*cosFreq*timePts)
	phaseInc = int(np.floor((cosFreq/(samplingFreq/decimFactor))*pow(2,16)))

	# specify total bits and fractional bits for fixed point input:
	n_bits = 16
	n_frac_bits = 15

	paddingFrac=4

	# square pulse signal
	pulseData = np.zeros(numPoints)

	pulseData[(numPoints/4):(numPoints-(numPoints/4))]=0.25
	pulseData = np.hstack([pulseData,pulseData])
	intPulse = np.uint16(pulseData*(2**n_bits-1)) 

	# Write out hex file for VHDL
	# intCosData = np.uint16(cosData*(pow(2,n_bits-1)-1))
	intCosData = np.uint16(cosData*(pow(2,n_bits-1)-1))
	intSinData = np.uint16(sinData*(pow(2,n_bits-1)-1))
	fixedData = [intToFixedPoint(int(i),n_bits,n_frac_bits) for i in intCosData]
	
	# pad data with zeros for pulse input
	if (zero_pad=='yes'):
		print '\nPadding input signal with zeros...'
		fixedData=[ 0 if i<(len(fixedData)/paddingFrac) else 0 if i>(len(fixedData)-len(fixedData)/paddingFrac) else fixedData[i] for i in range(len(fixedData)) ]
		intSinData[0:len(intSinData)/paddingFrac]=0
		intSinData[(len(intSinData)-len(intSinData)/paddingFrac):len(intSinData)]=0
		intCosData[0:len(intCosData)/paddingFrac]=0
		intCosData[(len(intCosData)-len(intCosData)/paddingFrac):len(intCosData)]=0
		intCosData = np.hstack([intCosData,intSinData])
		if (gauss=='gauss'):
			print 'Applying Gaussian Noise to input...'
			gauss_noise=np.random.normal(0,1,numPoints)
			gauss_noise=np.uint16(gauss_noise*(pow(2,n_bits-1)-1))
			intCosData[len(intCosData)/paddingFrac:(len(intCosData)-len(intCosData)/paddingFrac)]=intCosData[len(intCosData)/paddingFrac:(len(intCosData)-len(intCosData)/paddingFrac)]+gauss_noise
		# multi_pulse=1	
		# if (multi_pulse>1):
		# 	print 'Generating {} pusles to the processing chain...'.format(multi_pulse)
		# 	intCosData = [ np.hstack(intCosData) for i in range(multi_pulse)]


	# fixed point representation with n_bits, n_frac_bits
	with open(str(file_path)+'/iSimDatafxp'+str(numPoints)+'.txt','w') as FID:
	 	FID.write('signal myCosine : input_array :=(')
	 	FID.write(','.join(['x"{0:04X}"'.format(int(x)) for x in fixedData])+');')
	 	
	# 16-bit unsigned integer representation, current default:
	with open(str(file_path)+'/iSimData'+str(numPoints)+'.txt','w') as FID:
		FID.write('signal myCosine : input_array :=(')
		FID.write(','.join(['x"{0:04X}"'.format(int(x)) for x in intCosData])+');')

	# 16-bit unsigned integer representation, current default, opal kelly data:
	with open(str(file_path)+'/fpgaData'+str(numPoints)+'.txt','w') as FID:
			FID.write('\n'.join(['{}'.format(int(x)) for x in intCosData]))

	# square pulse, dc term:
	with open(str(file_path)+'/pulseData'+str(numPoints)+'.txt','w') as FID:
		FID.write('signal myCosine : input_array :=(')
		FID.write(','.join(['x"{0:04X}"'.format(int(x)) for x in intPulse])+');')		

	with open(str(file_path)+'/phaseInc.txt','w') as pfid:
		pfid.write('phaseInc <= '+'x"{0:04X}"'.format(phaseInc)+'; wait until (rising_edge(clk));')

	print '\nPhase increment: x"{0:04X}"'.format(phaseInc)

	
def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-n','--numPoints',dest='numPoints',type=int,help='Number of numPoints')
   parser.add_argument('-s','--samplingFreq',dest='sfreq',type=float,help='sampling frequency in Hz')
   parser.add_argument('-c','--cosFreq',dest='cfreq',type=float,help='frequency for cos wave in MHz')
   parser.add_argument('-d','--decimFactor',dest='decimFactor',type=int,help='Decimation Factor of Polyphase filter')
   parser.add_argument('-p','--file_path',dest='fpath',type=str,help='project file path')
   parser.add_argument('-r','--resolution',dest='rez',type=float,help='frequency resolution in Hz')
   parser.add_argument('-z','--zero_pad',dest='zpad',type=str,help='zero padding on/off (yes/no)')
   parser.add_argument('-g','--gaussian',dest='gauss',type=str,help='use gaussian noise (gauss/no)')
   args = parser.parse_args()

   # function call in main:
   make_cos_wave(args.cfreq,args.sfreq,args.numPoints,args.decimFactor,args.fpath,args.rez,args.zpad,args.gauss)
   # Display inputs:
   if (args.cfreq != '' and args.sfreq != ''):
   	print 'Cosine frequency: {} MHz \nSampling frequency: {} MHz'.format(args.cfreq,args.sfreq/1e06)
   	print 'Frequency resolution: {} Hz'.format(args.rez)
   	print 'Writing results to {} directory...\n'.format(str(args.fpath))
if __name__ == "__main__":
   main(sys.argv[1:])
