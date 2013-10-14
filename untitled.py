import numpy as np

def make_cos_wave(cosFreq, samplingFreq, numPoints):
	timeStep = 1.0/samplingFreq
	timePts = np.arange(0, numPoints*timeStep,timeStep) 
	cosData = np.cos(2*np.pi*cosFreq * timePts)

	#Write out hex file for VHDL
	intData = np.int16(cosData)
	with open('/home/nick/dualPortblockRAMdemod_top/cosData'+str(samples)+'.txt','w') as FID:
		FID.write(','.join(['x"{0:04X}"'.format(int(x)) for x in intData]) + ';')
	#Write out ASCII file for later plotting
	with open('/home/nick/dualPortblockRAMdemod_top/inputData'+str(samples)+'.txt','w') as FID:
		FID.write(','.join([str(x) for x in intData]) + ';')


# Exercise in python VCD file parsing with Blake and Colm
# 8/13/13
# Implemented in getSinAndCos() in diffBoardAndSim.py
timeStep = 5000
changePts = [x[0]/timeStep for x in sindata0Reader]
blockLengths = np.diff(changePts)

r = [np.hstack((a,b)) for a,b in zip([np.zeros(x) for x in blockLengths[::2]], [np.ones(x) for x in blockLengths[1::2]])]

finalVector = np.hstack(tuple(r))
	