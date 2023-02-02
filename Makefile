all:
	make -C hostapd
	make -C udev
	make -C sensirion

install-pkg:
	sudo apt install hostapd mosquitto mosquitto-clients picocom git python3-paho-mqtt python3-serial

install: all
	make -C hostapd install
	make -C udev install
	make -C sensirion install

	systemctl disable triggerhappy
	systemctl disable avahi-daemon
	systemctl disable ModemManager
