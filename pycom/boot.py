import pycom
import time
from network import Bluetooth

# Wait 20 seconds for host system to boot up

print("ResponseBoot-v1")
print("Waiting for host system to start...")
pycom.heartbeat(False)

# Make sure bt is disable
bluetooth = Bluetooth()
bluetooth.deinit()

for de in range (1,10):
 pycom.rgbled(0x7f0000)
 time.sleep(1)
 pycom.rgbled(0x2f7f00)
 time.sleep(1)
 print(".")

pycom.rgbled(0x00ff00)
print("...done")
