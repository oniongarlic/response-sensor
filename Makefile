all:

install-pkg:
	sudo apt get install hostapd python3-pip

install:
	make -C hostapd
	make -C sensirion2mqtt
