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

import settings as cfg

# Signal that we are now in main, blue led
pycom.rgbled(0x00007f)

rtc=RTC()
lte=LTE()
wlan=WLAN(mode=WLAN.STA)
sc=MQTTClient("pycom-sc", "192.168.123.254", port=1883)

ssl_params = {
 "server_hostname": cfg.SMQTT_BROKER_IP,
 "cert_reqs":ussl.CERT_REQUIRED,
 "ca_certs":"/flash/cert/ca.pem",
 "keyfile":"/flash/cert/pycom.key",
 "certfile":"/flash/cert/pycom.crt"}

# Sensor ID
sid=ubinascii.hexlify(machine.unique_id()).decode()

sdata=''
mqc=1

#uart = machine.UART(1, baudrate=115200)
#uart.init(115200, bits=8, stop=1, pins=("P3", "P4"),  rx_buffer_size=4096)

# Local MQTT sensor topic cb
def sub_sc_cb(topic, msg):
    pycom.rgbled(0x7f7f00)
    print(topic+" is "+msg)
    sdata=msg
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
    urlq=cfg.HTTP_BASE_URL+"?sid="+sid
    res=req.post(url=urlq, data=sdata, headers=headers)
    res.close()
    return True

# Prepare LTE connection to the world
# Assumes SIM card default PIN
def connect_lte(con):
    print("lte")
    time.sleep(1)
    ret=con.send_at_cmd('AT+CPIN="1234"')
    ret=ret.strip()
    print(ret)
    con.attach(apn="internet")
    while not con.isattached():
        print('.')
        time.sleep(1)
        machine.idle()
    con.connect()
    while not con.isconnected():
        print('.')
        time.sleep(1)
        machine.idle()
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
            if (lan.ssid=='ResponseSensor'):
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
    pycom.rgbled(0x40ff40)
    rsc=MQTTClient("ta-sc", cfg.SMQTT_BROKER_IP, port=cfg.SMQTT_BROKER_PORT, keepalive=25000, ssl=True, ssl_params=ssl_params)
    pycom.rgbled(0x00ffff)
    rsc.set_callback(sub_rsc_cb)
    rsc.set_last_will(topic="sensor/"+sid+"/online", msg="0")
    rsc.connect()
    rsc.publish("sensor/"+sid+"/online", str(1))
    rsc.publish("sensor/"+sid+"/reset", str(machine.reset_cause()))
    pycom.rgbled(0x00ff00)
    return rsc

# Update local time from ntp
def update_rtc():
    print("RTC")
    y=time.localtime()[0]
    while y == 1970:
        rtc.ntp_sync("pool.ntp.org")
        y=time.localtime()[0]
        time.sleep(5)
        machine.idle()
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
    rsc=connect_server()

    pycom.rgbled(0x003f7f)
    connect_sensor()

    pycom.rgbled(0x00ff7f)
    time.sleep(1)

    pycom.rgbled(0x00ff00)
    time.sleep(1)

    return rsc

# Main loop
# We poll for local mqtt messages, and send a ping every 60 seconds or so
# also the temperature of the pycom device
def main_loop():
  l=0
  while True:
    l+=1
    pycom.rgbled(0x00007f)
    time.sleep(1)
    pycom.rgbled(0x000000)
    if l>60:
        pycom.rgbled(0x0000ff)
        sc.ping()
        rsc.ping()
        l=0
        pct=((machine.temperature() - 32) / 1.8)
        rsc.publish("sensor/"+sid+"/temperature", str(pct))
        pycom.rgbled(0x000000)
    sc.check_msg()
    machine.idle()
#    rsc.check_msg()
#    machine.idle()

print("ResponseMain-v0.0.1")
print("Starting...")
try:
    rsc=startup()
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
    pycom.rgbled(0xff00ff)
    time.sleep(10)
    machine.reset()
