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
available in device tree, because ```/proc/device-tree/system/linux,revision``` doesn't exist.
```
$ sudo ./blink
Raspberry Pi blink
Oops: Unable to determine Raspberry Pi board revision from /proc/device-tree/system/linux,revision and from /proc/cpuinfo
      WiringPi    : 3.16
      system name : Linux
      release     : 6.16.7-1-aarch64-ARCH
      version     : #1 SMP PREEMPT_DYNAMIC Mon Sep 15 09:42:38 MDT 2025
      machine     : aarch64
 -> No "Revision" line
 -> WiringPi is designed for Raspberry Pi and can only be used with a Raspberry Pi.

 -> Check at https://github.com/wiringpi/wiringpi/issues.
```
Here is a way to populate Model Revision
and Serial Number at boot time with some minor changes. There are probably many better ways of achieving the same result,
but this works for now.

The following commands assume that ```sudo```, ```uboot-tools``` and ```dtc``` have been installed.

Add overlay file to create /system/linux,revision and /system/linux,serial to device-tree.

```console
cd /boot
sudo mkdir overlays || true
cd overlays &&
sudo tee cm4-boardinfo.dtso >/dev/null <<xEOFx
/dts-v1/;
/plugin/;

/ {
    compatible = "overlay";

    fragment@0 {
        target-path = "/";
        __overlay__ {
            system {
                /* 64-bit serial as two 32-bit BE cells */
                linux,serial   = <0x00000000 0x00000000>;
                /* 32-bit board revision */
                linux,revision = <0x00000000>;
            };
        };
    };
};
xEOFx
```
Compile it
```console
sudo dtc -@ -I dts -o dtb -o cm4-boardinfo.dtbo cm4-boardinfo.dtso
```
USB port needs DT change to be enabled, so we'll add another overlay while we're here.

Some systems might use ```"/soc/usb@7e980000"``` instead of xhci, so it's here as a comment, just in case.
```console
cd /boot/overlays &&
sudo tee cm4-xhci.dtso >/dev/null <<xEOFx
/dts-v1/;
/plugin/;

/ {
    compatible = "overlay";

    fragment@0 {
        target-path = "/scb/xhci@7e9c0000";
        #target-path = "/soc/usb@7e980000";
        __overlay__ {
            status = "okay";
        };
    };
};
xEOFx
```
Compile it.
```console
sudo dtc -@ -I dts -o dtb -o cm4-xhci.dtbo cm4-xhci.dtso
```
Add following lines to /boot/config.txt to enable USB.
```console
cd /boot
sudo tee -a /boot/config.txt >/dev/null <<xEOFx

[cm4]
otg_mode=1

xEOFx
```

U-Boot has access to board info, so use it to populate the device-tree.

__Note__ _that u-boot variables have been escaped, i.e. ```${var}``` ===> ```\${var}``` to prevent their interpretation in this shell script.
Remove these if pasting into an editor._
```console
sudo mv /boot/boot.txt /boot/boot.txt.sv
sudo tee /boot/boot.txt >/dev/null <<xEOFx 
# After modifying, run ./mkscr

# Set root partition to the second partition of boot device
part uuid \${devtype} \${devnum}:2 uuid

setenv bootargs console=ttyS0,115200 console=tty0 root=PARTUUID=\${uuid} rw rootwait smsc95xx.macaddr="\${usbethaddr}"

# 1) Load kernel, DTB, initramfs
if load \${devtype} \${devnum}:\${bootpart} \${kernel_addr_r} /Image; then
  if load \${devtype} \${devnum}:\${bootpart} \${fdt_addr_r} /dtbs/\${fdtfile}; then
    if load \${devtype} \${devnum}:\${bootpart} \${ramdisk_addr_r} /initramfs-linux.img; then
      setenv have_initramfs yes
    fi
  fi
fi

# 2) Make the just-loaded DTB current and give it space
fdt addr \${fdt_addr_r}
fdt resize

# 3) === Apply cm4-xhci overlay to force USB host on ===
setenv overlay_addr_r 0x04F00000
load \${devtype} \${devnum}:\${bootpart} \${overlay_addr_r} \${prefix}overlays/cm4-xhci.dtbo
fdt apply \${overlay_addr_r}

# 4) === Apply cm4-boardinfo overlay + fill fields ===
# reuse overlay_addr_r buffer for boardinfo
load \${devtype} \${devnum}:\${bootpart} \${overlay_addr_r} \${prefix}overlays/cm4-boardinfo.dtbo
fdt apply \${overlay_addr_r}

# populate /system values
if test -n "\${serial#}"; then
  setexpr serial_lo sub '^........' '' \${serial#}
  setexpr serial_hi sub '........$' '' \${serial#}
  fdt set /system linux,serial <0x\${serial_hi} 0x\${serial_lo}>
fi

if test -n "\${boardrev}"; then
  fdt set /system linux,revision <\${boardrev}>
elif test -n "\${board_revision}"; then
  fdt set /system linux,revision <\${board_revision}>
fi

# optional debug
fdt print /scb/xhci@7e9c0000/status
fdt print /system

# 5) Boot Linux with the modified DT
if test -n "\${have_initramfs}"; then
  booti \${kernel_addr_r} \${ramdisk_addr_r}:\${filesize} \${fdt_addr_r}
else
  booti \${kernel_addr_r} - \${fdt_addr_r}
fi

xEOFx
```
Make the boot image
```console
cd /boot
sudo ./mkscr
```

After rebooting the board revision and serial number should be in device-tree.
_Note that ```lsusb``` requires ```usbutils``` package._
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
$ lsusb
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```
