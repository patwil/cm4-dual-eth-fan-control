from wiringpi_wrapper import WiringPi
import time, os, sys, psutil, signal
import argparse, textwrap

GPIO = None
pwmPin = 19
fgPin = 17

# PWM clock source is usually 19.2MHz oscillator
BASE_CLOCK = 19_200_000
# 25KHz is a good frequency for fan motors,
# as anything above 20KHz avoids audible whine.
TARGET_FREQ = 25000
RANGE = 100

dc = 50
onGetSpeed = False

t1 = 0
t = 1

is_running_as_daemon = True

def is_terminal():
    return sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()

def running_as_daemon():
	# 1) Not attached to terminal
	if not is_terminal():
		# 2) Parent is init/systemd or PID 1
		parent = psutil.Process(os.getppid())
		if parent.pid == 1 or parent.name() in ("systemd", "init"):
			return True
	return False

def speedcallback():
	global t1, t
	if t1 != 0:
		t = time.time() - t1
		t1 = 0
	else:
		t1 = time.time()

def startGetSpeed(irqPin):
	cb_ref = GPIO.register_isr(irqPin, GPIO.INT_EDGE_FALLING, speedcallback)
	onGetSpeed = True

def stopGetSpeed(irqPin):
	GPIO.unregister_isr(irqPin)
	onGetSpeed = False

def getTemp():
	f = open('/sys/class/thermal/thermal_zone0/temp')
	return int(f.read())/1000.0

def autoSpeed(dc, temp):
	if temp < 45 and dc >= 10:
		return dc-10
	elif temp > 55 and dc <= (RANGE - 10):
		return dc+10
	else:
		return dc
	return dc

def handle_sigterm(signum, frame):
	GPIO.pinMode(pwmPin, GPIO.INPUT)
	if not is_running_as_daemon:
		print("Received SIGTERM, cleaning up...")
		stopGetSpeed(fgPin)
	sys.exit(0)

if __name__== '__main__':
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent('''\
		Sets fan speed depending on CPU temperature.
		 '''))
	parser.add_argument('-d', "--daemon", help='running as daemon, i.e. no output to terminal', action='store_true', required=False)
	args = parser.parse_args()
	is_running_as_daemon = args.daemon or running_as_daemon()
	GPIO = WiringPi()
	GPIO.wiringPiSetupPinType(GPIO.WPI_MODE_GPIO)
	GPIO.pinMode(pwmPin, GPIO.PWM_OUTPUT)
	GPIO.pinMode(fgPin, GPIO.INPUT)
	# Put PWM into mark–space mode (best for motors/fans)
	GPIO.pwmSetMode(GPIO.PWM_MODE_MS)

	GPIO.pwmSetRange(RANGE)
	divisor = int(round(BASE_CLOCK / (TARGET_FREQ * RANGE)))
	GPIO.pwmSetClock(divisor)

	# Register the signal handler
	signal.signal(signal.SIGTERM, handle_sigterm)

	try:
		GPIO.pwm_write(pwmPin, dc)
		if not is_running_as_daemon:
			startGetSpeed(fgPin)
		num = 0
		while True:
			temp = getTemp()
			if is_running_as_daemon:
				dc = int(autoSpeed(dc, temp))
				GPIO.pwm_write(pwmPin, dc)
				time.sleep(10)
			else:
				speed = 60/(t*2)
				print("The speed is %f" %speed)
				print("The temp is %f" %temp)
				print("dc=%3d" %dc)
				print("\33[4A")
				if num > 5:
					num = 0
					dc = int(autoSpeed(dc, temp))
					GPIO.pwm_write(pwmPin, dc)
				num = num+1
				time.sleep(1)
	except KeyboardInterrupt as e:
		pass

	GPIO.pinMode(pwmPin, GPIO.INPUT)
	if not is_running_as_daemon:
		stopGetSpeed(fgPin)
	sys.exit(0)
