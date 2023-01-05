import pycom
import time

# Wait 20 seconds for host system to boot up

pycom.heartbeat(False)

for de in range (1,10):
 pycom.rgbled(0x7f0000)
 time.sleep(1)
 pycom.rgbled(0x2f7f00)
 time.sleep(1)

pycom.rgbled(0x00ff00)
