#!/usr/bin/python

# Script to grab module information from 
# top_level design, select signals,
# insert signals into test_bench


# command line Arguments:
# ----------------------------------------------------------------------------------------- #
# 																							#
# -p project_dir	= path to top level module 								 				#
# -t top_level_file = file name of top level module											#
# -m module 		= vhdl module to select 												#
# -s signals 		= list of signals from module											#
# -b testbench 		= testbench file name													#
# 																							#
# ----------------------------------------------------------------------------------------- #


# --------------------------------Example Commandline--------------------------------------------------- #
#																								 		 #
#	./testbenchGen -p ~/project_dir -t my_top.vhd -m my_module.vhd -s [sig1,sig2,sigN]	 				 # 
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

# ------------------------------------------------- #
# 			Select Module to Evaluate				#
# ------------------------------------------------- #

def select_modules(project_dir,top_level_file,module_select):
	project_dir=regex.sub('\/$','',project_dir)
	with open(str(project_dir)+'/'+str(top_level_file),'r') as fid:
		top_level = fid.read()
	
	top_module = regex.sub('\.vhd','',top_level_file)
	match_ent = regex.compile('entity work.*')
	module_files = [regex.sub('^entity work\..*?','',top) for top in match_ent.findall(top_level)]
	module_files = [regex.sub('\s','',m) for m in module_files]
	module_files = [m+'.vhd' for m in module_files]

	print 'Opening {} from top level code...'.format(module_select)

	mod_indx = module_files.index(str(module_select)+'.vhd')
	with open(str(project_dir)+'/'+str(module_files[mod_indx]),'r') as fid:
		file_selected = fid.read()  

	# ------------------------------------------------- #
	# 			Extract Input signals 					#
	# ------------------------------------------------- #
	match_ins = regex.compile('.*\: in\s.*')
	
	inputs = match_ins.findall(file_selected)
	
	inputs = [regex.sub('\-\-.*','',inn) for inn in inputs]
	inputs = [regex.sub('\t','',inn) for inn in inputs]

	in_types = [regex.sub('.*\: in','',inn) for inn in inputs]
	in_types = [regex.sub('\;','',it) for it in in_types]

	inputs = [regex.sub('\:.*','',inn) for inn in inputs]	
	inputs = [regex.sub('\s','',inn) for inn in inputs]

	inputs_zip = [(i,j) for i,j in zip(inputs,in_types)]

	# ------------------------------------------------- #
	# 			Extract Output signals 					#
	# ------------------------------------------------- #

	match_outs = regex.compile('.*\: out\s.*')
	outputs = match_outs.findall(file_selected)
	outputs = [regex.sub('\-\-.*','',out) for out in outputs]
	outputs = [regex.sub('\t','',out) for out in outputs]

	out_types = [regex.sub('.*\: out?','',out) for out in outputs]
	out_types = [regex.sub('\;','',it) for it in out_types]

	outputs = [regex.sub('\:.*','',out) for out in outputs]	
	outputs = [regex.sub('\s','',out) for out in outputs]

	outputs_zip = [(i,j) for i,j in zip(outputs,out_types)]

	print 'Input Signals:\n-----------------------------\n{}'.format(inputs_zip)
	print '\n-----------------------------\n'
	print 'Output Signals:\n-----------------------------\n{}'.format(outputs_zip)

	types = np.hstack([in_types,out_types])
	signals = np.hstack([inputs,outputs])

	return inputs_zip,outputs_zip


# ------------------------------------------------- #
# 			Select Signals to output				#
# ------------------------------------------------- #

def select_signals(inputs,outputs,signal_select,project_dir,testbench):
	with open(str(testbench),'r') as fid:
		testbench_file = fid.read()

	match_clk_proc = regex.compile('clk\_process.*')
	clk_proc = match_clk_proc.findall(testbench_file)

	print clk_proc

	signals = [out[0] for out in outputs]
	types = [out[1] for out in outputs]
	sig_indx = signals.index(signal_select)
	selected_sig = signals[sig_indx]

	match_inwidths = regex.compile('([0-9]+.*)')
	match_outwidths = regex.compile('([0-9]+.*)')

	in_widths = [str(match_inwidths.findall(inputs[i][1])) for i in range(len(inputs))]

	in_widths = [regex.sub('downto.*','',inn) for inn in in_widths]
	in_widths = [regex.sub('\s$','',inn) for inn in in_widths]
	in_widths = [regex.sub('\'','',inn) for inn in in_widths]
	in_widths = [regex.sub('\[','',inn) for inn in in_widths]
	in_widths = [regex.sub('\]','',inn) for inn in in_widths]
	in_widths = [int(inn) if inn !='' else int(1) for inn in in_widths]

	out_widths = [str(match_outwidths.findall(outputs[i][1])) for i in range(len(outputs))]

	out_widths = [regex.sub('downto.*','',out) for out in out_widths]
	out_widths = [regex.sub('\s$','',out) for out in out_widths]
	out_widths = [regex.sub('\'','',out) for out in out_widths]
	out_widths = [regex.sub('\[','',out) for out in out_widths]
	out_widths = [regex.sub('\]','',out) for out in out_widths]
	out_widths = [int(outs) if outs !='' else int(1) for outs in out_widths]

	print 'Selected signal: {}'.format(selected_sig)


	# file writer code:

	print 'Writing file writer code to testbench file: {}'.format(testbench)

	print """\n-- -----------------------------------------------------------------------------------	
-- \tFile Writer Block										
-- -----------------------------------------------------------------------------------\n"""

	for i in range(len(signals)):
		print """output_file_"""+str(signals[i])+""" : entity work.file_writer 							  	
   generic map(																			  	
     dataWidth => """+str(out_widths[i])+""",													  	
     wordWidth => 1,																																				
     fileName => \""""+project_dir+"""/data"""+str(signals[i])+"""output.dat"			
   )																							
   port map( 																					
     reset => rst,																			
     clk => clk,																				
     enable => rst,																			
     data => """+str(signals[i])+""",														
     data_valid => rst																		
   );\n"""

	print """\n-- ----------------------------------------------------------------------------------- 	
-- \tEnd of File Writer Block										
-- -----------------------------------------------------------------------------------\n"""

	with open(str(testbench),'w') as fid:
		fid.write("""\n-- -----------------------------------------------------------------------------------	
-- \tFile Writer Block										
-- -----------------------------------------------------------------------------------\n""")
		for i in range(len(signals)):
			fid.write("""output_file_"""+str(signals[i])+""" : entity work.file_writer 							  	
	   generic map(																			  	
	     dataWidth => """+str(out_widths[i])+""",													  	
	     wordWidth => 1,																																				
	     fileName => \""""+project_dir+"""/data"""+str(signals[i])+"""output.dat"			
	   )																							
	   port map( 																					
	     reset => rst,																			
	     clk => clk,																				
	     enable => rst,																			
	     data => """+str(signals[i])+""",														
	     data_valid => rst																		
	   );\n""")
   		fid.write("""\n-- ----------------------------------------------------------------------------------- 	
-- \tEnd of File Writer Block										
-- -----------------------------------------------------------------------------------\n""")		




def main(argv):
   parser=argparse.ArgumentParser(description='Manage VHDL Verification and Plotting')
   # commandline args, for usage type '-h'
   parser.add_argument('-m','--module_select',dest='module_select',type=str,help='module to select for simulation')
   parser.add_argument('-p','--project_dir',dest='project_dir',type=str,help='project file path')
   parser.add_argument('-t','--top_level_file',dest='top_level_file',type=str,help='top level file name')
   parser.add_argument('-s','--signals',dest='signals',type=str,help='selected signals')
   parser.add_argument('-b','--testbench',dest='testbench',type=str,help='testbench file name')

   args = parser.parse_args()

   ins,outs = select_modules(args.project_dir,args.top_level_file,args.module_select)
   select_signals(ins,outs,args.signals,args.project_dir,args.testbench)

if __name__ == "__main__":
   main(sys.argv[1:])

