#!/usr/bin/env python

'''
Check if required modules are installed for fan-control program to run.
'''

import ctypes
from ctypes import cdll
from ctypes.util import find_library
import os
import sys


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
