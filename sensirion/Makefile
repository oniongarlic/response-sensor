all:

install:
#	pip3 install -r requirements.txt
	install -d -m 755 -o pi /opt/sensirion2mqtt/bin
	install -o pi -m 755 sensirion2mqtt.py /opt/sensirion2mqtt/bin/
	install -o root sensirion2mqtt.service /etc/systemd/system/

	systemctl enable sensirion2mqtt
	systemctl start sensirion2mqtt
