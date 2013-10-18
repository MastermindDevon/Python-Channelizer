#!/usr/bin/python
# 10/18/13
# Raytheon BBN Technologies
# Nick Materise

# Script to call Opal Kelly Board
# Run Signal Processing Chain
# Collect and Plot Results

# command line Arguments:
# ----------------------------------------------------------------------------------------- #
# 																							#
# -i inputFreq 		= input frequency (Hz) 													#
# -s samplingFreq 	= sampling rate (Samples/second) 										#
# 																							#
# -a amplitude		= amplitude fit parameter 												#
# -p phase 			= phase shift fit parameter 											#
# -o dc_offset 		= dc offset fit parameter 												#
# -n numPoints 		= number of points in input pulse										#
# -w window 		= window function name (boxcar,blackman,hann,hamming)					#
# 																							#
# -d decimFactor 	= decimation factor of FIR filter 										#
# -l project_dir	= output destination for input signal (project directory) 				#
#																							#
# -m module 		= vhdl module to plot (Demod,FIRFilter,IIRFilter)						#
# ----------------------------------------------------------------------------------------- #




# --------------------------------Example Commandline--------------------------------------------------- #
#																								 		 #
#	./dspOpalKelly6010.py -i 10e06 -s 500e06 -d 4 -p ~/project_dir -o plot -m module		 			 # 
#																								 		 #
# --------------------------------Example Commandline--------------------------------------------------- #



# import ok for Opal Kelly FrontPanel API
import ok
import time
import subprocess
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

xem = ok.FrontPanel()
xem.OpenBySerial("")
xem.LoadDefaultPLLConfiguration()

xem.ResetFPGA()

def generate_inputs(inputFreq,samplingFreq,decimFactor,numPoints,project_dir,options,window,module):
	print 'Generating input signals'
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
	subprocess.check_call(["makeCosWave.py","-c",str(inputFreq/1e06),"-s",str(samplingFreq),"-d",str(decimFactor),"-n",str(int(numPoints*2)),"-p",str(project_dir),"-r","1e05","-z","yes","-g","no"])
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'

	print '\nGenerating '+str(window)+' window coefficients'
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
	subprocess.check_call(["generateWindowCoefs.py","-l",str(int(numPoints)),"-n",str(int(numPoints*2)),"-p",str(project_dir),"-w",str(window)])
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'

	inputSignal=np.genfromtxt(str(project_dir)+'/fpgaData'+str(int(numPoints*2))+'.txt',dtype=np.int16)
	windowCoef=np.genfromtxt(str(project_dir)+'/fpgaCoefData'+str(int(numPoints*2))+'_'+str(window)+'.txt', dtype=np.int32)

	return inputSignal,windowCoef


def init_fpga(inputSignal,windowCoef,inputFreq,samplingFreq,decimFactor,numPoints,project_dir,options,window,module):
	
	project_dir_stripped=regex.sub('^.*\/','',project_dir)
	
	# initialize output signals:

	outputRe=np.zeros(int(numPoints))
	outputIm=np.zeros(int(numPoints))

	# read test vectors (inputSignalData, coefficients, ):
	print '\n-------------------------------------------------------------------------\n'
	print 'Starting Opal Kelly XEM 6010 Analysis...\n'
	print 'Writing in {} directory'.format(project_dir)
	print 'Configuring FPGA with {}/{}_Top.bit...'.format(str(project_dir),str(project_dir_stripped))
	print '\n-------------------------------------------------------------------------\n'
	
	xem.ConfigureFPGA(str(project_dir)+'/'+str(project_dir_stripped)+'_Top.bit')

	# pulse reset line:
	wireInLines = 0x0001
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	wireInLines = 0x0000
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	# write input signal data and coefficients to block ram:
	print 'Loading window coefficients...'
	wireInLines=0x0002
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()
	for i in range(int(numPoints)):
		xem.SetWireInValue(0x07,int(i))
		xem.SetWireInValue(0x05,0x7f)
		xem.SetWireInValue(0x06,0xff)
		xem.UpdateWireIns()
		xem.ActivateTriggerIn(0x40,0)

	print 'Loading input signal values...'
	for i in range(int(numPoints*decimFactor)):
		xem.SetWireInValue(0x03,int(i))
		xem.SetWireInValue(0x02,int(np.uint16(inputSignal[i])))
		xem.UpdateWireIns()
		xem.ActivateTriggerIn(0x40,0)

	wireInLines = 0x0000
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	print 'Start Accumulating...'
	wireInLines=0x000C
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	# compute phase increment:
	print 'Writing phase increment to NCO...'
	phaseInc = int(np.floor((inputFreq/(samplingFreq/decimFactor))*pow(2,16)))
	print 'Phase increment set to 0x{0:04X}...'.format(phaseInc)
	xem.SetWireInValue(0x01,phaseInc)
	xem.UpdateWireIns()

	print 'Wait 13 mirco seconds for RAM to fill...'
	time.sleep(13e-03)

	print 'Read results from accumulator...\n\n'
	for i in range(int(numPoints)):
		xem.SetWireInValue(0x04,int(i))
		xem.UpdateWireIns()
		xem.UpdateWireOuts()
		outputRe[i]=(xem.GetWireOutValue(0x20)<<64) | (xem.GetWireOutValue(0x21)<<32) | (xem.GetWireOutValue(0x22)<<16) | (xem.GetWireOutValue(0x23))
		outputIm[i]=(xem.GetWireOutValue(0x24)<<64) | (xem.GetWireOutValue(0x25)<<32) | (xem.GetWireOutValue(0x26)<<16) | (xem.GetWireOutValue(0x27))
		# print '[ [0x{0:04X}], [0x{0:04X}], [0x{0:04X}], [0x{0:04X}]\t[0x{0:04X}], [0x{0:04X}], [0x{0:04X}], [0x{0:04X}] ]:\t[0x{0:016X}\t0x{0:016X}]'.format(xem.GetWireOutValue(0x20),
		xem.GetWireOutValue(0x21),xem.GetWireOutValue(0x22),xem.GetWireOutValue(0x23),
		xem.GetWireOutValue(0x24),xem.GetWireOutValue(0x25),xem.GetWireOutValue(0x26),xem.GetWireOutValue(0x27),outputRe[i],outputIm[i])

	# ------------------------------------------------------------------------------ #

	# 5) Write Results and Plot
	
	print 'Writing Results to file...'
	wireInLines=0x0000
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	with open(str(project_dir)+'/fpgaOutputRe'+str(int(numPoints*2))+'_'+str(window)+'.txt','w') as fid:
		for i in range(len(outputRe)):
			fid.write(str(outputRe[i])+'\n')
	with open(str(project_dir)+'/fpgaOutputIm'+str(int(numPoints*2))+'_'+str(window)+'.txt','w') as fid:
		for i in range(len(outputIm)):
			fid.write(str(outputIm[i])+'\n')

	# 6) Call python scripts from outside
	if(options=='plot'):
		print '\nPlotting outputs from Opal Kelly Board...\n'	
		print '\n-------------------------------------\n'
		print 'Plotting Arguments Selected:\n\ninputFreq: {} MHz\nsamplingFreq: {} MHz\ndecimFactor: {} \nproject_dir: {}\nmodule: {}'.format(inputFreq/1e06,samplingFreq/1e06,decimFactor,project_dir,module)
		print '\n-------------------------------------\n'
		
		subprocess.check_call(["plotComplexSignal.py","-i",str(inputFreq),"-s",str(samplingFreq),"-d",str(decimFactor),"-p",str(project_dir),"-m",str(module),"-o",'fpga'])
	# ------------------------------------------------------------------------------ #

	outputData = np.vstack([outputRe,outputIm])

	return outputData

	xem.ResetFPGA()
	print '\nReseting FPGA...\n'


def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-s','--samplingFreq',dest='sfreq',type=float,help='sampling frequency in Hz (samples/second)')
   parser.add_argument('-i','--inputFreq',dest='ifreq',type=float,help='frequency for cos wave in MHz')
   parser.add_argument('-d','--decimFactor',dest='decimFactor',type=int,help='Decimation Factor of Polyphase filter')
   parser.add_argument('-n','--numPoints',dest='numPoints',type=float,help='Number of points in pulse')
   parser.add_argument('-p','--project_dir',dest='pdir',type=str,help='project file path')
   parser.add_argument('-o','--options',dest='options',type=str,help='plot, run, debug')
   parser.add_argument('-w','--window',dest='window',type=str,help='Type of window function (boxcar,hamming,hann,blackman)\ndefault=boxcar')
   parser.add_argument('-m','--module',dest='module',type=str,help='vhdl module to plot')
   args = parser.parse_args()

   # function call in main:
   inputs,window = generate_inputs(args.ifreq,args.sfreq,args.decimFactor,args.numPoints,args.pdir,args.options,args.window,args.module)
   init_fpga(inputs,window,args.ifreq,args.sfreq,args.decimFactor,args.numPoints,args.pdir,args.options,args.window,args.module)

if __name__ == "__main__":
   main(sys.argv[1:])