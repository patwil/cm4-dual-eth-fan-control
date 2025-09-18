**A Python script to control fan on Waveshare CM4-DUAL-ETH-MINI which running aarch64 Arch Linux**

RPi GPIO Python library is not suppoorted on aarch64 Arch Linux.
This means that the [fan control script for Waveshare CM4-DUAL-ETH-MINI](https://files.waveshare.com/upload/e/ee/CM4-DUAL-ETH-MINI-Example.zip)
does not work if the Compute Module 4 (CM4) is running 64-bit Arch Linux.

[WiringPi](https://github.com/WiringPi/WiringPi.git) is perhaps the most comprehensive and fastest set of C libraries for controlling RPi GPIO.
Unfortunately there is no up-to-date Python version at present.

A solution was found using OpenAI's ChatGPT using the following prompt:
```
Translate the following c include file into a python wrapper.
The generated code should be in a class named WiringPi.
https://github.com/WiringPi/WiringPi/blob/master/wiringPi/wiringPi.h
Ensure that the ISR callbacks are stored in class scope rather than local
to the functions which register the ISRs.
```
Save the generated Python code to a file named, say, ```wiringpi_wrapper.py``` in the same directory as ```main.py```.

Control of the GPIO pins needs root privileges, so the script needs to be run as superuser.

```sudo python ./main.py```

Use Control-C to exit the program.

WiringPi can output _copious_ debug info by setting WIRINGPI_DEBUG environment variable.

```sudo WIRINGPI_DEBUG=1 python ./main.py```
