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

# Setup

See lib/settings.py.example for example settings for PyCom module.

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
