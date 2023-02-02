# Response project air quality sensor

Air quality sensor using Sensirion module.
This is a simplified and partialy rewriten version of the original implementation.

Project details at https://h2020response.eu/

## Hardware & software setup summary

* Sensirion sensor is connected with serial connection to a Raspberry Pi
* Sensor reading are sent to local MQTT server
* Raspberry Pi has WiFi AP
* PyCom module handles data transfer with 5G connection
* PyCom module connects to Pi AP, listens to sensor reading with MQTT
* PyCom module sends sensor reading using MQTT and/or HTTP(s) post

This could be simplified further by:
* Using i2c connection to sensor, let kernel driver handle it

# Prepare the Pi side

Use lite image version, no GUI stuff is needed.

Install required (and helpfull) packages with

 apt install hostapd mosquitto mosquitto-clients picocom git python3-paho-mqtt python3-serial

Enable uart in /boot/config.txt

 enable_uart=1

Disable serial getty
 systemctl disable serial-getty@ttyS0.service

Disable serial console

Remove console=serial0,115200 from /boot/cmdline.txt

Fix permissions, add a file ttyS0.rules with 

 KERNEL=="ttyS0", GROUP="dialout", MODE="0660"

in /etc/udev/rules.d/ttyS0.rules

# Setup PyCom module

See lib/settings.py.example for example settings for PyCom module.

Passwords and related things are dummies in here, for a real setup you need to adjust the sample configurations.

# Setup Pi side 

TL;DR
sudo make install

## Hostapd

There is a example config in hostapd/

Add 

 interface wlan0
    static ip_address=192.168.123.254/24
    nohook wpa_supplicant

to /etc/dhcpcd.conf

## Sensirion to MQTT

See sensirion/ for scripts and init scripts

To check that sensor readings work, try

 mosquitto_sub -t sensor/airquality

# PyCom board

Transfer the contents of pycom/ to the module. How you do that is up to you.

Initial setup can be made by setting up wifi over USB serial port,
and transfering the files with ftp to the module IP.

See setup/pycom-wifi.py for an simple example on how to do that.

# Data destinations

The PyCom script can send send data to a http endpoint and/or MQTT.

## HTTP logger

A very simple example http to postgresql logger php script is in http

## MQTT

Data is sent using secure connection to a MQTT server. It can then be re-distributed or handled in some other manner.

Certificates need to be uploaded to the PyCom board in /flash/cert/

* "ca_certs":"/flash/cert/ca.pem"
* "keyfile":"/flash/cert/pycom.key"
* "certfile":"/flash/cert/pycom.crt"

You can easily monitor realtime values with mosquitto_sub, for example

mosquitto_sub -h mqtthost -v -t sensor/# --cafile MQTT-CA.pem --cert mqtt-client.crt --key mqtt-client.key -i sensor-debug
