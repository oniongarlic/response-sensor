all:

install:
	install -d -o root -m 755 /etc/hostapd/
	install -o root -m 644 hostapd.conf.example /etc/hostapd/hostapd.conf

	systemctl stop wpa_supplicant
	systemctl disable wpa_supplicant

	rfkill unblock wlan

	systemctl unmask hostapd
	systemctl enable hostapd
	systemctl start hostapd
