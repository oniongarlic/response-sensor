all:

install-pkg:
	sudo apt get install hostapd

install:
	make -C hostapd
	make -C sensirion2mqtt
