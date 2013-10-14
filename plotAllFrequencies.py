#!/usr/bin/python



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
#					Plot fits of frequencies in "sweepfreq" 								 #
#--------------------------------------------------------------------------------------------#

def sweepingPlot(sweepfreq,samplingFreq,p0,p1,p2,decimFactor,project_dir,sweep,inputFreq):
	project_dir=regex.sub('\/$','',project_dir)
	project_dir_stripped=regex.sub('\/{3}.*?',project_dir)
	print '\nReading {}/output from project directory: {}'.format(project_dir_stripped,project_dir)

	myString=[str(int(i/pow(10,5))) for i in sweepfreq]
	
	timeStep=1/samplingFreq
	cosoutput=[np.genfromtxt(str(project_dir)+'/cosoutput'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	cosTpts=[np.arange(0,len(co)*timeStep,timeStep) for co in cosoutput]
	
	outputData=[np.genfromtxt(str(project_dir)+'/'+str(project_dir_stripped)+'output'+str(myString[i])+'MHz.dat',dtype=np.int16) for i in range(len(sweepfreq))]
	outputTpts=[np.arange(0,len(od)*timeStep,timeStep) for do in outputData]

	fig00=plt.figure(17)
	fig00.suptitle(str(title))

	if (sweep=='singleFreq' and inputFreq!=0):
		cosoutput=np.genfromtxt(str(project_dir)+'/cosoutput'+str(inputFreq)+'MHz.dat',dtype=np.int16)
		cosTpts=np.arange(0,len(cos_output)*timeStep,timeStep)

		plt.subplot(3,1,1)
	    plt.title(str(inputFreq/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq/1e06)+' MHz Output')
	    plt.plot(cosTpts,cosoutput)
	    plt.xlabel('Time (s)')
	    plt.ylabel('Magnitude')
	    
	    # plot the output and cooresponding fit
	    plt.subplot(3,1,2)
	    plt.title(str(inputFreq/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq/1e06)+' MHz Output')
	    plt.xlabel('Time (s)')
	    plt.ylabel('Magnitude')
	    plt.plot(outputTpts[i],np.real(outputData[i]),'r',label='Filtered Output')
	    plt.plot(cosTpts[i],p0[i]*np.cos(2*np.pi*inputFreq*cosTpts[i]*decimFactor+p1[i])+p2[i],'b',label='Fitted Output')
	    plt.legend(loc='lower right')
	    
	    # plot the output and cooresponding fit
	    plt.subplot(3,1,3)
	    plt.title(str(inputFreq/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*inputFreq/1e06)+' MHz Output')
	    plt.xlabel('Time (s)')
	    plt.ylabel('Magnitude')
	    plt.plot(outputTpts[i],np.imag(outputData[i]),'r',label='Filtered Output')
	    plt.plot(cosTpts[i],p0[i]*np.cos(2*np.pi*inputFreq*cosTpts[i]*decimFactor+p1[i])+p2[i],'b',label='Fitted Output')
	    plt.legend(loc='lower right')
	    plt.show()


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
	    plt.plot(outputTpts[i],np.real(outputData[i]),'r',label='Filtered Output')
	    plt.plot(cosTpts[i],p0[i]*np.cos(2*np.pi*sweepfreq[i]*cosTpts[i]*decimFactor+p1[i])+p2[i],'b',label='Fitted Output')
	    plt.legend(loc='lower right')
	    
	    # plot the output and cooresponding fit
	    plt.subplot(3,1,3)
	    plt.title(str(sweepfreq[i]/1e06)+' MHz Input Cosine Wave, '+str(decimFactor*sweepfreq[i]/1e06)+' MHz Output')
	    plt.xlabel('Time (s)')
	    plt.ylabel('Magnitude')
	    plt.plot(outputTpts[i],np.imag(outputData[i]),'r',label='Filtered Output')
	    plt.plot(cosTpts[i],p0[i]*np.cos(2*np.pi*sweepfreq[i]*cosTpts[i]*decimFactor+p1[i])+p2[i],'b',label='Fitted Output')
	    plt.legend(loc='lower right')
	    plt.show()

	plt.close()

def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-f','--sweepfreq',dest='sweepfreq',help='List of frequencies in MHz')
   parser.add_argument('-s','--samplingFreq',dest='sfreq',type=float,help='sampling frequency in Hz')
   parser.add_argument('-i','--inputFreq',dest='ifreq',type=float,help='frequency for cos wave in MHz')
   parser.add_argument('-d','--decimFactor',dest='decimFactor',type=int,help='Decimation Factor of Polyphase filter')
   parser.add_argument('-p','--file_path',dest='fpath',type=str,help='project file path')
   parser.add_argument('-r','--resolution',dest='rez',type=float,help='frequency resolution in Hz')
   parser.add_argument('-z','--zero_pad',dest='zpad',type=str,help='zero padding on/off (True/False)')
   args = parser.parse_args()

   # function call in main:
   make_cos_wave(args.cfreq,args.sfreq,args.numPoints,args.decimFactor,args.fpath,args.rez,args.zpad)
   # Display inputs:
   if (args.cfreq != '' and args.sfreq != ''):
   	print '\nCosine frequency: {} MHz \nSampling frequency: {} MHz'.format(args.cfreq,args.sfreq/1e06)
   	print 'Frequency resolution: {} Hz'.format(args.rez)
   	print 'Writing results to {} directory...\n'.format(str(args.fpath))
if __name__ == "__main__":
   main(sys.argv[1:])

