all:

install-pkg:
	sudo apt get install hostapd mosquitto mosquitto-clients picocom git python3-paho-mqtt python3-serial

install:
	make -C hostapd
	make -C sensirion2mqtt
