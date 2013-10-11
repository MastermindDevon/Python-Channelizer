#!/usr/bin/python

# command line Arguments:
# ----------------------------------------------------------------------------------------- #
# 																							#
# -i inputFreq 		= input frequency (Hz) 													#
# -s samplingFreq 	= sampling rate (Samples/second) 										#
# 																							#
# -o options 		= fgpa/isim 			 												#
# 																							#
# -d decimFactor 	= decimation factor of FIR filter 										#
# -l project_dir	= output destination for input signal (project directory) 				#
#																							#
# -m module 		= vhdl module to plot (Demod,FIRFilter,IIRFilter,MUL)						#
# ----------------------------------------------------------------------------------------- #


# --------------------------------Example Commandline--------------------------------------------------- #
#																								 		 #
#	./plotComplexSignal.py -i 10e06 -s 500e06 -d 4 -p ~/project_dir -m module		 					 # 
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


#--------------------------------------------------------------------------------------------#
#					Plot single frequency input signal 		 								 #
#--------------------------------------------------------------------------------------------#

def plot_complex_signal(inputFreq,samplingFreq,decimFactor,project_dir,module,options):
	inputFreq=inputFreq/1e06
	# regex substitute:  ('pattern','replace',string)
	project_dir=regex.sub('\/$','',project_dir)
	project_dir_stripped=regex.sub('^.*\/','',project_dir)

	nyq = samplingFreq/2

	print '\nReading {}/outputRe{}MHz.dat from project directory: {}'.format(project_dir_stripped,int(inputFreq),project_dir)

	timeStep=1/samplingFreq

	cosoutput=np.genfromtxt(str(project_dir)+'/cosoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)
	# cosoutputIm=np.genfromtxt(str(project_dir)+'/cosoutputIm'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)
	# cosoutput=cosoutputRe + 1j * cosoutputIm
	cosTpts=np.arange(0,len(cosoutput)*timeStep,timeStep)

	# plot demodulator signals:
	if (module=='Demod'):
		decim_nyq=(samplingFreq/4)/2
		print 'Nyquist Frequency for Demodulator: {} MHz'.format(decim_nyq/1e06)

		inData=np.genfromtxt(str(project_dir)+'/cosoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int16)
		demodDataRe=np.genfromtxt(str(project_dir)+'/data'+str(module)+'Reoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)
		demodDataIm=np.genfromtxt(str(project_dir)+'/data'+str(module)+'Imoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)


		# compute frequency domain signals:
		if(options=='fpga'):
			demodPhasor=np.genfromtxt(str(project_dir)+'/fpgaDemod'+str(int(inputFreq))+'MHz.dat',np.int32)
			demodTpts=np.arange(0,len(demodData)*timeStep,timeStep)
			print 'Demodulator values from {}...'.format(options)
		else: 
			demodPhasor=demodDataRe + 1j * demodDataIm
			inTpts=np.arange(0,len(inData)*1/100e06,1/100e06)
			demodTpts=timeStep*np.arange(0,len(demodDataRe))
		
		demodfft=np.fft.fft(demodPhasor)
		demodfftfreq=np.fft.fftfreq(len(demodfft),d=timeStep*4)

		title='Project: '+str(project_dir_stripped)
		fig000=plt.figure(1)
		fig000.suptitle(str(title))

		# time domain signals:
		plt.subplot(3,1,1)
		plt.title('Real Output from Multiplier')
		plt.plot(demodTpts,demodDataRe*pow(2,-19))
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')

		plt.subplot(3,1,2)
		plt.title('Imag Output from Multiplier')
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude [Im]')
		plt.plot(demodTpts,demodDataIm*pow(2,-19))

		# frequency domain signals:
		plt.subplot(3,1,3)
		plt.title('Frequency Response of Demodulator')
		plt.xlabel('Normalized Frequency')
		plt.ylabel('Magnitude')
		plt.plot(demodfftfreq/np.max(demodfftfreq),np.abs(demodfft)/np.max(np.abs(demodfft)))
		plt.xlim((0,1))

		fig000.savefig(str(project_dir)+'/'+str(project_dir_stripped)+'_'+str(module)+'.pdf')

	# plot iir filter input/output:
	if (module=='IIRFilter'):
		inData=np.genfromtxt(str(project_dir)+'/cosoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int16)

		iirDataRe=np.genfromtxt(str(project_dir)+'/data'+str(module)+'Reoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)
		iirDataIm=np.genfromtxt(str(project_dir)+'/data'+str(module)+'Imoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)

		iirPhasor = iirDataRe + 1j * iirDataIm

		inTpts=timeStep*np.arange(0,len(inData))
		iirtpts=np.arange(0,len(iirPhasor)*1/100e06,1/100e06)

		iirPhasor=[ir*pow(2,-14) for ir in iirPhasor]

		fig0 = plt.figure(1)
		fig0.suptitle('Project:'+str(project_dir_stripped))

		plt.subplot(211)
		plt.title('Input Pulse')
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')
		plt.plot(inTpts,inData,'g',label='Input Pulse')

		plt.subplot(212)
		plt.title('IIR Filter Results')
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')
		plt.plot(iirtpts,np.abs(iirPhasor),'r',label='Real Filter Output')
		plt.plot(iirtpts,np.angle(iirPhasor)*(180/np.pi),'b',label='Imag Filter Output')
		plt.legend(loc='lower right')

		plt.show()
		fig0.savefig(str(project_dir)+'/'+str(project_dir_stripped)+'_'+str(module)+'.pdf')

	# plot fir filter input/output:
	if (module=='FIRFilter'):
		inData=np.genfromtxt(str(project_dir)+'/cosoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int16)
		if(options=='fpga'):
			print 'FIRFilter values from {}...'.format(options)
			FIRData=np.genfromtxt(str(project_dir)+'/fpgaFIRFilter'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)
		else:
			FIRData=np.genfromtxt(str(project_dir)+'/dataFrom'+str(module)+'output'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)

		inTpts=np.arange(0,len(inData)*1/100e06,1/100e06)
		FIRtpts=np.arange(0,len(FIRData)*1/100e06,1/100e06)

		inData=[(co*pow(2,-15)) for co in inData]
		FIRData=[ir*pow(2,-15) for ir in FIRData]

		fig0 = plt.figure(1)
		fig0.suptitle('Project:'+str(project_dir_stripped))

		plt.title('Input Pulse and FIR Filter Results')
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')
		plt.plot(inTpts,inData,'r',label='pulse input')
		plt.plot(FIRtpts,FIRData,'b',label='filter output')
		plt.legend(loc='lower right')

		plt.show()
		fig0.savefig(str(project_dir)+'/'+str(project_dir_stripped)+'_'+str(module)+'.pdf')

	if (module=='MUL'):
		mulDataRe=np.genfromtxt(str(project_dir)+'/data'+str(module)+'Reoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int64)
		mulDataIm=np.genfromtxt(str(project_dir)+'/data'+str(module)+'Imoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int64)
		mulTpts=timeStep*np.arange(0,len(mulDataRe))

		window=np.genfromtxt(str(project_dir)+'/data'+str(module)+'windowoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int32)
		windowTpts=timeStep*np.arange(0,len(window))

		print 'Window length: {} signal length: {}'.format(len(window),len(mulTpts))

		title='Project: '+str(project_dir_stripped)
		fig000=plt.figure(1)
		fig000.suptitle(str(title))

		plt.subplot(4,1,1)
		plt.title(str(inputFreq)+' MHz Input Cosine Wave')
		plt.plot(cosTpts,np.real(cosoutput)*pow(2,-17))
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')

		plt.subplot(4,1,2)
		plt.title('Window Function')
		plt.plot(windowTpts,window*pow(2,-15))
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')

		plt.subplot(4,1,3)
		plt.title('Real Output from Multiplier')
		plt.plot(mulTpts,mulDataRe*pow(2,-28))
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')

		# plot the output and cooresponding fit
		plt.subplot(4,1,4)
		plt.title('Imag Output from Multiplier')
		plt.xlabel('Time (s)')
		plt.ylabel('Magnitude')
		plt.plot(mulTpts,mulDataIm*pow(2,-28))
		fig000.savefig(str(project_dir)+'/'+str(project_dir_stripped)+'_'+str(module)+'.pdf')			

	outputDataReMSB=np.genfromtxt(str(project_dir)+'/'+str(project_dir_stripped)+'ReMSBoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int64)
	outputDataReLSB=np.genfromtxt(str(project_dir)+'/'+str(project_dir_stripped)+'ReLSBoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.uint32)
	outputDataImMSB=np.genfromtxt(str(project_dir)+'/'+str(project_dir_stripped)+'ImMSBoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.int64)
	outputDataImLSB=np.genfromtxt(str(project_dir)+'/'+str(project_dir_stripped)+'ImLSBoutput'+str(int(inputFreq))+'MHz.dat',dtype=np.uint32)

	if(options=='fpga'):
		print 'Reading {} results from file...'.format(options)
		outputDataRe=np.genfromtxt(str(project_dir)+'/fpgaOutputRe'+str(int(inputFreq))+'MHz.dat',dtype=np.int64)
		outputDataIm=np.genfromtxt(str(project_dir)+'/fpgaOutputIm'+str(int(inputFreq))+'MHz.dat',dtype=np.int64)
	else:
		outputDataRe=np.array([(msb << 32) | np.int64(lsb) for msb,lsb in zip(outputDataReMSB,outputDataReLSB)])
		outputDataIm=np.array([(msb << 32) | np.int64(lsb) for msb,lsb in zip(outputDataImMSB,outputDataImLSB)])



	outputPhasor = outputDataRe + 1j*outputDataIm

	print 'Plotting data from {}'.format(str(project_dir)+'/'+str(project_dir_stripped)+'Reoutput'+str(int(inputFreq))+'MHz.dat')

	outputData=[re+1j*im for re,im in zip(outputDataRe,outputDataIm)]
	outputTpts=timeStep*np.arange(0,len(outputData))

	title='Project: '+str(project_dir_stripped)
	fig00=plt.figure(17)
	fig00.suptitle(str(title))

	plt.subplot(3,1,1)
	plt.title(str(inputFreq)+' MHz Input Cosine Wave')
	plt.plot(cosTpts,cosoutput*pow(2,-15))
	plt.xlabel('Time (s)')
	plt.ylabel('Magnitude')

	# plot the output and cooresponding fit
	plt.subplot(3,1,2)
	plt.title(str(inputFreq)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq)+' MHz Output')
	plt.xlabel('Time (s)')
	plt.ylabel('Magnitude')
	plt.plot(outputTpts,#np.abs(outputPhasor),
	np.real(outputPhasor)*pow(2,-28),'r',label='Filtered Output')
	
	# plot the output and cooresponding fit
	plt.subplot(3,1,3)
	plt.title(str(inputFreq)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq)+' MHz Output')
	plt.xlabel('Time (s)')
	plt.ylabel('Phase')
	plt.plot(outputTpts,#np.angle(outputPhasor)/np.pi
	np.imag(outputPhasor)*pow(2,-28),'r',label='Filtered Output')	
	plt.show()
	fig00.savefig(str(project_dir)+'/'+str(project_dir_stripped)+'_acc.pdf')

	plt.close()

def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-s','--samplingFreq',dest='sfreq',type=float,help='sampling frequency in Hz (samples/second)')
   parser.add_argument('-i','--inputFreq',dest='ifreq',type=float,help='frequency for cos wave in MHz')
   parser.add_argument('-d','--decimFactor',dest='decimFactor',type=int,help='Decimation Factor of Polyphase filter')
   parser.add_argument('-p','--project_dir',dest='pdir',type=str,help='project file path')
   parser.add_argument('-m','--module',dest='module',type=str,help='vhdl module to plot')
   parser.add_argument('-o','--options',dest='options',type=str,help='fpga or isim')
   args = parser.parse_args()

   # function call in main:
   plot_complex_signal(args.ifreq,args.sfreq,args.decimFactor,args.pdir,args.module,args.options)
   # Display inputs:
   if (args.ifreq != '' and args.sfreq != ''):
   	print '\nCosine frequency: {} MHz \nSampling frequency: {} MHz'.format(args.ifreq/1e06,args.sfreq/1e06)
   	print 'Writing results to {} directory...\n'.format(str(args.pdir))
if __name__ == "__main__":
   main(sys.argv[1:])
