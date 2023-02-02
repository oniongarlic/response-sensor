all:

install-pkg:
	sudo apt install hostapd mosquitto mosquitto-clients picocom git python3-paho-mqtt python3-serial

install:
	make -C hostapd
	make -C udev
	make -C sensirion2mqtt
