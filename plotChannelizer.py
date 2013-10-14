#!/usr/bin/python

# command line Arguments:
# ----------------------------------------------------------------------------------------- #
# 																							#
# -i inputFreq 		= input frequency (Hz) 													#
# -s samplingFreq 	= sampling rate (Samples/second) 										#
# 																							#
# -a amplitude		= amplitude fit parameter 												#
# -p phase 			= phase shift fit parameter 											#
# -o dc_offset 		= dc offset fit parameter 												#
# 																							#
# -d decimFactor 	= decimation factor of FIR filter 										#
# -l project_dir	= output destination for input signal (project directory) 				#
#																							#
# ----------------------------------------------------------------------------------------- #


# --------------------------------Example Commandline-------------------------------------- #
#																							#
#	./plotChannelizer.py -i 10e06 -s 500e06 -a 1 -p 3.14159 -o 5 -d 4 -l ~/project_dir		# 
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


#--------------------------------------------------------------------------------------------#
#					Plot single frequency input signal 		 								 #
#--------------------------------------------------------------------------------------------#

def plot_complex_signal(inputFreq,samplingFreq,p0,p1,p2,decimFactor,project_dir):
	inputFreq=inputFreq/1e06
	# regex substitute:           ('pattern','replace',string)
	project_dir_stripped=regex.sub('^.*\/','',project_dir)

	print '\nReading {}/outputRe{}MHz.dat from project directory: {}'.format(project_dir_stripped,inputFreq,project_dir)

	timeStep=1/samplingFreq

	outputDataRe=np.genfromtxt(str(project_dir)+'/'+str(project_dir_stripped)+'Reoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int16)
	outputDataIm=np.genfromtxt(str(project_dir)+'/'+str(project_dir_stripped)+'Imoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int16)
	outputData=outputDataRe + 1j * outputDataIm
	outputTpts=np.arange(0,len(outputData)*timeStep,timeStep)


	title='Project: '+str(project_dir_stripped)
	fig00=plt.figure(17)
	fig00.suptitle(str(title))

	cosoutput=np.genfromtxt(str(project_dir)+'/cosoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int16)
	cosTpts=np.arange(0,len(cosoutput)*timeStep,timeStep)

	plt.subplot(3,1,1)
	plt.title(str(inputFreq)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq)+' MHz Output')
	plt.plot(cosTpts,cosoutput)
	plt.xlabel('Time (s)')
	plt.ylabel('Magnitude')

	# plot the output and cooresponding fit
	plt.subplot(3,1,2)
	plt.title(str(inputFreq)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq)+' MHz Output')
	plt.xlabel('Time (s)')
	plt.ylabel('Magnitude')
	plt.plot(outputTpts,np.real(outputData),'r',label='Filtered Output')
	plt.plot(cosTpts,p0*np.cos(2*np.pi*inputFreq*cosTpts*decimFactor+p1)+p2,'b',label='Fitted Output')
	plt.legend(loc='lower right')

	# plot the output and cooresponding fit
	plt.subplot(3,1,3)
	plt.title(str(inputFreq)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq)+' MHz Output')
	plt.xlabel('Time (s)')
	plt.ylabel('Magnitude')
	plt.plot(outputTpts,np.imag(outputData),'r',label='Filtered Output')
	plt.plot(cosTpts,p0*np.cos(2*np.pi*inputFreq*cosTpts*decimFactor+p1)+p2,'b',label='Fitted Output')
	plt.legend(loc='lower right')
	plt.show()

	plt.close()

def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-s','--samplingFreq',dest='sfreq',type=float,help='sampling frequency in Hz')
   parser.add_argument('-i','--inputFreq',dest='ifreq',type=float,help='frequency for cos wave in MHz')
   parser.add_argument('-d','--decimFactor',dest='decimFactor',type=int,help='Decimation Factor of Polyphase filter')
   parser.add_argument('-l','--project_dir',dest='pdir',type=str,help='project file path')
   parser.add_argument('-a','--amplitude',dest='amp',type=float,help='amplitude fit parameter')
   parser.add_argument('-p','--phase',dest='phase',type=float,help='phase shift fit parameter')
   parser.add_argument('-o','--dc_offset',dest='dc',type=float,help='dc offset fit parameter')
   args = parser.parse_args()

   # function call in main:
   plot_complex_signal(args.ifreq,args.sfreq,args.amp,args.phase,args.dc,args.decimFactor,args.pdir)
   # Display inputs:
   if (args.cfreq != '' and args.sfreq != ''):
   	print '\nCosine frequency: {} MHz \nSampling frequency: {} MHz'.format(args.cfreq,args.sfreq/1e06)
   	print 'Writing results to {} directory...\n'.format(str(args.project_dir))
if __name__ == "__main__":
   main(sys.argv[1:])