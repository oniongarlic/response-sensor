# Response project air quality sensor

Air quality sensor using Sensirion module. This is a simplified and partialy rewriten version of the original implementation that wasn't properly finished.

* Sensirion sensor is connected with serial connection to a Raspberry Pi
* Sensor reading are sent to local MQTT server
* Raspberry Pi has WiFi AP
* PyCom module handles 5G connection
* PyCom module connects to Pi AP
* PyCom module listens to sensor reading with MQTT
* PyCom module sends sensor reading using MQTT and/or HTTP(s) post

This could be simplified further by:
* Using i2c to sensor, let kernel driver handle it

# HTTP logger

A very simple example http to postgresql logger php script is in http/

# MQTT

Monitor values with mosquitto_sub, for example

mosquitto_sub -h mqtthost -v -t sensor/# --cafile MQTT-CA.pem --cert mqtt-client.crt --key mqtt-client.key -i sensor-debug
