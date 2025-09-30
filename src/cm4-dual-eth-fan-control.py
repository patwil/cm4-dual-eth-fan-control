#!/usr/bin/env python

import_error = False
import_error_list = []

try:
	import time
except ImportError:
	import_error = True
	import_error_list.append('time')

try:
	import os
except ImportError:
	import_error = True
	import_error_list.append('os')

try:
	import sys
except ImportError:
	import_error = True
	import_error_list.append('sys')

try:
	import signal
except ImportError:
	import_error = True
	import_error_list.append('signal')

try:
	import logging
except ImportError:
	import_error = True
	import_error_list.append('logging')

if not import_error:
	sys.path.append('/usr/local/lib/python')

try:
	from wiringpi_wrapper import WiringPi
except ImportError:
	import_error = True
	import_error_list.append('wiringpi_wrapper')

if import_error:
	print('The following packages must be installed for this program to run:')
	for import_module in import_error_list:
		print(import_module)
	exit(1)

GPIO = None
pwm_pin = 19

# PWM clock source is usually 19.2MHz oscillator
BASE_CLOCK = 19_200_000
# 25KHz is a good frequency for fan motors,
# as anything above 20KHz avoids audible whine.
TARGET_FREQ = 25000
RANGE = 100

logger = None

def getTemp():
	f = open('/sys/class/thermal/thermal_zone0/temp')
	return int(f.read())/1000.0

def autoSpeed(duty_cycle, temp):
	global RANGE
	if temp < 45 and duty_cycle >= 10:
		return duty_cycle-10
	elif temp > 55 and duty_cycle <= (RANGE - 10):
		return duty_cycle+10
	else:
		return duty_cycle
	return duty_cycle

def handle_sigterm(signum, frame):
	GPIO.pinMode(pwm_pin, GPIO.INPUT)
	logger.info("Received signal (%s). Terminating." % signal.strsignal(signum))
	sys.exit(0)

def main():
	global logger
	global GPIO, pwm_pin
	global BASE_CLOCK, TARGET_FREQ, RANGE

	# Configure logging
	prog_name, prog_ext = os.path.splitext(os.path.basename(sys.argv[0]))

	logger = logging.getLogger(prog_name)
	logger.setLevel(logging.INFO)

	fh = logging.FileHandler('/var/log/'+prog_name+'.log')
	fh.setLevel(logging.INFO)

	formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	formatter = logging.Formatter(formatstr)

	fh.setFormatter(formatter)

	logger.addHandler(fh)

	# Redirect input/output to /dev/null
	sys.stdin = open(os.devnull, 'r')
	sys.stdout = open(os.devnull, 'w')
	sys.stderr = open(os.devnull, 'w')

	try:
		GPIO = WiringPi()
	except Exception as e:
		logger.exception("Cannot initialise WiringPi. Check that it is installed.")

	GPIO.wiringPiSetupPinType(GPIO.WPI_MODE_GPIO)
	GPIO.pinMode(pwm_pin, GPIO.PWM_OUTPUT)
	# Put PWM into mark–space mode (best for motors/fans)
	GPIO.pwmSetMode(GPIO.PWM_MODE_MS)

	GPIO.pwmSetRange(RANGE)
	divisor = int(round(BASE_CLOCK / (TARGET_FREQ * RANGE)))
	GPIO.pwmSetClock(divisor)

	# Register the signal handler
	signal.signal(signal.SIGINT, handle_sigterm)
	signal.signal(signal.SIGTERM, handle_sigterm)

	logger.info("Initialisation complete. Starting main loop.")
	try:
		duty_cycle = 0
		GPIO.pwm_write(pwm_pin, duty_cycle)
		while True:
			duty_cycle = int(autoSpeed(duty_cycle, getTemp()))
			GPIO.pwm_write(pwm_pin, duty_cycle)
			time.sleep(10)
	except Exception as e:
		logger.exception("Cannot initialise WiringPi.\nCheck that it is installed.")

	logger.info("Terminating.")
	GPIO.pinMode(pwm_pin, GPIO.INPUT)
	sys.exit(0)

# This is the standard boilerplate that calls the main function.
if __name__ == '__main__':
	main()
