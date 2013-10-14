#!/usr/bin/python
# python script to generate new hardware output.
# handles the input signal, output file I/O, and plotting functions
# 8/6/13

# argslist:
# -s 			numPoints
# -o 			function Option
# -f 			sampling frequency
# -c 			input frequency
# -b 			bandwidth
# -n 			numTaps (polyphase FIR Filter)
# -t 			simulation time
# -d 			decimation factor (polyphase FIR Filter)
# -m 			matlab flag
# -r 			frequency range
# -l 			filter length of IIR Filter


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

# from mlabwrap import mlab


#--------------------------------------------------------------------------------------------#
# from http://software-carpentry.org/blog/2012/05/an-exercise-with-matplotlib-and-numpy.html #
#--------------------------------------------------------------------------------------------#

def r_squared(actual, ideal):
    actual_mean = np.mean(actual)
    ideal_dev = np.sum([(val - actual_mean)**2 for val in ideal])
    actual_dev = np.sum([(val - actual_mean)**2 for val in actual])

    return ideal_dev / actual_dev

#--------------------------------------------------------------------------------------------#
#								diff of board and iSim dumps 								 #
#--------------------------------------------------------------------------------------------#

def diffHardwareAndSim(numPoints):
	hardwareFile=mylab.csv2rec('/home/nick/digitalDemodTest2/outputRAMtestdemod'+str(numPoints)+'.txt',delimiter='\t')
	newFile=open('/home/nick/dualPortblockRAMdemod_top/hardwareOutput'+str(numPoints)+'.txt','w')
	realOut=[0]*numPoints
	imagOut=[0]*numPoints
	for i in range(numPoints-1):
		realOut[i]=hardwareFile[i][2]
		imagOut[i]=hardwareFile[i][3]
		newFile.write(str('{0:032b}'.format(realOut[i]))+'\t'+str('{0:032b}'.format(imagOut[i]))+'\n')

#--------------------------------------------------------------------------------------------#
#				Generate test inputs for iSim in x"_ _ _ _" format 							 #
#--------------------------------------------------------------------------------------------#

def make_cos_wave(cosFreq, samplingFreq, numPoints, decimFactor):
	resolution=1e05 # (100kHz)
	cosFreq = cosFreq*resolution
	timeStep = 1.0/samplingFreq
	timePts = np.arange(0, numPoints*timeStep,timeStep) 
	cosData = np.cos(2*np.pi*cosFreq * timePts) 
	realData = np.genfromtxt('/home/nick/dualPortblockRAMdemod_top/re_output.dat', dtype=np.int32)
	imagData = np.genfromtxt('/home/nick/dualPortblockRAMdemod_top/im_output.dat', dtype=np.int32)
	myPhasor = realData + 1j * imagData
	phaseInc = int(np.floor((cosFreq/samplingFreq)*pow(2,16)*decimFactor))


	#Write out hex file for VHDL
	intData = np.uint16(cosData*(2**15-1))
	fixedData = [intToFixedPoint(int(i),16,15) for i in intData]
	
	zeroPad=True
	if (zeroPad==True):
		fixedData=[ 0 if i<(len(fixedData)/8) else 0 if i>(len(fixedData)-len(fixedData)/8) else fixedData[i] for i in range(len(fixedData)) ]
		intData[0:len(intData)/8]=0
		intData[(len(intData)-len(intData)/8):len(intData)]=0

	with open('/home/nick/dualPortblockRAMdemod_top/iSimData'+str(numPoints)+'.txt','w') as FID:
		FID.write('signal myCosine : vector_array :=(')
		FID.write(','.join(['x"{0:04X}"'.format(int(x)) for x in intData])+');')
	
	# with open('/home/nick/iirFilter/iSimData'+str(numPoints)+'.txt','w') as FID:
	# 	FID.write('signal myCosine : input_array :=(')
	# 	FID.write(','.join(['x"{0:04X}"'.format(int(x)) for x in fixedData])+');')
	# 	print '\nSimulation Input File written.'
	with open('/home/nick/iirFilter/iSimData'+str(numPoints)+'.txt','w') as FID:
		FID.write('signal myCosine : input_array :=(')
		FID.write(','.join(['x"{0:04X}"'.format(int(x)) for x in intData])+');')

	with open('/home/nick/iirFilter/phaseInc.txt','w') as pfid:
		pfid.write('phaseInc <= '+'x"{0:04X}"'.format(phaseInc)+'; wait until (rising_edge(clk));')

	with open('/home/nick/firFilter/demodData'+str(len(myPhasor))+'.txt','w') as demodFile:
		demodFile.write('signal myDemodData : vector_array :=(') 
		demodFile.write(','.join(['x"{0:04X}"'.format(( (~int(np.abs(x))) &0xfff )+1) for x in myPhasor]) + ');') 

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
	
#--------------------------------------------------------------------------------------------#
#					Amplitude and Phase Response Plotting 									 #
#--------------------------------------------------------------------------------------------#

def plotMagPhase(fileSelect,sweepfreq,p0,p1,p2,nyq):
	cutoff=0.4
	nsweepfreq=[sw/nyq for sw in sweepfreq]

	print '\n\nLength of sweepfreq: ({}) and length of parameters: ({},{},{})\n'.format(len(sweepfreq),len(p0),len(p1),len(p2))

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
#					Plot fits of frequencies in "sweepfreq" 								 #
#--------------------------------------------------------------------------------------------#

def sweepingPlot(sweepfreq,timePts,data,p0,p1,p2,decimFactor,title,total):
	myString=[str(int(i/pow(10,5))) for i in sweepfreq]
	
	# uses polyDecimDemodFilter_Top_tb.vhd data:
	if (total==True):
		timeStep=1/100e06
		cosoutput=[np.genfromtxt('/home/nick/polyDecimDemodFilter/cosoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
		firoutput=[np.genfromtxt('/home/nick/polyDecimDemodFilter/datatoDemodTopoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]

		cosoutput = [co*pow(2,-15) for co in cosoutput]
		firoutput=[fi*pow(2,-4) for fi in firoutput]

		firTpts=[np.arange(0,len(fi)*timeStep*decimFactor,timeStep) for fi in firoutput]
		cosTpts=[np.arange(0,len(co)*timeStep,timeStep) for co in cosoutput]
		fig00=plt.figure(17)
		fig00.suptitle(str(title))
		fftdata=[np.fft.fft(dt) for dt in data]
		myfftfreq=[np.fft.fftfreq(len(fd)) for fd in fftdata]

		# import pdb ; pdb.set_trace() 

		for i in range(len(sweepfreq)):
		    
		    # plot the input signal
		    plt.subplot(3,1,1)
		    plt.title(str(sweepfreq[i]/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*sweepfreq[i]/1e06)+' MHz Output')
		    plt.plot(cosTpts[i],cosoutput[i])
		    plt.xlabel('Time (s)')
		    plt.ylabel('Magnitude')
		    
		    # plot the output and cooresponding fit
		    plt.subplot(3,1,2)
		    plt.title(str(sweepfreq[i]/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*sweepfreq[i]/1e06)+' MHz Output')
		    plt.xlabel('Time (s)')
		    plt.ylabel('Magnitude')
		    plt.plot(timePts[i],np.real(data[i]),'r',label='Filtered Output')
		    plt.plot(timePts[i],p0[i]*np.cos(2*np.pi*sweepfreq[i]*timePts[i]*decimFactor+p1[i]),'b',label='Fitted Output')
		    plt.legend(loc='lower right')
		    
		    # plot the output and cooresponding fit
		    plt.subplot(3,1,3)
		    plt.title(str(sweepfreq[i]/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*sweepfreq[i]/1e06)+' MHz Output')
		    plt.xlabel('Time (s)')
		    plt.ylabel('Magnitude')
		    plt.plot(timePts[i],np.imag(data[i]),'r',label='Filtered Output')
		    plt.plot(timePts[i],p0[i]*np.cos(2*np.pi*sweepfreq[i]*timePts[i]*decimFactor+p1[i]),'b',label='Fitted Output')
		    plt.legend(loc='lower right')
		    plt.show()

	# use all other vhdl testbenches:
	elif (total==False):
		fig00=plt.figure(17)
		fig00.suptitle(str(title))
		for i in range(len(sweepfreq)):
			# subplot_indx1=len(sweepfreq)
			# subplot_indx2=1
			# subplot_indx3=i+1
			# plt.subplot(subplot_indx1, subplot_indx2, subplot_indx3)
			# plot the output and corresponding fit
			plt.title(str(sweepfreq[i]/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*sweepfreq[i]/1e06)+' MHz Output')
			plt.xlabel('Time (s)')
			plt.ylabel('Magnitude')
			plt.plot(timePts[i],data[i],'r',label='Filtered Output')
			plt.plot(timePts[i],p0[i]*np.cos(2*np.pi*sweepfreq[i]*timePts[i]*decimFactor+p1[i])+p2[i],'b',label='Fitted Output')
			plt.legend(loc='lower right')
			plt.show()
	plt.close()
	
#--------------------------------------------------------------------------------------------#
#					Reading and plotting Opal Kelly 6010 LX45 data 							 #
#--------------------------------------------------------------------------------------------#

def readAndPlot(numPoints):
	timeVec2=[0]*numPoints
	realOut=[0]*numPoints
	imagOut=[0]*numPoints
	input1=[0]*numPoints
	totalSignal=[0]*numPoints
	outputData=mylab.csv2rec('/home/nick/digitalDemodTest2/outputRAMtestdemod'+str(numPoints)+'.txt',delimiter='\t')
	for i in range(numPoints-1):
		timeVec2[i]=outputData[i][0]
		input1[i]=outputData[i][1]
		realOut[i]=outputData[i][2]
		imagOut[i]=outputData[i][3]
	totalSignal=np.vectorize(complex)(realOut,imagOut)
	plt.figure(1)
	plt.subplot(211)
	plt.title('Real Input and Output Signals')
	plt.plot(timeVec2,np.real(input1),'r.-',timeVec2,realOut,'b.-')
	plt.subplot(212)
	plt.title('Imag Input and Output Signals')
	plt.plot(timeVec2,np.imag(input1),'r.-',timeVec2,imagOut,'b.-')
	plt.show()

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
# 				Plot output of signal processing chain 										 #
#--------------------------------------------------------------------------------------------#

def plotTotalChannelizer(cosFreq, samplingFreq, numPoints, numTaps, decimFactor, simTime, fileSelect, frange, filterLength):
	timeStep = 1.0/samplingFreq
	sweepfreq = [i for i in np.arange(5e05,125e05,5e05)]
	print sweepfreq
	sweepfreq = [float(i) for i in sweepfreq]
	nyq = samplingFreq/2.0


	myString=[str(int(i/pow(10,5))) for i in sweepfreq]

	# iSim signals from file writer:
	demodoutputRe=[np.genfromtxt('/home/nick/polyDecimDemodFilter/dataDemodReoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	demodoutputIm=[np.genfromtxt('/home/nick/polyDecimDemodFilter/dataDemodImoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	firoutput=[np.genfromtxt('/home/nick/polyDecimDemodFilter/datatoDemodTopoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	inputCos = [np.genfromtxt('/home/nick/polyDecimDemodFilter/cosoutput'+str(myString[i])+'MHz.dat',dtype=str) for i in range(len(sweepfreq))]
	outputRe = [np.genfromtxt('/home/nick/polyDecimDemodFilter/polyDecimDemodFilterReoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	outputIm = [np.genfromtxt('/home/nick/polyDecimDemodFilter/polyDecimDemodFilterImoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]

	print 'Length of input data: {}\n'.format(len(inputCos[0]))

	# convert to fixed point
	print 'FixedPoint Value: {}\n'.format(np.float(int(inputCos[0][10]))*pow(2,-15))

	newdemodRe = [[0]*len(sweepfreq)*len(re) for re in demodoutputRe]
	newdemodIm = [[0]*len(sweepfreq)*len(im) for im in demodoutputIm]
	newCos = [[0]*len(sweepfreq)*len(ic) for ic in inputCos]
	newRe = [[0]*len(sweepfreq)*len(re) for re in outputRe]
	newIm = [[0]*len(sweepfreq)*len(im) for im in outputIm]
	newFirOutput = [[0]*len(fi) for fi in firoutput]
	demod_phasor = [[0]*len(sweepfreq)*len(re) for re in demodoutputRe]
	phasor = [[0]*len(sweepfreq)*len(re) for re in outputRe]


	# cosine input signal:
	for i in range(len(sweepfreq)):
		for j in range(len(inputCos[i])):
			newCos[i][j]=np.float(int(inputCos[i][j]))#*pow(2,-15)

	# fir output signal:
	for i in range(len(sweepfreq)):
		for j in range(len(firoutput[i])):
			newFirOutput[i][j]=np.float(int(firoutput[i][j]))*pow(2,-4)

	# demodulator real signal:
	for i in range(len(sweepfreq)):
		for j in range(len(demodoutputRe[i])):
			newdemodRe[i][j]=np.float(demodoutputRe[i][j])#*pow(2,-9)

	# demodulator imag signal:
	for i in range(len(sweepfreq)):
		for j in range(len(demodoutputIm[i])):
			newdemodIm[i][j]=np.float(demodoutputIm[i][j])#*pow(2,-9) 

	for i in range(len(sweepfreq)):
		for j in range(len(newdemodRe[i])):
			demod_phasor[i][j] = newdemodRe[i][j] + 1j * newdemodIm[i][j]	

	# output phasor signals:
	for i in range(len(sweepfreq)):
		for j in range(len(outputRe[i])):
			newRe[i][j]=np.float(int(outputRe[i][j]))#*pow(2,-10)

	for i in range(len(sweepfreq)):
		for j in range(len(outputIm[i])):
			newIm[i][j]=np.float(int(outputIm[i][j]))#*pow(2,-10)

	for i in range(len(sweepfreq)):
		for j in range(len(outputRe[i])):
			phasor[i][j] = newRe[i][j] + 1j * newIm[i][j]



	print 'Length of output signals: {} and {} and {}\n'.format(len(outputRe),len(outputIm),len(inputCos))


	# truncate phasor:
	trunc_length = numTaps+filterLength
	# phasor = [ph[trunc_length:len(ph)-1]/32 for ph in phasor]

	# truncate:
	print 'Truncation Length: {}\nSize: {} a multiple? {}'.format(trunc_length,len(newRe[0]),len(newRe[0])%trunc_length==0)
	# newRe = [re[8:256] for re in newRe]

	# phasor = [ph[50:244] for ph in phasor]



	# firoutput = [fi[7:len(fi)] for fi in firoutput]

	for i in range(len(firoutput)):
		print 'Lengths: {}'.format(len(firoutput[i]))

	# time vectors:

	# demod_phasor = [dp[50:244] for dp in demod_phasor]

	# newFirOutput = [fi[50:220] for fi in newFirOutput]

	demodTpts = [np.arange(0,len(dp)*timeStep,timeStep) for dp in demod_phasor]
	cosTpts = [np.arange(0,len(ic)*timeStep,timeStep) for ic in inputCos]
	phasorTpts = [np.arange(0,len(ph)*timeStep,timeStep) for ph in phasor]
	outputRePts = [np.arange(0,len(re)*timeStep,timeStep) for re in newRe]
	firTpts=[np.arange(0,len(fi)*timeStep,timeStep) for fi in newFirOutput]

	phasor = [np.real(ph) for ph in phasor]

	re_p0,re_p1,re_p2 = phaseMagFit(sweepfreq,phasorTpts,np.real(phasor),1)
	# im_p0,im_p1,im_p2 = phaseMagFit(sweepfreq,phasorTpts,np.imag(phasor),decimFactor)
	p0,p1,p2 = phaseMagFit(sweepfreq,outputRePts,newRe,1)
	p00,p11,p22 = phaseMagFit(sweepfreq,firTpts,newFirOutput,decimFactor)
	p000,p111,p222 = phaseMagFit(sweepfreq,demodTpts,np.real(demod_phasor),decimFactor)


	# plotMagPhase(fileSelect,sweepfreq,re_p0,re_p1,re_p2,nyq)

	plotMagPhase(fileSelect,sweepfreq,p00,p11,p22,nyq)
	# plotMagPhase(fileSelect,sweepfreq,p0,p1,p2,nyq)
	# plotMagPhase(fileSelect,sweepfreq,p000,p111,p222,nyq)

	sweepingPlot(sweepfreq,phasorTpts,phasor,re_p0,re_p1,re_p2,decimFactor,'Total Channelizer',True)
	# sweepingPlot(sweepfreq,demodTpts,demod_phasor,p000,p111,p222,decimFactor,'Demodulated Phasor',True)

	# plotMagPhase(fileSelect,sweepfreq,re_p0,re_p1,nyq/decimFactor)
	

	# -------------------------------------save---------------------------------------------#
	#																						#
	# sweepingPlot(sweepfreq,firTpts,newFirOutput,p00,p11,decimFactor,'FIR Filter',False)	#
	#																						#
	# -------------------------------------save---------------------------------------------#

	# sweepingPlot(sweepfreq,outputRePts,newRe,p0,p1,1,'Total Channelizer Input vs. Output',True)
	# sweepingPlot(sweepfreq,phasorTpts,phasor,re_p0,re_p1,decimFactor,'Total Channelizer Input vs. Output',True)

	# inputFreq=10
	# freqSelect=inputFreq-1

	# fig0 = plt.figure(0)
	# plt.suptitle('Input Signal and output from Signal Processor')
	# plt.subplot(211)
	# plt.title('Input Cos Signal')
	# plt.plot(cosTpts[freqSelect],inputCos[freqSelect])
	# plt.xlabel('Time (s)')
	# plt.ylabel('Magnitude')

	# plt.subplot(212)
	# plt.title('Output Signal')
	# plt.plot(phasorTpts[freqSelect],phasor[freqSelect])
	# plt.xlabel('Time (s)')
	# plt.ylabel('Magnitude')
	# plt.show()
	# phaseMagFit()	

#--------------------------------------------------------------------------------------------#
# 			Plot all iSim signals for individual and combined blocks 						 #
#--------------------------------------------------------------------------------------------#

def justPlotSim2(cosFreq, samplingFreq, numPoints, numTaps, decimFactor, simTime, fileSelect, frange, filterLength):
	iirLength = filterLength
	timeStep = 1.0/samplingFreq
	sweepfreq = [i for i in np.arange(1e06,13e06,1e06)]
	sweepfreq = [float(i) for i in sweepfreq]
	sweepfreqIIR = [float(i) for i in np.arange(5e06,125e06,5e06)]
	nyq = samplingFreq/2.0
	matlab_path = '/home/MQCO/matlab_firFilter'
	# mlab.path(mlab.path(),matlab_path)
	# filterParams = [decimFactor,numTaps,samplingFreq,numPoints/decimFactor]
	# mlab.sweepPolyphaseFreq(frange[0],frange[1],filterParams)
	print 'Using ', len(sweepfreq),' frequencies from '+str(np.min(sweepfreq)/1e06)+' MHz to '+str(np.max(sweepfreq)/1e06)+' MHz ...\n'
	print '\nDecimating at a rate of {} ...'.format(decimFactor)
	# demodulator plotting signals:
	sinData = np.genfromtxt('/home/nick/dualPortblockRAMdemod_top/sin_output.dat', dtype=np.int16)
	cosData = np.genfromtxt('/home/nick/dualPortblockRAMdemod_top/cos_output.dat', dtype=np.int16)
	realData = np.genfromtxt('/home/nick/dualPortblockRAMdemod_top/re_output.dat', dtype=np.int32)
	imagData = np.genfromtxt('/home/nick/dualPortblockRAMdemod_top/im_output.dat', dtype=np.int32)
	# polyphase signals:
	polyData = np.genfromtxt('/home/nick/firFilter/firFilter_outputStep.dat',dtype=np.int32)
	polyDataPts = np.arange(0,len(polyData)*timeStep,timeStep)
	polyImpulseData = np.genfromtxt('/home/nick/firFilter/firFilter_outputImpulse.dat',dtype=np.int32)
	polyImpulsePts = np.arange(0,len(polyImpulseData)*timeStep,timeStep)

	# filtered signal from demodulator:
	polyDemodData = np.genfromtxt('/home/nick/firFilter/firFilter_outputDemod.dat',dtype=np.int32)
	polyDemodDataTpts = np.arange(0,len(polyDemodData)*timeStep,timeStep)
	polyDemodDataFFT = np.fft.fft(polyDemodData)
	polyDemodFreq = np.fft.fftfreq(len(polyDemodDataFFT))

	# polyphase sweep signals:
	myString=[str(i/pow(10,6)) if str(i/pow(10,6))=='1.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='2.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='3.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='4.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='5.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='6.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='7.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='8.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='9.5' else str(int(i/pow(10,6))) for i in sweepfreq]
	myStringIIR = [str(i/pow(10,6)) if str(i/pow(10,6))=='1.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='2.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='3.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='4.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='5.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='6.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='7.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='8.5' else str(i/pow(10,6)) if str(i/pow(10,6))=='9.5' else str(int(i/pow(10,6))) for i in sweepfreqIIR]

	# Select which set of files to plot:
	if(fileSelect=='matlab'):
		polyDataSweep = [np.genfromtxt('/home/nick/matlab_firFilter/matlab_polyphase_sweep_'+str(myString[i])+'_MHz.txt',dtype=np.float) for i in range(len(sweepfreq)) ]
	elif(fileSelect=='VHDL'):
		polyDataSweep = [np.genfromtxt('/home/nick/firFilter/firFilter_output'+str(myString[i])+'MHz.dat',dtype=np.int32) for i in range(len(sweepfreq)) ]
	# iirfilterData = [np.genfromtxt('/home/nick/iirFilter/iirFilter_output'+str(myStringIIR[i])+'MHz.dat',dtype=np.int16)*int(pow(2,15)) for i in range(len(sweepfreqIIR))]
	# butterworthFilterData = [np.genfromtxt('/home/nick/butterworthFilter/butterworth_output'+str(myStringIIR[i])+'MHz.dat',dtype=str) for i in range(len(sweepfreqIIR))]
	butterworthFilterData = [np.genfromtxt('/home/nick/butter_quantized_20bit/butter_quantized_20bit_output'+str(myStringIIR[i])+'MHz.dat',dtype=str) for i in range(len(sweepfreqIIR))]
	print '\n--------------------------------------------------------------------------------\n\n{} plotting option selected...\n'.format(fileSelect)


	# newButterData = [np.float(int(bw,2))*pow(2,-10) for bw in butterworthFilterData]

	newButterData = [[0]*len(sweepfreqIIR)*len(bw) for bw in butterworthFilterData]
	for i in range(len(sweepfreqIIR)-1):
		for j in range(len(butterworthFilterData[i])-1):
			# newButterData[i][j] = np.float(int(butterworthFilterData[i][j],2))*pow(2,-10)
			newButterData[i][j] = np.float(int(butterworthFilterData[i][j]))*pow(2,-14)


	# newButterData=[nd.pop() if nd>1 else nd for nd in newButterData]


	# newButterData = [[0]*len(sweepfreqIIR)*len(bw) for bw in butterworthFilterData]
	# for i in range(len(sweepfreqIIR)-1):
	# 	for j in range(len(butterworthFilterData[i])-1):
	# 		newButterData[i][j] = binaryToFixedPoint(butterworthFilterData[i][j],16,10).__float__()/(pow(2,32-1))


	# truncate iir filter by length of filter:
	# newButterData =[ np.float(bw)/32 for bw in newButterData]

	newButterData = [bw[8:len(bw)/64] for bw in newButterData]
	butterworthTpts = [np.arange(0,len(bw)*timeStep,timeStep) for bw in newButterData]



	# butterworthFilterData = [int(binaryToFixedPoint(bw,16,15)) for bw in butterworthFilterData]

	# # truncate iir filter by length of filter:
	# butterworthFilterData =[ bw/32 for bw in butterworthFilterData]
	# butterworthTpts = [np.arange(0,len(bw)*timeStep,timeStep) for bw in butterworthFilterData]
	# iirfilterData = [fd[iirLength:len(fd)-1] for fd in iirfilterData ]
	# iirTimePts = [np.arange(0,len(iirfd)*timeStep,timeStep) for iirfd in iirfilterData]
	
	print '\nRemoving initial samples from filter of length {} ...\n'.format(numTaps)
	print 'Length of signal: {} and specified number of points: {}'.format(len(polyDataSweep[0]),numPoints)
	# truncate for 21 points or the length of the filter
	file_length_diff = [ len(sp) - np.int(np.floor(numPoints/decimFactor)) for sp in polyDataSweep]
	if(file_length_diff>0):
		print '\nOutput file difference: {}'.format(file_length_diff)
		polyDataSweep = [ sp[numTaps:len(sp)-1-fd] for sp,fd in zip(polyDataSweep,file_length_diff)]	
	else:
		print '\nOnly truncating {} points from filter length.'.format(numTaps)
		polyDataSweep = [ sp[numTaps:len(sp)-1] for sp in polyDataSweep]
	polyDataSweepPts = [np.arange(0,len(i)*timeStep,timeStep) for i in polyDataSweep]
	sweepTimePts = np.arange(0,numPoints*timeStep,timeStep)
	inputSweep = [np.cos(2*np.pi*spFreq*sweepTimePts)*pow(2,16-1) for spFreq in sweepfreq ]
	nsweepfreq = [float(sf)/nyq for sf in sweepfreq ]



	# normalized Frequencies and magnitudes:
	polyDataSweepFFT = [np.fft.fft(pd) for pd in polyDataSweep]
	polyDataSweepFFTMag = [np.abs(pdfft) for pdfft in polyDataSweepFFT]
	# polyDataSweepFFTMagResponse = [10*np.log10(pdfftmg) for pdfftmg in polyDataSweepFFTMag]

	fftFreq = [np.fft.fftfreq(pdfft.size, d = 1/samplingFreq) for pdfft in polyDataSweepFFT]
	
	
	
	# plotting all frequencies and their curve_fit() functions:
	# fit function of the form: s(t) = p0 * cos( 2*pi*f*t + p1 )

	# plotting phase and magnitude of FIR Filter:

	fitPolyModel=False
	if(fitPolyModel==True):
		p0,p1,p2 = phaseMagFit(sweepfreq,polyDataSweepPts,polyDataSweep,decimFactor)
		plotMagPhase(fileSelect,sweepfreq,p0,p1,p2,nyq)
		# sweepingPlot(sweepfreq,polyDataSweepPts,polyDataSweep,p0,p1,decimFactor,'Fitted Cosine and Output Cosine')
		

	# plotting phase and magnitude response of IIR Filter:

	# 1. elliptic iir filter test plotting
	fitiirFilter=False
	if(fitiirFilter==True):	
		p00,p11,p22 = phaseMagFit(sweepfreqIIR,iirTimePts,iirfilterData,1)
		plotMagPhase(fileSelect,sweepfreqIIR,p00,p11,p22,nyq)
		# sweepingPlot(sweepfreqIIR,iirTimePts,iirfilterData,p00,p11,1,'IIR Filter Analysis (MATLAB Generated VHDL)')

	# 2. butterworth iir filter test plotting
	butterworth=True
	if(butterworth==True):
		print 'Plotting Butterworth filter...\n'
		p000,p111,p222 = phaseMagFit(sweepfreqIIR,butterworthTpts,newButterData,1)
		plotMagPhase(fileSelect,sweepfreqIIR,p000,p111,p222,nyq)
		# sweepingPlot(sweepfreqIIR,butterworthTpts,newButterData,p000,p111,1,'Butterworth Filter Analysis (MATLAB Generated VHDL)',False)
		# p000,p111 = phaseMagFit(sweepfreqIIR,butterworthTpts,butterworthFilterData,1)
		# plotMagPhase(fileSelect,sweepfreqIIR,p000,p111)
		# # sweepingPlot(sweepfreqIIR,butterworthTpts,butterworthFilterData,p000,p111,1,'Butterworth Filter Analysis (MATLAB Generated VHDL)',False)


	timePts = np.arange(0, len(sinData)*timeStep,timeStep)
	inputData = np.cos(2*np.pi*cosFreq*timePts)*pow(2,16-1)
	demodTimePts = np.arange(0, len(realData)*timeStep,timeStep)
	polyphaseTimePts = np.arange(0, len(polyData)*timeStep,timeStep)

	# sinPhase=2*np.pi*cosFreq*timeLag
	# cosPhase=2*np.pi*cosFreq*timeLag
	sinPhase=0
	cosPhase=0
	cleanSin = np.sin(2*np.pi*cosFreq*timePts+sinPhase)*pow(2,16-1)
	cleanCos = np.cos(2*np.pi*cosFreq*timePts+cosPhase)*pow(2,16-1)
	
	# demodulator and NCO phasor signals:
	demodPhasorSignal = realData + 1j*imagData
	phasorSignal = cosData + 1j*sinData
	demodFreq, demodPxx_den = signal.periodogram(demodPhasorSignal, samplingFreq, 'flattop', scaling='density')
	freq, Pxx_den = signal.periodogram(phasorSignal, samplingFreq, 'flattop', scaling='density')
	
	maxfreq = np.max(freq)
	maxdemodFreq = np.max(demodFreq)
	maxPxx_den = np.max(Pxx_den)
	maxdemodPxx_den = np.max(demodPxx_den)

	# output spectrum arrays:
	k = np.arange(len(phasorSignal))	
	T = len(phasorSignal)/samplingFreq
	specFreq = k/T
	specFreq = specFreq[range(len(phasorSignal)/2)]
	maxspecFreq = np.max(specFreq)
	phasorFFT = np.fft.fft(phasorSignal)/len(phasorSignal)
	phasorFFT = phasorFFT[range(len(phasorSignal)/2)]
	# print '\nMax Frequencies: \n', maxfreq/1.0e06,'MHz, ', maxdemodFreq/1.0e06, 'MHz, and ',maxspecFreq/1.0e06 ,'MHz\n'


	# polyphase frequency response:
	polyFFT = np.fft.fft(polyData)
	polyFreq = np.fft.fftfreq(polyData.size, d = 1/samplingFreq)
	# step response input to filter:
	stepTimePts = np.arange(0,numPoints*timeStep,timeStep)
	stepImpulse = [0 if i<len(stepTimePts)/2 else 1 for i in range(len(stepTimePts))]
	# unit impulse signals:
	unitImpulse = [1 if i==0 else 0 for i in range(len(timePts))]
	polyImpulseFFT = np.fft.fft(polyImpulseData)
	polyImpulseFreq = np.fft.fftfreq(len(polyImpulseData), d = timeStep)


	# set True to plot all modules:
	analyzeAll=False

	cosPlot=False
	if (cosPlot == True or analyzeAll == True):
		# sin and cos signals from NCO with floating point equivalents:
		fig1 = plt.figure(1)
		fig1.suptitle('Sin and Cos Signals from NCO, Floating Point Equivalents Superimposed',fontsize=16, fontweight='bold')
		plt.subplot(211)
		plt.xlim(0,0.000010)
		plt.title('Sin Signal from NCO with Clean Sin Wave')
		plt.plot(timePts,sinData,'r.-',timePts,cleanSin,'b.-')
		
		plt.subplot(212)
		plt.xlim(0,0.000010)
		plt.title('Cos Signal from NCO with Clean Cos Wave')
		plt.plot(timePts,cosData,'r.-',timePts,cleanCos,'b.-')
	
	analyzeDemod=False
	if (analyzeDemod == True or analyzeAll == True):
		# power spectral density of NCO phasor signal, s(t) = cos(wt+phi) + j*sin(wt+phi):
		fig2 = plt.figure(2)
		fig2.suptitle('Power Spectrum Estimates for NCO',fontsize=16, fontweight='bold')
		
		plt.subplot(211)
		plt.title('Power Spectral Density in $V^2$/Hz from signal.periodogram()')
		plt.ylim(pow(10,-11),pow(10,1))
		plt.axhline(y=1, color='#FF4900', linestyle='-',label="0 dB noise level")
		plt.axhline(y=pow(10,-4.8), color='#FF9200', linestyle='-',label="-48 dB level")
		plt.axhline(y=pow(10,-5.0), color='k', linestyle='--',label="-50 dB level")
		plt.axhline(y=pow(10,-2.557), color='#007241', linestyle='-',label="-25 dB level")
		plt.semilogy(freq/maxfreq,Pxx_den/maxPxx_den)
		plt.xlabel('frequency [Hz]')
		plt.ylabel('Power Spectral Density [$V^2$/Hz]')

		plt.subplot(212)
		plt.title('Power Spectral Density in dB/Hz from signal.periodogram()')
		plt.ylim(-110,10)
		plt.axhline(y=0, color='#FF4900', linestyle='-',label="0 dB level")
		plt.axhline(y=-50, color='k', linestyle='--',label="-50 dB level")
		plt.axhline(y=-48, color='#FF9200', linestyle='-',label="-48 dB level")
		plt.axhline(y=-25.57, color='#007241', linestyle='-',label="-25 dB level")
		plt.plot(freq/maxfreq,10*np.log10(Pxx_den/maxPxx_den))
		plt.xlabel('frequency [Hz]')
		plt.ylabel('Power Spectral Density [dB/Hz]')


		# power spectral density of demodulator output signal:
		fig3 = plt.figure(3)	
		fig3.suptitle('Power Spectrum Estimates for Demodulator',fontsize=16, fontweight='bold')
		plt.subplot(211)
		plt.title('Power spectral Density of demodSignal in $V^2$/Hz from signal.periodogram()')
		plt.ylim(pow(10,-11),pow(10,1))
		plt.axhline(y=1, color='#FF4900', linestyle='-',label="0 dB noise level")
		plt.axhline(y=pow(10,-4.8), color='#FF9200', linestyle='-',label="-48 dB level")
		plt.axhline(y=pow(10,-5.0), color='k', linestyle='--',label="-50 dB level")
		plt.axhline(y=pow(10,-2.57), color='#007241', linestyle='-',label="-25 dB level")
		plt.semilogy(demodFreq/maxdemodFreq,demodPxx_den/maxdemodPxx_den)
		plt.xlabel('frequency [Hz]')
		plt.ylabel('Power Spectral Density [$V^2$/Hz]')

		plt.subplot(212)
		plt.title('Power spectral Density of demodSignal in dB/Hz from signal.periodogram()')
		plt.ylim(-110,10)
		plt.axhline(y=0, color='#FF4900', linestyle='-',label="0 dB level")
		plt.axhline(y=-50, color='k', linestyle='--',label="-50 dB level")
		plt.axhline(y=-48, color='#FF9200', linestyle='-',label="-48 dB level")
		plt.axhline(y=-25.58, color='#007241', linestyle='-',label="-25 dB level")
		plt.plot(demodFreq/maxdemodFreq,10*np.log10(demodPxx_den/maxdemodPxx_den))
		plt.xlabel('frequency [Hz]')
		plt.ylabel('Power Spectral Density [dB/Hz]')

	
		# multiplication of signals:
		fig4 = plt.figure(4)
		fig4.suptitle('Multiplication of Input Signal and Real NCO Signals',fontsize=16, fontweight='bold')
		plt.subplot(311)
		plt.title('Input/Carrier Signal')
		plt.xlim(0,0.000006)
		plt.plot(timePts,inputData,'c.-')

		plt.subplot(312)
		plt.title('Signals into Real Multiplier')
		plt.xlim(0,0.000006)
		plt.plot(timePts,cosData,'r.-') # ,timePts,inputData,'c.-')
		
		plt.subplot(313)
		plt.title('Signal out of Real Multiplier')
		plt.xlim(0,0.000006)
		plt.plot(demodTimePts,realData,'g.-')
		
		fig5 = plt.figure(5)
		fig5.suptitle('Multiplication of Input Signal and Imag NCO Signals',fontsize=16, fontweight='bold')
		plt.subplot(311)
		plt.xlim(0,0.000006)
		plt.title('Input/Carrier Signal')
		plt.plot(timePts,inputData,'c.-')

		plt.subplot(312)
		plt.title('Signals into Imag Multiplier')
		plt.xlim(0,0.000006)	
		plt.plot(timePts,sinData,'r.-') # ,timePts,inputData,'c.-')
		
		plt.subplot(313)
		plt.title('Signal out of Imag Multiplier')
		plt.xlim(0,0.000006)
		plt.plot(demodTimePts,imagData,'g.-')

	analyzePoly=False
	sweepPoly=False
	analyzePolyDemod=False
	if (analyzePoly == True or analyzeAll == True):

		# polyphase filtering results:
		fig6 = plt.figure(6)
		fig6.suptitle('Polyphase Filtered Signal')
		plt.subplot(311)
		plt.title('Step Impulse Input')
		plt.plot(stepTimePts/1.0e-06,stepImpulse,'c')
		plt.ylim(-0.1,1.1)
		plt.xlabel('Time ($\mu{s}$)')
		plt.ylabel('Magnitude')

		plt.subplot(312)
		plt.title('Magnitude Response of Filtered Signal')
		plt.axhline(y=70, color='#FF4900', linestyle='-',label="Real Max dB level")
		plt.axhline(y=0, color='k', linestyle='--',label="0 dB level")
		plt.axhline(y=50, color='#FF9200', linestyle='-',label="50 dB level")
		plt.axhline(y=21, color='#007241', linestyle='-',label="21 dB level")
		plt.xlim(0,1)
		plt.ylim(-np.max(10*np.log10(np.abs(polyFFT)))/2,np.max(10*np.log10(np.abs(polyFFT)))+10)
		plt.plot(polyFreq*2.0*np.pi/np.max(polyFreq*2.0*np.pi),10*np.log10(np.abs(polyFFT)))
		plt.xlabel('Normalized Frequency')
		plt.ylabel('Normalized Magnitude')

		plt.subplot(313)
		plt.title('Time Domain Response')
    	plt.plot(polyDataPts/1.0e-06,polyData,'r')
    	plt.xlabel('Time ($\mu{s}$)')
    	plt.ylabel('Magnitude')
    	# plt.show()
    	if (sweepPoly == True or analyzeAll == True):
			fig7 = plt.figure(7)
			fig7.suptitle('Sweeping frequencies through filter')
			
			plt.subplot(311)
			plt.title('Input Signals')
			plt.xlabel('Time')
			plt.ylabel('Magnitude')
			plt.xlim(0,0.000002)
			for i in range(len(sweepfreq)):
				plt.plot(sweepTimePts,inputSweep[i]/np.max(inputSweep[i]))

			plt.subplot(312)
			plt.title('Filtered Signals Magnitude Response')
			plt.xlabel('Normalized Frequency')
			plt.ylabel('Normalized Magnitude')
			plt.xlim(0,1)
			for i in range(len(sweepfreq)):
				plt.plot(polyDataSweepFreq[i]/np.max(polyDataSweepFreq[i]),10*np.log10(np.abs(polyDataSweepFFT[i])))

			phaseSlope, phaseIntercept = np.polyfit(sweepfreq,phaseShift,1)
			print '\nslope and intercept: ',phaseSlope,' ',phaseIntercept,'\n'

			bestFitShift = [phaseIntercept + (phaseSlope*sf) for sf in sweepfreq]
			fit_shift_label = 'Linear Fit ({0:.8f})'.format(phaseSlope)
			r_sqrd = r_squared(phaseShift,bestFitShift)

			print 'phaseShift and bestFitShift lengths: ',len(phaseShift),' ',len(bestFitShift),'\n'

			plt.subplot(313)
			plt.title('Phase shift $\phi_i=2\pi{f_i}\Delta{t_i}$')
			plt.xlabel('Input Frequency (Hz)')
			plt.ylabel('Phase Shift')
			plt.plot(sweepfreq,phaseShift,'ro')
			plt.plot(sweepfreq,bestFitShift,'b--',label=fit_shift_label)
			plt.annotate('$r^2$={0:.8f}'.format(r_sqrd), (0.05, 0.9), xycoords='axes fraction')
			plt.legend(loc='lower right')

			fig8 = plt.figure(8)
			fig8.suptitle('Polyphase filtering of unit impulse')
			plt.subplot(311)
			plt.xlim(-1,)
			plt.ylim(0,1.1)
			plt.title('Unit Impulse Input Signal')
			plt.plot(timePts/1.0e-06,unitImpulse,'c')
			plt.xlabel('Time ($\mu{s}$)')
			plt.ylabel('Magnitude')
    
			plt.subplot(312)
			plt.title('Filtered Frequency Response')
			plt.axhline(y=70, color='#FF4900', linestyle='-',label="Real Max dB level")
			plt.axhline(y=50, color='#FF9200', linestyle='-',label="50 dB level")
			plt.axhline(y=21, color='#007241', linestyle='-',label="21 dB level")
			plt.xlim(0,1)
			plt.ylim(np.min(10*np.log10(np.abs(polyImpulseFFT)))-5,np.max(10*np.log10(np.abs(polyImpulseFFT)))+5)
			plt.plot(polyImpulseFreq*2.0*np.pi/np.max(polyImpulseFreq*2.0*np.pi),10*np.log10(np.abs(polyImpulseFFT)))
			plt.xlabel('Normalized Frequency')
			plt.ylabel('Normalized Magnitude')

			plt.subplot(313)
			plt.title('Filtered Signals Phase Response')
			plt.plot(polyImpulsePts/1.0e-06,polyImpulseData,'r')
			plt.xlabel('Time ($\mu{s}$)')
			plt.ylabel('Magnitude')

			# plt.show()

	# plot demodulated signal then filter the signal:
	if (analyzePolyDemod == True or analyzeAll == True):
		fig9 = plt.figure(9)
		fig9.suptitle('Demodulated Signal Filtered')
		plt.subplot(211)
		plt.title('Demodulated Phasor Signal')
		plt.plot(demodTimePts,phasorSignal/np.max(phasorSignal),'m')
		plt.xlabel('Time')
		plt.ylabel('Magnitude')
		plt.xlim(0,0.000016)

		plt.subplot(212)
		plt.title('Magnitude Response of Filtered And Demodulated Signal')
		plt.xlim(0,1)
		plt.xlabel('Normalized Frequency')
		plt.ylabel('Normalized Magnitude')
		plt.plot(polyDemodFreq/np.max(polyDemodFreq),10*np.log10(np.abs(polyDemodDataFFT)))
		# plt.show()

	# print 'Lengths of sweepTimePts: {} and inputSweep: {}'.format(len(sweepTimePts),len(inputSweep))

	# # plot polyphase filtered signals:
	# for i in range(len(sweepfreq)):
	# 	fig10 = plt.figure(10)
	# 	fig10.suptitle(str(decimFactor*sweepfreq[i]/1e06)+' MHz Filtered Signal')
	# 	plt.subplot(311)
	# 	plt.title('Input Cosine Wave at '+str(sweepfreq[i]/1e06)+' MHz')
	# 	plt.xlabel('Time ($\mu{s}$)')
	# 	plt.ylabel('Magnitude')
	# 	plt.plot(sweepTimePts/1.0e-06,inputSweep[i])

	# 	plt.subplot(312)
	# 	plt.title('Filtered Output Signal at '+str(decimFactor*sweepfreq[i]/1e06)+' MHz')
	# 	plt.xlabel('Time ($\mu{s}$)')
	# 	plt.ylabel('Magnitude')
	# 	plt.plot(polyDataSweepPts[i]/1.0e-06,polyDataSweep[i])

	# 	plt.subplot(313)
	# 	plt.title('Magnitude of Frequency Response')
	# 	plt.xlabel('Normalized Frequency')
	# 	plt.ylabel('Magnitude in dB')
	# 	plt.plot(fftFreq[i],polyDataSweepFFTMagResponse[i]	)
	# plt.show()

#--------------------------------------------------------------------------------------------#
# 				SciPy FIR filter coefficient Generation 									 #
#--------------------------------------------------------------------------------------------#

def makeFIRCoefs(samplingFreq,IFFreq,bandwidth,numPoints,numTaps):
	IFFreq = IFFreq*1e06
	(b,a) = signal.iirdesign(IFFreq/2, IFFreq, 3, 30, ftype='butter')
	timeStep = 1.0/samplingFreq
	timePts = np.arange(0, numPoints*timeStep,timeStep) 
	stepImpulse = [0 if i<len(timePts)/2 else 1 for i in range(len(timePts))]
	unitImpulse = [1 if i==0 else 0 for i in range(len(timePts))]
	nIFFreq=IFFreq/(samplingFreq/2)
	nbandwidth=bandwidth/(samplingFreq/2)
	print 'Cuttoff frequency: ', nIFFreq, 'Hz\n'
	print 'building FIR coefficients with {} taps...\n'.format(numTaps)
	firCoefs=signal.firwin(float(numTaps),0.09*samplingFreq,width=None,window='hamming',pass_zero=True,scale=True,nyq=samplingFreq/2)

	# step impulse for polyphase filter input test:
	with open('/home/nick/firFilter/stepFunction'+str(numPoints)+'.txt','w') as stepfid:
		stepfid.write('signal myStepImpulse : vector_array :=(')		
		stepfid.write(','.join(['x"{0:04X}"'.format(x) for x in stepImpulse])+');')
	with open('/home/nick/firFilter/unitImpulse'+str(numPoints)+'.txt','w') as impfid:
		impfid.write('signal myUnitImpulse : vector_array :=(')
		impfid.write(','.join(['x"{0:04X}"'.format(x) for x in unitImpulse])+');')

	# for i in range(len(firCoefs)):
	# 	print 'Reload index {} = {number:.{width}f}'.format(i,number=firCoefs[i],width=32)
	
	# two's complement filter coefficients for VHDL:
	with open('/home/nick/firFilter/firCoefs'+str(int(numTaps))+'taps.coe','w') as fid:
		fid.write('radix=10;\ncoefdata=')
		fid.write(','.join(['{number:.{width}f}'.format(number=f,width=32) for f in firCoefs])+';')
	with open('/home/nick/firFilter/firCoefs'+str(IFFreq/1.e06)+'MHzVHDL.txt','w') as fid2:
		fid2.write('type vector_arrayTaps is array ('+str(numTaps-1)+' downto 0) of std_logic_vector(15 downto 0);\nsignal myReload : vector_arrayTaps:=(')
		fid2.write(','.join(['x"{0:04X}"'.format((~int(np.abs(x*pow(2,16-1)))&0xfff)+1) for x in firCoefs]) + ');')

	# IIR filter coefficients written to VHDL:
	with open('/home/nick/firFilter/iirCoefs'+str(int(IFFreq/1.e06))+'MHzVHDL.txt','w') as iirfid:
		iirfid.write('signal loadIIRCoefsA : vector_array :=(')
		iirfid.write(','.join(['x"{0:04X}"'.format((~int(np.abs(x*pow(2,64-1)))&0xffff)+1) for x in a]) + ');')
		iirfid.write('\nsignal loadIIRCoefsB : vector_array :=(')
		iirfid.write(','.join(['x"{0:04X}"'.format((~int(np.abs(x*pow(2,64-1)))&0xffff)+1) for x in b]) + ');')


#--------------------------------------------------------------------------------------------#
#	 				Main to call all functions defined above 								 #
#--------------------------------------------------------------------------------------------#

def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-s','--numPoints',dest='numPoints',type=int,help='Number of numPoints')
   parser.add_argument('-o','--functionOption',dest='functionOption',help='Select option: (diffHardwareAndSim, makeCosWave, plot, plotSim)')
   parser.add_argument('-f','--samplingFreq',dest='sfreq',type=float,help='sampling frequency in Hz')
   parser.add_argument('-c','--cosFreq',dest='cfreq',type=float,help='frequency for cos wave in Hz')
   parser.add_argument('-b','--bandwidth',dest='bandwidth',type=float,help='bandwidth, equal to channel linewidth')
   parser.add_argument('-n','--numTaps',dest='numTaps',type=float,help='Number of coefficients in FIR Filter')
   parser.add_argument('-t','--simTime',dest='simTime',type=float,help='Simulation Time in seconds')
   parser.add_argument('-d','--decimFactor',dest='decimFactor',type=int,help='Decimation Factor of Polyphase filter')
   parser.add_argument('-m','--matlabFlag',dest='matlabFlag',type=str,help='matlab=Load matlab files, VHDL=Load iSim files')
   parser.add_argument('-r','--frequencyRange',dest='frange',type=list,help='range of frequencies (MHz), i.e. [1,20]')
   parser.add_argument('-l','--iirFilterLength',dest='filterLength',type=int,help='Length of IIR Filter, number of coefficients')
   args = parser.parse_args()

   #./diffBoardAndSim -o makeCosWave -f samplingFreq -c cosFreq -s numPoints -d decimFactor
   if (args.functionOption=='makeCosWave'):
   	make_cos_wave(args.cfreq, args.sfreq, args.numPoints, args.decimFactor)
   	print '\nRunning ', str(args.functionOption), ' with sampling frequency: ', str(args.sfreq), 'Hz.'
   # ./diffBoardAndSim -o diffBoardAndSim -s numPoints
   elif (args.functionOption=='diffHardwareAndSim'):
   	diffHardwareAndSim(args.numPoints)	
   # ./diffBoardAndSim -o plot -s numPoints
   elif (args.functionOption=='plot'):
   	print '\nPlotting input and output signals sampled at ',str(args.sfreq), 'Hz...'
   	readAndPlot(args.numPoints)
   # ./diffBoardAndSim -o getSinAndCos -s numPoints -c cosFreq -f samplingFreq
   elif (args.functionOption=='getSinAndCos'):
   	print '\nProcessing sin and cos VCD files...\n'
   	getSinAndCos(args.cfreq, args.sfreq, args.numPoints)
   # ./diffBoardAndSim -o plotSim2 -s numPoints -c cosFreq -f samplingFreq -d decimFactor -t simTim -m matlabflag -f freqRange -l iirFilterLength -n numTaps
   elif (args.functionOption=='plotSim2'):
   	justPlotSim2(args.cfreq, args.sfreq, args.numPoints, args.numTaps, args.decimFactor, args.simTime, args.matlabFlag, args.frange, args.filterLength)
   # ./diffBoardAndSim -o plotSimFinal 	-s numPoints -c cosFreq -f samplingFreq -d decimFactor -t simTim -m matlabflag -f freqRange -l iirFilterLength -n numTaps
   elif (args.functionOption=='plotSimFinal'):
   	plotTotalChannelizer(args.cfreq, args.sfreq, args.numPoints, args.numTaps, args.decimFactor, args.simTime, args.matlabFlag, args.frange, args.filterLength)
   # ./diffBoardAndSim -o firCoefs -s numPoints -c cosFreq -n numTaps -b bandwidth -f samplingFreq 
   elif(args.functionOption=='firCoefs'):
   	makeFIRCoefs(args.sfreq,args.cfreq,args.bandwidth,args.numPoints,args.numTaps)
   print '\nSelected operation: ', args.functionOption
   print '\nNumber of numPoints: ', args.numPoints
   if (args.cfreq != '' and args.sfreq != ''):
   	print '\nUsing input signal with cosine frequency', args.cfreq, 'MHz and sampling frequency', args.sfreq/1e06, 'MHz\n'
if __name__ == "__main__":
   main(sys.argv[1:])

