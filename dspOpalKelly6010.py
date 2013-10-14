#!/usr/bin/python
# 9/26/13
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

def init_fpga(inputFreq,samplingFreq,decimFactor,numPoints,project_dir,options,window,module):
	# initialize output signals:

	outputRe=np.zeros(int(numPoints*4))
	outputIm=np.zeros(int(numPoints*4))

	firdata=np.zeros(int(numPoints*4))
	demoddata=np.zeros(int(numPoints*4))

	# read test vectors (inputSignalData, coefficients, ):
	print '\n-------------------------------------------------------------------------\n'
	print 'Starting Opal Kelly XEM 6010 Analysis...\n'
	print 'Writing in {} directory'.format(project_dir)
	print '\n-------------------------------------------------------------------------\n'
	
	# with open('','r') as fid:
	# 	inputSignalData = fid.read()
	# with open('') as fid:
	# 	coefdata = fid.read()

	xem.ConfigureFPGA(str(project_dir)+'_Top.bit')

	# test FPGA LED Signals:
	print '\nLighting Test LED'
	led=0x01
	xem.SetWireInValue(0x0E,led)
	xem.UpdateWireIns()

	# pulse reset line:
	wireInLines = 0x0001
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()
	wireInLines = 0x0000
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	# write input signals out to board:
	print 'Generating input signals'
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
	subprocess.check_call(["/home/nick/dualPortblockRAMdemod_top/makeCosWave.py","-c",str(inputFreq/1e06),"-s",str(samplingFreq),"-d",str(decimFactor),"-n",str(int(numPoints*2)),"-p",str(project_dir),"-r","1e05","-z","yes","-g","no"])
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'

	print '\nGenerating '+str(window)+' window coefficients'
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
	subprocess.check_call(["/home/nick/dualPortblockRAMdemod_top/generateWindowCoefs.py","-l",str(int(numPoints)),"-n",str(int(numPoints*2)),"-p",str(project_dir),"-w",str(window)])
	print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'

	inputSignal=np.genfromtxt(str(project_dir)+'/fpgaData'+str(int(numPoints*2))+'.txt',dtype=np.int16)
	windowCoef=np.genfromtxt(str(project_dir)+'/fpgaCoefData'+str(int(numPoints*2))+'_'+str(window)+'.txt', dtype=np.int32)

	print '\nLoading input signal values...'
	# write input signal data and coefficients to block ram:

	for i in range(int(numPoints*4)):
		xem.ActivateTriggerIn(0x40,0)
		xem.SetWireInValue(0x03,int(i))
		xem.SetWireInValue(0x02,int(np.uint16(inputSignal[i])))
		xem.UpdateWireIns()


	print 'Loading window coefficients...'
	wireInLines=0x0002
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()
	for i in range(int(numPoints*4)):
		xem.ActivateTriggerIn(0x40,0)
		xem.SetWireInValue(0x03,int(i))
		xem.SetWireInValue(0x05,int(0))
		xem.SetWireInValue(0x06,int(windowCoef[i]))
		xem.UpdateWireIns()

	print 'Signaling to FIRFilter to accept valid data...'
	wireInLines=0x0008
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	# compute phase increment:
	print 'Writing phase increment to NCO...'
	phaseInc = int(np.floor((inputFreq/(samplingFreq/decimFactor))*pow(2,16)))
	xem.SetWireInValue(0x01,phaseInc)
	xem.UpdateWireIns()

	print 'Start Accumulating...'
	wireInLines=0x0004
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	print 'Read results from accumulator...'
	for i in range(int(numPoints*4)):
		if (xem.GetWireOutValue(0x20) != 0 or xem.GetWireOutValue(0x21) != 0 
			or xem.GetWireOutValue(0x22) != 0 or xem.GetWireOutValue(0x23)
			 != 0 or xem.GetWireOutValue(0x24) != 0 or xem.GetWireOutValue(0x25) != 0 
			 or xem.GetWireOutValue(0x26) != 0 or xem.GetWireOutValue(0x27) != 0):
			print '[ [{}] [{}] [{}] [{}]\t[{}] [{}] [{}] [{}] ]'.format(xem.GetWireOutValue(0x20),
				xem.GetWireOutValue(0x21),xem.GetWireOutValue(0x22),xem.GetWireOutValue(0x23),
				xem.GetWireOutValue(0x24),xem.GetWireOutValue(0x25),xem.GetWireOutValue(0x26),xem.GetWireOutValue(0x27))
		outputRe[i]=(xem.GetWireOutValue(0x20)<<64) + (xem.GetWireOutValue(0x21)<<32) + (xem.GetWireOutValue(0x22)<<16) + (xem.GetWireOutValue(0x23))
		outputIm[i]=(xem.GetWireOutValue(0x24)<<64) + (xem.GetWireOutValue(0x25)<<32) + (xem.GetWireOutValue(0x26)<<16) + (xem.GetWireOutValue(0x27))
		firdata[i]=xem.GetWireOutValue(0x28)
		demoddata[i]=xem.GetWireOutValue(0x29)
		 # print '[{}]\t[{}]'.format(xem.GetWireOutValue(0x28),xem.GetWireOutValue(0x29))
	# ------------------------------------------------------------------------------ #

	# 5) Write Results and Plot
	
	print 'Writing Results to file...'
	wireInLines=0x0000
	xem.SetWireInValue(0x00,wireInLines)
	xem.UpdateWireIns()

	with open(str(project_dir)+'/fpgaOutputRe'+str(int(numPoints*2))+'_'+str(window)+'.txt','w') as fid:
		for i in range(len(outputRe)):
			fid.write('\n'.join(str(outputRe[i])))
	with open(str(project_dir)+'/fpgaOutputIm'+str(int(numPoints*2))+'_'+str(window)+'.txt','w') as fid:
		for i in range(len(outputIm)):
			fid.write('\n'.join(str(outputIm[i])))

	# 6) Call python scripts from outside
	if(options=='plot'):
		print '\nPlotting outputs from Opal Kelly Board...\n'	
		print '\n-------------------------------------\n'
		print 'Plotting Arguments Selected:\n\ninputFreq: {} MHz\nsamplingFreq: {} MHz\ndecimFactor: {} \nproject_dir: {}\nmodule: {}'.format(inputFreq/1e06,samplingFreq/1e06,decimFactor,project_dir,module)
		print '\n-------------------------------------\n'
		
		subprocess.check_call(["/home/nick/dualPortblockRAMdemod_top/plotComplexSignal.py","-i",str(inputFreq),"-s",str(samplingFreq),"-d",str(decimFactor),"-p",str(project_dir),"-m",str(module)])
	# ------------------------------------------------------------------------------ #

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
   init_fpga(args.ifreq,args.sfreq,args.decimFactor,args.numPoints,args.pdir,args.options,args.window,args.module)

if __name__ == "__main__":
   main(sys.argv[1:])