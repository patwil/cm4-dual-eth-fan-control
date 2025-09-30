#!/usr/bin/env python

'''
Check if required modules are installed for fan-control program to run.
'''

try:
	import importlib
except ImportError:
	print('Error trying to import importlib.')
	exit(1)
	
try:
	import sys
except ImportError:
	print('Error trying to import sys.')
	exit(1)
	
required_modules = ['ctypes', 'time', 'os', 'signal', 'logging']

missing_modules = []

for module in required_modules:
	try:
		importlib.import_module(module)
	except ImportError:
		missing_modules.append(module)

if len(missing_modules):
	if len(missing_modules) == 1:
		sys.stderr.write(f'The following module is missing:\n\t{missing_modules[0]}\n')
	else:
		sys.stderr.write(f'The following modules are missing:\n')
		for missing_module in missing_modules:
			sys.stderr.write(f'\t{missing_module}\n')
	exit(1)

import ctypes
from ctypes import cdll
from ctypes.util import find_library
import os


WiringPi_libnames = ['wiringPi', 'wiringpi']
WiringPi_libfilenames = ['libwiringPi.so', 'libwiringPi.so.2']

has_wpi_lib_installed = False

for libname in WiringPi_libnames:
	found_lib = find_library(libname)
	if found_lib:
		try:
			wpi_lib = ctypes.CDLL(found_lib)
			has_wpi_lib_installed = True
		except OSError:
			pass
	if has_wpi_lib_installed:
		break

if not has_wpi_lib_installed:
	for libfilename in WiringPi_libfilenames:
		try:
			wpi_lib = ctypes.CDLL(libfilename)
			has_wpi_lib_installed = True
		except OSError:
			pass
		if has_wpi_lib_installed:
			break

if not has_wpi_lib_installed:
	sys.stderr.write('Could not find any of the following WiringPi libraries:\n')
	for lib in WiringPi_libnames:
		sys.stderr.write(f'\t{lib}\n')
	for lib in WiringPi_libfilenames:
		sys.stderr.write(f'\t{lib}\n')
	exit(2)
