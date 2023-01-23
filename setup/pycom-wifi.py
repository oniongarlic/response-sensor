from network import WLAN
import time

w = WLAN(mode=WLAN.STA)
w.ifconfig(config=('192.168.123.1', '255.255.255.0', '192.168.123.254', '192.168.123.254'))
w.hostname('pycom')
w.scan()
w.connect(ssid='ResponseSensor', auth=(WLAN.WPA2, 'Sensirion22'), timeout=5000)
time.sleep(2)
w.isconnected()
