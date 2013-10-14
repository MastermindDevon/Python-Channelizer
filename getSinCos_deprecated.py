#!/usr/bin/python
# python script to generate new hardware output.
# handles the input signal, output file I/O, and plotting functions
# 8/6/13
# $1=numPoints

# argslist:
# -s numPoints
# -c cosFreq
# -o functionOption
# -f samplingFreq

import sys
import argparse
import numpy as np
import math 
import matplotlib.pyplot as plt
import matplotlib.mlab as mylab
import csv
import Verilog_VCD
from scipy import signal
from scipy.optimize import curve_fit

def getSinAndCos(cosFreq, samplingFreq, numPoints):
	simValuesDict = Verilog_VCD.parse_vcd('/home/nick/dualPortblockRAMdemod_top/mydumpfile')
	sindata0Reader=simValuesDict['G!']['tv']
	cosdata0Reader=simValuesDict['W!']['tv']
	sindata1Reader=simValuesDict['H!']['tv']
	cosdata1Reader=simValuesDict['X!']['tv']
	sindata2Reader=simValuesDict['I!']['tv']
	cosdata2Reader=simValuesDict['Y!']['tv']
	sindata3Reader=simValuesDict['J!']['tv']
	cosdata3Reader=simValuesDict['Z!']['tv']
	print 'half byte done...'
	sindata4Reader=simValuesDict['K!']['tv']
	cosdata4Reader=simValuesDict['[!']['tv']
	sindata5Reader=simValuesDict['L!']['tv']
	cosdata5Reader=simValuesDict['\!']['tv']
	sindata6Reader=simValuesDict['M!']['tv']
	cosdata6Reader=simValuesDict[']!']['tv']
	sindata7Reader=simValuesDict['N!']['tv']
	cosdata7Reader=simValuesDict['^!']['tv']
	print 'first byte processed...'
	sindata8Reader=simValuesDict['O!']['tv']
	cosdata8Reader=simValuesDict['_!']['tv']
	sindata9Reader=simValuesDict['P!']['tv']
	cosdata9Reader=simValuesDict['`!']['tv']
	sindata10Reader=simValuesDict['Q!']['tv']
	cosdata10Reader=simValuesDict['a!']['tv']
	sindata11Reader=simValuesDict['R!']['tv']
	cosdata11Reader=simValuesDict['b!']['tv']
	print 'next half byte done...'
	sindata12Reader=simValuesDict['S!']['tv']
	cosdata12Reader=simValuesDict['c!']['tv']
	sindata13Reader=simValuesDict['T!']['tv']
	cosdata13Reader=simValuesDict['d!']['tv']
	sindata14Reader=simValuesDict['U!']['tv']
	cosdata14Reader=simValuesDict['e!']['tv']
	sindata15Reader=simValuesDict['V!']['tv']
	cosdata15Reader=simValuesDict['f!']['tv']

	print 'building sin change points and diff arrays...'
	sinchangePts0 = [x[0]/timeStep for x in sindata0Reader]
	sinblockLengths0 = np.diff(sinchangePts0)
	sinr0 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths0[::2]], [np.ones(x) for x in sinblockLengths0[1::2]])]
	sinfinalVector0 = np.hstack(tuple(sinr0))
	
	sinchangePts1 = [x[0]/timeStep for x in sindata1Reader]
	sinblockLengths1 = np.diff(sinchangePts1)
	sinr1 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths1[::2]], [np.ones(x) for x in sinblockLengths1[1::2]])]
	sinfinalVector1 = np.hstack(tuple(sinr1))
	
	sinchangePts2 = [x[0]/timeStep for x in sindata2Reader]
	sinblockLengths2 = np.diff(sinchangePts2)
	sinr2 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths2[::2]], [np.ones(x) for x in sinblockLengths2[1::2]])]
	sinfinalVector2 = np.hstack(tuple(sinr2))
	
	sinchangePts3 = [x[0]/timeStep for x in sindata3Reader]
	sinblockLengths3 = np.diff(sinchangePts3)
	sinr3 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths3[::2]], [np.ones(x) for x in sinblockLengths3[1::2]])]
	sinfinalVector3 = np.hstack(tuple(sinr3))
	
	sinchangePts4 = [x[0]/timeStep for x in sindata4Reader]
	sinblockLengths4 = np.diff(sinchangePts4)
	sinr4 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths4[::2]], [np.ones(x) for x in sinblockLengths4[1::2]])]
	sinfinalVector4 = np.hstack(tuple(sinr4))
	
	sinchangePts5 = [x[0]/timeStep for x in sindata5Reader]
	sinblockLengths5 = np.diff(sinchangePts5)
	sinr5 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths5[::2]], [np.ones(x) for x in sinblockLengths5[1::2]])]
	sinfinalVector5 = np.hstack(tuple(sinr5))
	
	sinchangePts6 = [x[0]/timeStep for x in sindata6Reader]
	sinblockLengths6 = np.diff(sinchangePts6)
	sinr6 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths6[::2]], [np.ones(x) for x in sinblockLengths6[1::2]])]
	sinfinalVector6 = np.hstack(tuple(sinr6))
	
	sinchangePts7 = [x[0]/timeStep for x in sindata7Reader]
	sinblockLengths7 = np.diff(sinchangePts7)
	sinr7 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths7[::2]], [np.ones(x) for x in sinblockLengths7[1::2]])]
	sinfinalVector7 = np.hstack(tuple(sinr7))
	
	sinchangePts8 = [x[0]/timeStep for x in sindata8Reader]
	sinblockLengths8 = np.diff(sinchangePts8)
	sinr8 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths8[::2]], [np.ones(x) for x in sinblockLengths8[1::2]])]
	sinfinalVector8 = np.hstack(tuple(sinr8))
	
	sinchangePts9 = [x[0]/timeStep for x in sindata9Reader]
	sinblockLengths9 = np.diff(sinchangePts9)
	sinr9 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths9[::2]], [np.ones(x) for x in sinblockLengths9[1::2]])]
	sinfinalVector9 = np.hstack(tuple(sinr9))
	
	sinchangePts10 = [x[0]/timeStep for x in sindata10Reader]
	sinblockLengths10 = np.diff(sinchangePts10)
	sinr10 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths10[::2]], [np.ones(x) for x in sinblockLengths10[1::2]])]
	sinfinalVector10 = np.hstack(tuple(sinr10))
	
	sinchangePts11 = [x[0]/timeStep for x in sindata11Reader]
	sinblockLengths11 = np.diff(sinchangePts11)
	sinr11 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths11[::2]], [np.ones(x) for x in sinblockLengths11[1::2]])]
	sinfinalVector11 = np.hstack(tuple(sinr11))
	
	sinchangePts12 = [x[0]/timeStep for x in sindata12Reader]
	sinblockLengths12 = np.diff(sinchangePts12)
	sinr12 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths12[::2]], [np.ones(x) for x in sinblockLengths12[1::2]])]
	sinfinalVector12 = np.hstack(tuple(sinr12))
	
	sinchangePts13 = [x[0]/timeStep for x in sindata13Reader]
	sinblockLengths13 = np.diff(sinchangePts13)
	sinr13 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths13[::2]], [np.ones(x) for x in sinblockLengths13[1::2]])]
	sinfinalVector13 = np.hstack(tuple(sinr13))
	
	sinchangePts14 = [x[0]/timeStep for x in sindata14Reader]
	sinblockLengths14 = np.diff(sinchangePts14)
	sinr14 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths14[::2]], [np.ones(x) for x in sinblockLengths14[1::2]])]
	sinfinalVector14 = np.hstack(tuple(sinr14))
	
	sinchangePts15 = [x[0]/timeStep for x in sindata15Reader]
	sinblockLengths15 = np.diff(sinchangePts15)
	sinr15 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in sinblockLengths15[::2]], [np.ones(x) for x in sinblockLengths15[1::2]])]
	sinfinalVector15 = np.hstack(tuple(sinr15))


	print 'building cos change points and diff arrays...'
	coschangePts0 = [x[0]/timeStep for x in cosdata0Reader]
	cosblockLengths0 = np.diff(coschangePts0)
	cosr0 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths0[::2]], [np.ones(x) for x in cosblockLengths0[1::2]])]
	cosfinalVector0 = np.hstack(tuple(cosr0))
	
	coschangePts1 = [x[0]/timeStep for x in cosdata1Reader]
	cosblockLengths1 = np.diff(coschangePts1)
	cosr1 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths1[::2]], [np.ones(x) for x in cosblockLengths1[1::2]])]
	cosfinalVector1 = np.hstack(tuple(cosr1))
	
	coschangePts2 = [x[0]/timeStep for x in cosdata2Reader]
	cosblockLengths2 = np.diff(coschangePts2)
	cosr2 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths2[::2]], [np.ones(x) for x in cosblockLengths2[1::2]])]
	cosfinalVector2 = np.hstack(tuple(cosr2))
	
	coschangePts3 = [x[0]/timeStep for x in cosdata3Reader]
	cosblockLengths3 = np.diff(coschangePts3)
	cosr3 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths3[::2]], [np.ones(x) for x in cosblockLengths3[1::2]])]
	cosfinalVector3 = np.hstack(tuple(cosr3))
	
	coschangePts4 = [x[0]/timeStep for x in cosdata4Reader]
	cosblockLengths4 = np.diff(coschangePts4)
	cosr4 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths4[::2]], [np.ones(x) for x in cosblockLengths4[1::2]])]
	cosfinalVector4 = np.hstack(tuple(cosr4))
	
	coschangePts5 = [x[0]/timeStep for x in cosdata5Reader]
	cosblockLengths5 = np.diff(coschangePts5)
	cosr5 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths5[::2]], [np.ones(x) for x in cosblockLengths5[1::2]])]
	cosfinalVector5 = np.hstack(tuple(cosr5))
	
	coschangePts6 = [x[0]/timeStep for x in cosdata6Reader]
	cosblockLengths6 = np.diff(coschangePts6)
	cosr6 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths6[::2]], [np.ones(x) for x in cosblockLengths6[1::2]])]
	cosfinalVector6 = np.hstack(tuple(cosr6))
	
	coschangePts7 = [x[0]/timeStep for x in cosdata7Reader]
	cosblockLengths7 = np.diff(coschangePts7)
	cosr7 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths7[::2]], [np.ones(x) for x in cosblockLengths7[1::2]])]
	cosfinalVector7 = np.hstack(tuple(cosr7))
	
	coschangePts8 = [x[0]/timeStep for x in cosdata8Reader]
	cosblockLengths8 = np.diff(coschangePts8)
	cosr8 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths8[::2]], [np.ones(x) for x in cosblockLengths8[1::2]])]
	cosfinalVector8 = np.hstack(tuple(cosr8))
	
	coschangePts9 = [x[0]/timeStep for x in cosdata9Reader]
	cosblockLengths9 = np.diff(coschangePts9)
	cosr9 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths9[::2]], [np.ones(x) for x in cosblockLengths9[1::2]])]
	cosfinalVector9 = np.hstack(tuple(cosr9))
	
	coschangePts10 = [x[0]/timeStep for x in cosdata10Reader]
	cosblockLengths10 = np.diff(coschangePts10)
	cosr10 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths10[::2]], [np.ones(x) for x in cosblockLengths10[1::2]])]
	cosfinalVector10 = np.hstack(tuple(cosr10))
	
	coschangePts11 = [x[0]/timeStep for x in cosdata11Reader]
	cosblockLengths11 = np.diff(coschangePts11)
	cosr11 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths11[::2]], [np.ones(x) for x in cosblockLengths11[1::2]])]
	cosfinalVector11 = np.hstack(tuple(cosr11))
	
	coschangePts12 = [x[0]/timeStep for x in cosdata12Reader]
	cosblockLengths12 = np.diff(coschangePts12)
	cosr12 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths12[::2]], [np.ones(x) for x in cosblockLengths12[1::2]])]
	cosfinalVector12 = np.hstack(tuple(cosr12))
	
	coschangePts13 = [x[0]/timeStep for x in cosdata13Reader]
	cosblockLengths13 = np.diff(coschangePts13)
	cosr13 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths13[::2]], [np.ones(x) for x in cosblockLengths13[1::2]])]
	cosfinalVector13 = np.hstack(tuple(cosr13))
	
	coschangePts14 = [x[0]/timeStep for x in cosdata14Reader]
	cosblockLengths14 = np.diff(coschangePts14)
	cosr14 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths14[::2]], [np.ones(x) for x in cosblockLengths14[1::2]])]
	cosfinalVector14 = np.hstack(tuple(cosr14))
	
	coschangePts15 = [x[0]/timeStep for x in cosdata15Reader]
	cosblockLengths15 = np.diff(coschangePts15)
	cosr15 = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in cosblockLengths15[::2]], [np.ones(x) for x in cosblockLengths15[1::2]])]
	cosfinalVector15 = np.hstack(tuple(cosr15))
	
	print 'cosbit files writen.'

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
   if args.numPoints is None:
      args.numPoints = raw_input('Enter number of numPoints: ')
   if (args.functionOption=='makeCosWave'):
   elif (args.functionOption=='getSinAndCos'):
   	print '\nProcessing sin and cos VCD files...\n'
   	getSinAndCos(args.cfreq, args.sfreq, args.numPoints)
   if (args.cfreq != '' and args.sfreq != ''):
   	print '\nUsing input signal with cosine frequency', args.cfreq, 'MHz and sampling frequency', args.sfreq/1e06, 'MHz\n'
if __name__ == "__main__":
   main(sys.argv[1:])
