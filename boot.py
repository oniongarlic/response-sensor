import pycom
import time

# Wait 12 seconds for host system to boot up

pycom.heartbeat(False)

for de in range (1,10):
 pycom.rgbled(0x7f0000)
 time.sleep(1)
 pycom.rgbled(0x2f7f000)
 time.sleep(0.2)

pycom.rgbled(0x00ff00)
