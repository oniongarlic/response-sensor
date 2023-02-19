import machine
import pycom
import ubinascii
import ussl
import time
import socket
import sys
import urequests as req

from network import WLAN
from network import LTE
from mqtt import MQTTClient
from machine import RTC
from machine import WDT

import settings as cfg

def get_temp():
    return ((machine.temperature() - 32) / 1.8)

# Sensor ID
sid=ubinascii.hexlify(machine.unique_id()).decode()

# Signal that we are now in main, blue led
pycom.rgbled(0x00007f)

rtc=RTC()
lte=LTE()
wlan=WLAN(mode=WLAN.STA)
scid="pycom-"+sid
sc=MQTTClient(scid, "192.168.123.254", port=1883)
rsc=False

ssl_params = {
 "server_hostname": cfg.SMQTT_BROKER_IP,
 "cert_reqs":ussl.CERT_REQUIRED,
 "ca_certs":"/flash/cert/ca.pem",
 "keyfile":"/flash/cert/pycom.key",
 "certfile":"/flash/cert/pycom.crt"}

sdata=''
mqc=1
pct=get_temp()

#uart = machine.UART(1, baudrate=115200)
#uart.init(115200, bits=8, stop=1, pins=("P3", "P4"),  rx_buffer_size=4096)

# Local MQTT sensor topic cb
def sub_sc_cb(topic, msg):
    pycom.rgbled(0x7f7f00)
    # print(topic+" is "+msg)
    print("s")
    wdt.feed()
    sdata=msg
    if rsc:
       mqtt_publish(msg)
    http_post(msg)
    pycom.rgbled(0x007f00)

# Remote MQTT topic cb, for now does nothing
def sub_rsc_cb(topic, msg):
    print("Remote sent:"+topic+" is "+msg)

# Connect to remote MQTT server and publish details
def mqtt_connect():
    try:
        rsc.connect()
        rsc.publish("sensor/"+sid+"/online", str(mqc))
        rsc.publish("sensor/"+sid+"/reset", str(machine.reset_cause()))
        mqc+=1
        return True
    except OSError as e:
        sys.print_exception(e)
    return False

# Publish data
# if connection has failed, try to reconnect
def mqtt_publish(sdata):
    try:
        rsc.publish("sensor/"+sid+"/airquality", sdata)
        return True
    except OSError as e:
        if e.errno == errno.ECONNRESET:
            mqtt_connect()
            rsc.publish("sensor/"+sid+"/airquality", sdata)
            return True
    return False

# http POST the sensor data to remote server
def http_post(sdata):
    headers = {"X-Authorization" : cfg.HTTP_AUTH_KEY }
    urlq=cfg.HTTP_BASE_URL+"?sid="+sid+"&temp="+str(pct)
    try:
        print("p")
        res=req.post(url=urlq, data=sdata, headers=headers)
        res.close()
        return True
    except ValueError as e:
        sys.print_exception(e)
    return False

# Prepare LTE connection to the world
# Assumes SIM card default PIN
def connect_lte(con):
    print("lte")
    time.sleep(1)
    ret=con.send_at_cmd('AT+CPIN="1234"')
    ret=ret.strip()
    print(ret)
    con.attach(apn="internet")
    ca=1
    while not con.isattached():
        print(".a"+str(ca))
        time.sleep(ca)
        machine.idle()
        ca+=1
        if ca > 10:
          print("lte-attach timeout")
          con.reset()
          machine.reset()

    cc=1
    con.connect()
    while not con.isconnected():
        print(".c"+str(cc))
        time.sleep(cc)
        machine.idle()
        cc+=1
        if cc > 10:
          print("lte-connect timeout")
          con.reset()
          machine.reset()

    print('Connected')

# Prepare private WiFi connection to host Raspberry Pi
# Assumes AP has network 192.168.123.0/24 and is 192.168.123.254
def connect_wlan(con):
    print("wlan")
    pycom.rgbled(0x7f2020)
    con.ifconfig(config=('192.168.123.1', '255.255.255.0', '192.168.123.254', '192.168.123.254'))
    print('Searching')
    found=False
    while not found:
        wl=con.scan()
        print(wl)
        for lan in wl:
            if (lan.ssid==cfg.SSID):
                print('Found!')
                print(lan)
                pycom.rgbled(0x7fff20)
                found=True
                break
        print('.')
        time.sleep(5)
        machine.idle()
    connected=False    
    while not connected:
        try:
            con.connect(ssid=cfg.SSID, auth=(WLAN.WPA2, cfg.PASSWORD), timeout=10000)
            pycom.rgbled(0x7f2020)
            while not con.isconnected():      
                print('.')
                time.sleep(4)
                machine.idle()
            connected=True
        except Exception as e:
            print("TimeoutError")
            sys.print_exception(e)

    print('Connected')
    print(con.ifconfig())
    pycom.rgbled(0x20ff20)
    return True

# Connect to local Raspberry Pi MQTT
def connect_sensor():
    print("MQTT to sensor")
    sc.set_callback(sub_sc_cb)
    sc.connect()
    sc.subscribe(topic="sensor/airquality")

# Connect to remote server MQTT
def connect_server():
    print("MQTT to server")
    if len(cfg.SMQTT_BROKER_IP)==0:
      print("No MQTT server defined, skipping")
      return False
    pycom.rgbled(0x40ff40)
    rsc=MQTTClient("ta-sc", cfg.SMQTT_BROKER_IP, port=cfg.SMQTT_BROKER_PORT, keepalive=25000, ssl=True, ssl_params=ssl_params)
    pycom.rgbled(0x00ffff)
    rsc.set_callback(sub_rsc_cb)
    rsc.set_last_will(topic="sensor/"+sid+"/online", msg="0")
    mqtt_connect()
    pycom.rgbled(0x00ff00)
    return rsc

# Update local time from ntp
def update_rtc():
    print("RTC")
    y=time.localtime()[0]
    to=0
    while y == 1970:
        print("r")
        to+=1
        rtc.ntp_sync("pool.ntp.org")
        time.sleep(2)
        y=time.localtime()[0]
        if y > 2020:
          break
        time.sleep(3)
        check_connections()
        if to > 10:
          print("ntp timeout")
          break
    print(time.localtime())

# Note, order is important here:
# Private wlan up first, lte seconds
# We need a working DNS for the MQTT connection and LTE provides that
# local obviously does not.

def startup():
# Wlan first    
    connect_wlan(wlan)    
    time.sleep(1)

# LTE Second (DNS!)
    pycom.rgbled(0x7f2000)
    connect_lte(lte)
    pycom.rgbled(0x7f7f00)
    time.sleep(1)

    print("DNS")
    print(socket.dnsserver())

# Sync RTC to current time
    pycom.rgbled(0x00007f)
    update_rtc()
    pycom.rgbled(0x007f7f)
    time.sleep(1)

# MQTT
    pycom.rgbled(0x00307f)
    if len(cfg.SMQTT_BROKER_IP)>0:
       rsc=connect_server()
    else:
       rsc=False

    pycom.rgbled(0x003f7f)
    connect_sensor()

    pycom.rgbled(0x00ff00)
    time.sleep(1)

    return rsc

# Check that we are still connected and if not, reset
def check_connections():
   if not wlan.isconnected():
     pycom.rgbled(0xff00ff)
     print("Lost wlan connection")
     time.sleep(5)
     machine.reset()
   if not lte.isconnected():
     pycom.rgbled(0xffff00)
     print("Lost lte connection")
     time.sleep(5)
     machine.reset()

# Main loop
# We poll for local mqtt messages, and send a ping every 60 seconds or so
# also the temperature of the pycom device
def main_loop():
  l=0
  while True:
    print("m")
    l+=1
    pycom.rgbled(0x00007f)
    wdt.feed()
    time.sleep(1)
    wdt.feed()
    pct=get_temp()
    pycom.rgbled(0x000000)
    if l>60:
        l=0
        print("l")
        pycom.rgbled(0x0000ff)
        sc.ping()
        if rsc:
          rsc.ping()
          rsc.publish("sensor/"+sid+"/temperature", str(pct))
        pycom.rgbled(0x000000)
    wdt.feed()
    sc.check_msg()
    check_connections()
    machine.idle()

print("ResponseMain-v0.0.2")
print("SID: "+sid)

try:
    rsc=startup()
    wdt=WDT(timeout=35000)
    main_loop()
except Exception as e:
    print("Exception")
    sys.print_exception(e)
    pycom.rgbled(0xff0000)
    time.sleep(10)
    machine.reset()
except OSError as e:
    print("OSError")
    sys.print_exception(e)
    pycom.rgbled(0xff0000)
    time.sleep(10)
    machine.reset()
