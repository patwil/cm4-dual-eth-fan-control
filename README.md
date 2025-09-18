# Python wrapper for WiringPi on Arch Linux

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


# Device-Tree additions needed for WiringPi on CM4

WiringPi will not run on CM4 or CM5 as the Model and Revision info is not displayed in ```/proc/cpuinfo```; neither is this info
available in device tree, because ```/proc/device-tree/system/linux,revision``` doesn't exist. Here is a way to populate Model Revision
and Serial Number at boot time with some minor changes. There are probably many better ways of achieving the same result,
but this works for now.

The following commands assume that ```uboot-tools``` has been installed.

```console
sudo -i
DTFILE=bcm2711-rpi-cm4
cd /boot/dtbs/broadcom
cp ${DTFILE}.dtb ${DTFILE}.dtb.orig
dtc -I dtb -O dts ${DTFILE}.dtb -o ${DTFILE}.dts

### Populate device tree with serial# and revision#
# Add following lines after leds section:
        system {
                linux,serial = <0x00000000 0x00000000>;
                linux,revision = <0x000000>;
        };

###

# or use patch:

patch --ignore-whitespace ${DTFILE}.dts <<xEOFx
--- bcm2711-rpi-cm4.dts.orig     2025-08-22 13:11:40.000000000 -0400
+++ bcm2711-rpi-cm4.dts 2025-08-22 12:29:42.000000000 -0400
@@ -2387,44 +2387,49 @@
 
        leds {
                compatible = "gpio-leds";
                phandle = <0xf0>;

                led-act {
                        label = "ACT";
                        default-state = "off";
                        linux,default-trigger = "mmc0";
                        gpios = <0x07 0x2a 0x00>;
                        phandle = <0x58>;
                };

                led-pwr {
                        label = "PWR";
                        gpios = <0x0b 0x02 0x01>;
                        default-state = "off";
                        linux,default-trigger = "default-on";
                        phandle = <0x59>;
                };
        };

+       system {
+               linux,serial = <0x00000000 0x00000000>;
+               linux,revision = <0x000000>;
+       };
+
        sd_io_1v8_reg {
                compatible = "regulator-gpio";
                regulator-name = "vdd-sd-io";
xEOFx

# Save, then compile.

dtc -I dts -O dtb -o ${DTFILE}.dtb ${DTFILE}.dts

# Add following lines to /boot/boot.txt
      setexpr serial_lo sub '^........' '' ${serial#}
      setexpr serial_hi sub '........$' '' ${serial#}
      fdt addr ${fdt_addr_r}
      fdt set /system linux,serial <0x${serial_hi} 0x${serial_lo}>
      fdt set /system linux,revision <${board_revision}>

# or use patch:

patch --ignore-whitespace boot.txt <<xEOFx
--- boot.txt.orig       2025-08-22 16:14:22.000000000 -0400
+++ boot.txt    2025-08-22 16:14:04.000000000 -0400
@@ -8,6 +8,11 @@
 if load ${devtype} ${devnum}:${bootpart} ${kernel_addr_r} /Image; then
   if load ${devtype} ${devnum}:${bootpart} ${fdt_addr_r} /dtbs/${fdtfile}; then
     if load ${devtype} ${devnum}:${bootpart} ${ramdisk_addr_r} /initramfs-linux.img; then
+      setexpr serial_lo sub '^........' '' ${serial#}
+      setexpr serial_hi sub '........$' '' ${serial#}
+      fdt addr ${fdt_addr_r}
+      fdt set /system linux,serial <0x${serial_hi} 0x${serial_lo}>
+      fdt set /system linux,revision <${board_revision}>
       booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdt_addr_r};
     else
       booti ${kernel_addr_r} - ${fdt_addr_r};
xEOFx

# Make the boot image
./mkscr

```

After rebooting the board revision and serial number should be in device-tree.
```console
$ hexdump -C /proc/device-tree/system/linux,revision
00000000  00 d0 31 41                                       |..1A|
00000004
$ hexdump -C /proc/device-tree/system/linux,serial
00000000  10 00 00 00 bc 77 be ef                           |.....w..|
00000008
$ hexdump -C /sys/firmware/devicetree/base/system/linux,revision
00000000  00 d0 31 41                                       |..1A|
00000004
$ hexdump -C /sys/firmware/devicetree/base/system/linux,serial
00000000  10 00 00 00 bc 77 be ef                           |.....w..|
00000008
```
