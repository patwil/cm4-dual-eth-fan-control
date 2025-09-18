# wiringpi_wrapper.py
"""
ctypes wrapper generated from wiringPi/wiringPi.h (user-provided header).
All bindings are placed inside the WiringPi class.

Important:
 - ISR callback objects are stored on the WiringPi instance (self._isr_callbacks
   and self._isr2_callbacks) to prevent them from being garbage-collected.
 - Not every single symbol from the header is bound; the wrapper exposes the
   most commonly used functions, structs and constants. Extend as needed.
"""

import ctypes
import ctypes.util
import sys
from ctypes import (
    c_int, c_uint, c_longlong, c_ulong, c_void_p, c_char_p, c_ubyte, c_ulonglong
)


class WiringPi:
    # -----------------------
    # Common constants (selected from wiringPi.h)
    # -----------------------
    TRUE = True
    FALSE = False

    # wiringPi modes
    WPI_MODE_PINS = 0
    WPI_MODE_GPIO = 1
    WPI_MODE_GPIO_SYS = 2
    WPI_MODE_PHYS = 3
    WPI_MODE_PIFACE = 4
    WPI_MODE_GPIO_DEVICE_BCM = 5
    WPI_MODE_GPIO_DEVICE_WPI = 6
    WPI_MODE_GPIO_DEVICE_PHYS = 7
    WPI_MODE_UNINITIALISED = -1

    # Pin modes
    INPUT = 0
    OUTPUT = 1
    PWM_OUTPUT = 2
    GPIO_CLOCK = 3
    SOFT_PWM_OUTPUT = 4
    SOFT_TONE_OUTPUT = 5
    PWM_TONE_OUTPUT = 6
    PM_OFF = 7
    PWM_MS_OUTPUT = 8
    PWM_BAL_OUTPUT = 9

    # Digital values
    LOW = 0
    HIGH = 1

    # Pull up/down
    PUD_OFF = 0
    PUD_DOWN = 1
    PUD_UP = 2

    # PWM modes
    PWM_MODE_MS = 0
    PWM_MODE_BAL = 1

    # Interrupt levels
    INT_EDGE_SETUP = 0
    INT_EDGE_FALLING = 1
    INT_EDGE_RISING = 2
    INT_EDGE_BOTH = 3

    # -----------------------
    # Structs & callback types
    # -----------------------
    class WPIWfiStatus(ctypes.Structure):
        _fields_ = [
            ("statusOK", c_int),          # -1 error, 0 timeout, 1 irq processed
            ("pinBCM", c_uint),           # BCM pin number
            ("edge", c_int),              # INT_EDGE_*
            ("timeStamp_us", c_longlong), # timestamp in microseconds
        ]

    # ISR callback types
    # old-style: void handler(void)
    ISR_CALLBACK = ctypes.CFUNCTYPE(None)
    # new-style: void handler(struct WPIWfiStatus, void* userdata)
    ISR2_CALLBACK = ctypes.CFUNCTYPE(None, WPIWfiStatus, c_void_p)

    # -----------------------
    # Exception
    # -----------------------
    class WiringPiError(RuntimeError):
        pass

    # -----------------------
    # Initialization: load lib + bind
    # -----------------------
    def __init__(self, libname: str = None):
        """
        Instantiate and load libwiringPi. If libname provided, it's attempted first.
        """
        self._wpi = None
        self._libname_used = None
        self._load_library(libname)

        # keep references to ISR callbacks so Python doesn't GC them
        # keyed by pin or by generated id for ISR2
        self._isr_callbacks = {}   # pin -> CFUNCTYPE handler
        self._isr2_callbacks = {}  # pin -> CFUNCTYPE handler

        # bind common functions
        self._bind_core_functions()

    def _load_library(self, libname: str = None):
        tried = []
        if libname:
            tried.append(libname)
            try:
                self._wpi = ctypes.CDLL(libname)
                self._libname_used = libname
                return
            except OSError:
                self._wpi = None

        for candidate in ('wiringPi', 'wiringpi'):
            found = ctypes.util.find_library(candidate)
            if found:
                tried.append(found)
                try:
                    self._wpi = ctypes.CDLL(found)
                    self._libname_used = found
                    return
                except OSError:
                    self._wpi = None

        for filename in ('libwiringPi.so', 'libwiringPi.so.2'):
            tried.append(filename)
            try:
                self._wpi = ctypes.CDLL(filename)
                self._libname_used = filename
                return
            except OSError:
                self._wpi = None

        raise self.WiringPiError(f"Could not load wiringPi library. Tried: {tried}")

    def _bind(self, name, restype, argtypes):
        """
        Attempt to bind a function from the loaded library. Returns None if not present.
        """
        try:
            func = getattr(self._wpi, name)
        except AttributeError:
            return None
        func.restype = restype
        func.argtypes = argtypes
        return func

    def _ensure(self, func, name):
        if func is None:
            raise self.WiringPiError(f"Function '{name}' not found in wiringPi library.")
        return func

    # -----------------------
    # Core bindings
    # -----------------------
    def _bind_core_functions(self):
        # Setup
        self.wiringPiVersion = self._bind("wiringPiVersion", c_int, [])
        self.wiringPiSetup = self._bind("wiringPiSetup", c_int, [])
        self.wiringPiSetupSys = self._bind("wiringPiSetupSys", c_int, [])
        self.wiringPiSetupGpio = self._bind("wiringPiSetupGpio", c_int, [])
        self.wiringPiSetupPhys = self._bind("wiringPiSetupPhys", c_int, [])
        self.wiringPiSetupPinType = self._bind("wiringPiSetupPinType", c_int, [c_int])
        self.wiringPiSetupGpioDevice = self._bind("wiringPiSetupGpioDevice", c_int, [c_int])

        # Pin control
        self.pinModeAlt = self._bind("pinModeAlt", None, [c_int, c_int])
        self.getPinModeAlt = self._bind("getPinModeAlt", c_int, [c_int])
        self.pinMode = self._bind("pinMode", None, [c_int, c_int])
        self.pullUpDnControl = self._bind("pullUpDnControl", None, [c_int, c_int])
        self.digitalRead = self._bind("digitalRead", c_int, [c_int])
        self.digitalWrite = self._bind("digitalWrite", None, [c_int, c_int])
        self.pwmWrite = self._bind("pwmWrite", None, [c_int, c_int])
        self.analogRead = self._bind("analogRead", c_int, [c_int])
        self.analogWrite = self._bind("analogWrite", None, [c_int, c_int])

        # Board specifics
        self.piGpioLayout = self._bind("piGpioLayout", c_int, [])
        self.piBoardRev = self._bind("piBoardRev", c_int, [])
        self.piBoardId = self._bind("piBoardId", None, [ctypes.POINTER(c_int), ctypes.POINTER(c_int), ctypes.POINTER(c_int), ctypes.POINTER(c_int), ctypes.POINTER(c_int)])
        self.piBoard40Pin = self._bind("piBoard40Pin", c_int, [])
        self.piRP1Model = self._bind("piRP1Model", c_int, [])
        self.wpiPinToGpio = self._bind("wpiPinToGpio", c_int, [c_int])
        self.physPinToGpio = self._bind("physPinToGpio", c_int, [c_int])
        self.getAlt = self._bind("getAlt", c_int, [c_int])

        # Pad/drive
        self.setPadDrive = self._bind("setPadDrive", None, [c_int, c_int])
        self.setPadDrivePin = self._bind("setPadDrivePin", None, [c_int, c_int])

        # PWM/Clock
        self.pwmToneWrite = self._bind("pwmToneWrite", None, [c_int, c_int])
        self.pwmSetMode = self._bind("pwmSetMode", None, [c_int])
        self.pwmSetRange = self._bind("pwmSetRange", None, [c_uint])
        self.pwmSetClock = self._bind("pwmSetClock", None, [c_int])
        self.gpioClockSet = self._bind("gpioClockSet", None, [c_int, c_int])

        # Byte read/write
        self.digitalReadByte = self._bind("digitalReadByte", c_uint, [])
        self.digitalReadByte2 = self._bind("digitalReadByte2", c_uint, [])
        self.digitalWriteByte = self._bind("digitalWriteByte", None, [c_int])
        self.digitalWriteByte2 = self._bind("digitalWriteByte2", None, [c_int])

        # Interrupts / wait
        self.wiringPiISR = self._bind("wiringPiISR", c_int, [c_int, c_int, self.ISR_CALLBACK])
        self.wiringPiISR2 = self._bind("wiringPiISR2", c_int, [c_int, c_int, self.ISR2_CALLBACK, c_ulong, c_void_p])
        # waitForInterrupt2 may return struct by value on some ABIs; attempt bind
        self.waitForInterrupt2 = self._bind("waitForInterrupt2", self.WPIWfiStatus, [c_int, c_int, c_int, c_ulong])
        self.wiringPiISRStop = self._bind("wiringPiISRStop", c_int, [c_int])
        self.waitForInterruptClose = self._bind("waitForInterruptClose", c_int, [c_int])

        # Threads & scheduling
        self.piThreadCreate = self._bind("piThreadCreate", c_int, [ctypes.CFUNCTYPE(c_void_p, c_void_p)])
        self.piLock = self._bind("piLock", None, [c_int])
        self.piUnlock = self._bind("piUnlock", None, [c_int])
        self.piHiPri = self._bind("piHiPri", c_int, [c_int])

        # Timing
        self.delay = self._bind("delay", None, [c_uint])
        self.delayMicroseconds = self._bind("delayMicroseconds", None, [c_uint])
        self.millis = self._bind("millis", c_uint, [])
        self.micros = self._bind("micros", c_uint, [])
        self.piMicros64 = self._bind("piMicros64", c_ulonglong, [])

    # -----------------------
    # High-level helpers
    # -----------------------
    def libname(self):
        return self._libname_used

    def setup(self):
        f = self._ensure(self.wiringPiSetup, "wiringPiSetup")
        return f()

    def setup_gpio(self):
        f = self._ensure(self.wiringPiSetupGpio, "wiringPiSetupGpio")
        return f()

    def set_pin_mode(self, pin, mode):
        f = self._ensure(self.pinMode, "pinMode")
        f(pin, mode)

    def set_pullupdn(self, pin, pud):
        f = self._ensure(self.pullUpDnControl, "pullUpDnControl")
        f(pin, pud)

    def digital_write(self, pin, value):
        f = self._ensure(self.digitalWrite, "digitalWrite")
        f(pin, value)

    def digital_read(self, pin):
        f = self._ensure(self.digitalRead, "digitalRead")
        return f(pin)

    def pwm_write(self, pin, value):
        f = self._ensure(self.pwmWrite, "pwmWrite")
        f(pin, value)

    def sleep_ms(self, ms):
        f = self._ensure(self.delay, "delay")
        f(ms)

    def sleep_us(self, us):
        f = self._ensure(self.delayMicroseconds, "delayMicroseconds")
        f(us)

    # -----------------------
    # ISR registration: store callback references in instance scope
    # -----------------------
    def register_isr(self, pin: int, edge: int, handler):
        """
        Register an old-style ISR (no-arg function). Keeps reference to callback
        in self._isr_callbacks[pin] to prevent GC.
        Returns the result of wiringPiISR (0 on success).
        """
        if not callable(handler):
            raise TypeError("handler must be callable (no args).")
        f = self._ensure(self.wiringPiISR, "wiringPiISR")
        cb = self.ISR_CALLBACK(handler)
        # store reference
        self._isr_callbacks[pin] = cb
        return f(pin, edge, cb)

    def unregister_isr(self, pin: int):
        """
        Stop keeping a reference to an old-style ISR. Note: there is no
        direct wiringPi API to unregister the callback (wiringPiISRStop exists
        but may require the pin). We attempt wiringPiISRStop if available.
        """
        # attempt to stop via wiringPiISRStop if present
        if self.wiringPiISRStop:
            try:
                self.wiringPiISRStop(pin)
            except Exception:
                pass
        # remove stored ref
        self._isr_callbacks.pop(pin, None)

    def register_isr2(self, pin: int, edge: int, handler, userdata=0):
        """
        Register a new-style ISR that expects (WPIWfiStatus, userdata).
        We store the CFUNCTYPE wrapper in self._isr2_callbacks[pin].
        `userdata` is passed to wiringPiISR2 as an unsigned long.
        """
        if not callable(handler):
            raise TypeError("handler must be callable (wfiStatus, userdata).")
        f = self._ensure(self.wiringPiISR2, "wiringPiISR2")
        cb = self.ISR2_CALLBACK(handler)
        self._isr2_callbacks[pin] = cb
        return f(pin, edge, cb, c_ulong(userdata), None)

    def unregister_isr2(self, pin: int):
        if self.wiringPiISRStop:
            try:
                self.wiringPiISRStop(pin)
            except Exception:
                pass
        self._isr2_callbacks.pop(pin, None)

    # -----------------------
    # Utility / introspection
    # -----------------------
    def has_function(self, name: str) -> bool:
        return getattr(self, name, None) is not None

    # -----------------------
    # Optional: a small smoke test for manual invocation (no pin toggles)
    # -----------------------
    def _smoke_test(self):
        print("wiringPi lib:", self.libname())
        print("Has wiringPiSetup:", self.has_function("wiringPiSetup"))
        print("Has pinMode:", self.has_function("pinMode"))
        print("Has digitalWrite:", self.has_function("digitalWrite"))

# If executed as a script perform a safe smoke test
if __name__ == "__main__":
    try:
        w = WiringPi()
    except WiringPi.WiringPiError as e:
        print("Could not load WiringPi:", e)
        sys.exit(1)

    w._smoke_test()

