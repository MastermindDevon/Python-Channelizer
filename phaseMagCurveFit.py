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
# 
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
#					Amplitude and Phase Response Plotting 									 #
#--------------------------------------------------------------------------------------------#

def plotMagPhase(fileSelect,sweepfreq,p0,p1,p2,nyq):
	nsweepfreq=[sw/nyq for sw in sweepfreq]

	fig0=plt.figure(0)
	fig0.suptitle('Phase Shift-Frequency Dependence of '+str(fileSelect)+' files')

	plt.subplot(211)
	plt.title('Magnitude Response --> Free Parameter (0)')
	plt.xlabel('Frequencies (Hz)')
	plt.ylabel('Free Parameter ')
	plt.xlim(0,1)
	plt.ylim(-75,10)
	plt.plot(nsweepfreq,20*np.log10(p0),'g.-')

	plt.subplot(212)
	plt.title('Phase Response --> Free Parameter (1)')
	plt.xlabel('Frequencies (Hz)')
	plt.ylabel('Free Parameter ')
	plt.plot(nsweepfreq,np.unwrap(p1),'r.-')
	plt.show()

#--------------------------------------------------------------------------------------------#
# 				Plot output of signal processing chain 										 #
#--------------------------------------------------------------------------------------------#

def plotTotalChannelizer(cosFreq,samplingFreq,numPoints,numTaps,decimFactor,fileSelect,project_dir,module):
	# regex substitute:  ('pattern','replace',string)
	project_dir=regex.sub('\/$','',project_dir)
	project_dir_stripped=regex.sub('^.*\/','',project_dir)
	
	timeStep = 1.0/samplingFreq
	nyq = samplingFreq/2.0

	sweepfreq = [i for i in np.arange(5e05,125e05,5e05)]
	sweepfreq = [float(i) for i in sweepfreq]
	myString=[str(int(i/pow(10,5))) for i in sweepfreq]

	# iSim signals from file writer:
	demodoutputRe=[np.genfromtxt(str(project_dir)+'/dataDemodReoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	demodoutputIm=[np.genfromtxt(str(project_dir)+'/dataDemodImoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	firoutput=[np.genfromtxt(str(project_dir)+'/datatoDemodTopoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	inputCos = [np.genfromtxt(str(project_dir)+'/cosoutput'+str(myString[i])+'MHz.dat',dtype=str) for i in range(len(sweepfreq))]
	outputRe = [np.genfromtxt(str(project_dir)+'/polyDecimDemodFilterReoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	outputIm = [np.genfromtxt(str(project_dir)+'/polyDecimDemodFilterImoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]

	print 'Length of input data: {}\n'.format(len(inputCos[0]))

	# convert to fixed point
	print 'FixedPoint Value: {}\n'.format(np.float(int(inputCos[0][10]))*pow(2,-15))

	newCos = [[0]*len(sweepfreq)*len(ic) for ic in inputCos]
	newFirOutput = [[0]*len(fi) for fi in firoutput]
	
	newdemodRe = [[0]*len(sweepfreq)*len(re) for re in demodoutputRe]
	newdemodIm = [[0]*len(sweepfreq)*len(im) for im in demodoutputIm]
	demod_phasor = [[0]*len(sweepfreq)*len(re) for re in demodoutputRe]
	
	newRe = [[0]*len(sweepfreq)*len(re) for re in outputRe]
	newIm = [[0]*len(sweepfreq)*len(im) for im in outputIm]
	phasor = [[0]*len(sweepfreq)*len(re) for re in outputRe]

	# cosine input signal:
	for i in range(len(sweepfreq)):
		for j in range(len(inputCos[i])):
			newCos[i][j]=np.float(int(inputCos[i][j]))

	# fir output signal:
	for i in range(len(sweepfreq)):
		for j in range(len(firoutput[i])):
			newFirOutput[i][j]=np.float(int(firoutput[i][j]))*pow(2,-4)

	# demodulator real signal:
	for i in range(len(sweepfreq)):
		for j in range(len(demodoutputRe[i])):
			newdemodRe[i][j]=np.float(demodoutputRe[i][j])

	# demodulator imag signal:
	for i in range(len(sweepfreq)):
		for j in range(len(demodoutputIm[i])):
			newdemodIm[i][j]=np.float(demodoutputIm[i][j]) 

	for i in range(len(sweepfreq)):
		for j in range(len(newdemodRe[i])):
			demod_phasor[i][j] = newdemodRe[i][j] + 1j * newdemodIm[i][j]	

	# output phasor signals:
	for i in range(len(sweepfreq)):
		for j in range(len(outputRe[i])):
			newRe[i][j]=np.float(int(outputRe[i][j]))

	for i in range(len(sweepfreq)):
		for j in range(len(outputIm[i])):
			newIm[i][j]=np.float(int(outputIm[i][j]))

	for i in range(len(sweepfreq)):
		for j in range(len(outputRe[i])):
			phasor[i][j] = newRe[i][j] + 1j * newIm[i][j]


	# firoutput = [fi[7:len(fi)] for fi in firoutput]

	# time vectors:

	# demod_phasor = [dp[50:244] for dp in demod_phasor]

	# newFirOutput = [fi[50:220] for fi in newFirOutput]


	demodTpts = [np.arange(0,len(dp)*timeStep,timeStep) for dp in demod_phasor]
	cosTpts = [np.arange(0,len(ic)*timeStep,timeStep) for ic in inputCos]
	phasorTpts = [np.arange(0,len(ph)*timeStep,timeStep) for ph in phasor]
	outputRePts = [np.arange(0,len(re)*timeStep,timeStep) for re in newRe]
	firTpts=[np.arange(0,len(fi)*timeStep,timeStep) for fi in newFirOutput]

	phasor = [np.real(ph) for ph in phasor]


	# plot polyphase fir filter results:
	if(module=='firFilterPoly'):
		p00,p11,p22 = phaseMagFit(sweepfreq,firTpts,newFirOutput,decimFactor)
		plotMagPhase(fileSelect,sweepfreq,p00,p11,p22,nyq)	
		# sweepingPlot(sweepfreq,firTpts,newFirOutput,p00,p11,decimFactor,'FIR Filter',False)

	if(module=='digitalDemod'):
		p000,p111,p222 = phaseMagFit(sweepfreq,demodTpts,np.real(demod_phasor),decimFactor)	
		plotMagPhase(fileSelect,sweepfreq,p000,p111,p222,nyq)
		# sweepingPlot(sweepfreq,demodTpts,demod_phasor,p000,p111,p222,decimFactor,'Demodulated Phasor',True)

	if(module=='top'):
		re_p0,re_p1,re_p2 = phaseMagFit(sweepfreq,phasorTpts,np.real(phasor),1)
		plotMagPhase(fileSelect,sweepfreq,re_p0,re_p1,re_p2,nyq
		# sweepingPlot(sweepfreq,phasorTpts,phasor,re_p0,re_p1,re_p2,decimFactor,'Total Channelizer',True)
			
	

#--------------------------------------------------------------------------------------------#
#						Amplitude and Phase Response curve fitting							 #
#--------------------------------------------------------------------------------------------#

def phaseMagFit(freq,timePts,data,decimFactor):
	def model(x,p0,p1,p2):
	 # p0: amplitude
	 # p1: phase shift
	 # p2: DC-Bias
	 return p0*np.cos(2*np.pi*x[0]*x[1]*decimFactor+p1)+p2

	# optimal parameters populated by curve_fit():
	popt = [0]*len(freq)
	pcov = [0]*len(freq)

	print '\nOptimal parameters: \n'
	x = [(i, j) for i,j in zip(timePts,freq)]

	for i in range(len(freq)):
		popt[i], pcov[i] = curve_fit(model,x[i],data[i])
		print freq[i]/1e06,' MHz:\t', popt[i]

	p0 = [0]*len(popt)
	p1 = [0]*len(popt)
	p2 = [0]*len(popt)
	for i in range(len(popt)):
		p0[i] = abs(popt[i][0])
		p1[i] = (popt[i][1] + np.pi if popt[i][0] < 0 else popt[i][1]) % (2*np.pi)
		p2[i] = popt[i][2]
	return [p0,p1,p2]

def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-n','--numPoints',dest='numPoints',type=int,help='Number of numPoints')
   parser.add_argument('-s','--samplingFreq',dest='sfreq',type=float,help='sampling frequency in Hz')
   parser.add_argument('-c','--cosFreq',dest='cfreq',type=float,help='frequency for cos wave in MHz')
   parser.add_argument('-d','--decimFactor',dest='decimFactor',type=int,help='Decimation Factor of Polyphase filter')
   parser.add_argument('-p','--file_path',dest='fpath',type=str,help='project file path')

   args = parser.parse_args()
   # function call in main:

   # Display inputs:

if __name__ == "__main__":
   main(sys.argv[1:])