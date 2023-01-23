#!/usr/bin/python3
#
# Read Sensirion SPS30 using UART connection and send the data 
# to MQTT server.
#
# Based on initial implementation, that is based on pyserial/SPS30 demo
#
import serial
import time
import datetime
import struct
import binascii
import traceback
import json
import paho.mqtt.client as mqtt
from constants import SERIAL_PORT,      \
                      RPI_TEMP_FILE,    \
                      IP_ADDRESS,       \
                      MQTT_PASSWORD,    \
                      MQTT_USERNAME,    \
                      MEASUREMENTS_TOPIC, \
                      MEASUREMENT_DELAY

login = {'username':MQTT_USERNAME, 'password':MQTT_PASSWORD}
measurements = {}

# This is the number of frames expected as a proper response from the SPS30 assuming there is no byte-stuffing
#
expected_bytes = 47

measurement_names = [
    "PM1.0",
    "PM2.5",
    "PM4.0",
    "PM10.0",
    "NC0.5",
    "NC1.0",
    "NC2.5",
    "NC4.0",
    "NC10.0",
    "TypicalParticleSize"
    ]

# All of the frames are found using the SPS30 datasheet available in
# the README.md or at
# https://cdn.sparkfun.com/assets/2/d/2/a/6/Sensirion_SPS30_Particulate_Matter_Sensor_v0.9_D1__1_.pdf
#
measurement_start_frame_start_bits = ['7e', '00', '03', '00', '28']
measurement_empty_frame = ['7e', '00', '03', '00', '00', 'fc', '7e']
measurement_frame_number = 0

time_format = "%d-%m-%Y-%H-%M-%S-%f"
start_time = datetime.datetime.now()
start_time_string = start_time.strftime(time_format)

class SHDLC:
    # MOSI Frames that are sent to sps30 via SHDLC protocol over UART
    __measurement_start     = "7E0000020103F97E" # 8 Bytes
    __measurement_stop      = "7E000100FE7E"     # 6 Bytes
    __read_measured_values  = "7E000300FC7E"     # 6 Bytes
    __start_cleaning        = "7E005600A97E"     # 6 bytes

    # Convert to bytes format for pyserial
    measurement_start = bytes.fromhex(__measurement_start)
    measurement_read  = bytes.fromhex(__read_measured_values)
    measurement_stop  = bytes.fromhex(__measurement_stop)
    start_cleaning    = bytes.fromhex(__start_cleaning)

command = SHDLC() # initialize communication frames
frame_number = -1 # used to track and count number of response frames

# MISO frame return is: [Start, ADR, CMD, State, , , ]

def prepare_measurements(byte_list, frame_number, diff) -> None:
    length = len(byte_list)
    if length > expected_bytes:
        s = [i for i, x in enumerate(byte_list) if x == '7d']
        for j in range(length - expected_bytes):
            if byte_list[(s[j] - j) + 1] == '5e':
                byte_list[(s[j] - j) + 1] = '7e'
                byte_list.pop((s[j] - j))
            elif byte_list[(s[j] - j) + 1] == '5d':
                byte_list[(s[j] - j) + 1] = '7d'
                byte_list.pop((s[j] - j))
            elif byte_list[(s[j] - j) + 1] == '31':
                byte_list[(s[j] - j) + 1] = '11'
                byte_list.pop((s[j] - j))
            elif byte_list[(s[j] - j) + 1] == '33':
                byte_list[(s[j] - j) + 1] = '13'
                byte_list.pop((s[j] - j))

    byte_index = 5 # Skip the initial 5 bytes of information data
    measurement_length = 4 # length in bytes
    measurement_bytes_length = len(byte_list) - byte_index # Skip the initial 5 bytes of information data
    i = 0 # used for iterating through measurement names

    while byte_index <= measurement_bytes_length:
        measurement = hex_to_ieee(byte_list, byte_index)
        #print(f'{measurement_names[i]} --- {measurement}')
        measurements[measurement_names[i]] = f'{measurement:.3f}'
        byte_index += measurement_length
        i += 1
    measurements['frame'] = frame_number
    measurements['diff'] = diff
    measurements['uptime'] = time.monotonic()
    measurements['temp'] = get_temp()

def hex_to_ieee(byte_list, n):
    byte_string = byte_list[n:n+4]
    hex_string = byte_string[0] + byte_string[1] + byte_string[2] + byte_string[3]
    ieee_result = struct.unpack('>f', binascii.unhexlify(hex_string))
    return ieee_result[0]

def get_temp():
    rpi_temp = -256
    with open(RPI_TEMP_FILE, 'r') as f:
        rpi_temp = f.read().strip()
    return rpi_temp

while True:
    print('SPS30 Sensor reader started!')
    try:
        client = mqtt.Client(client_id="sps30-reader", clean_session=True)
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.connect("127.0.0.1", 1883, 60)
        with serial.Serial(SERIAL_PORT, baudrate = 115200, stopbits=1, bytesize=8, timeout=1) as sps30:
            time.sleep(3)
            sps30.write(command.measurement_start) #Starts the sensor measurements
            #print(f'Number of bytes in output buffer {sps30.out_waiting}')
            while True:
                response_frames = {}
                #time.sleep(1)
                sps30.write(command.measurement_read) #The reason this was giving a response is pyserial.write returns the number of bits the command is.
                #print(f'Number of bytes in output buffer {sps30.out_waiting}')
                # output_buff_bytes = sps30.out_waiting
                # This doesn't seem to be an issue anymore because whatever is in the output buffer gets read anyway and handled below
                # if output_buff_bytes:
                #     # To do: properly handle this error
                #     print(f'Number of bytes in output buffer {sps30.out_waiting}, resetting')
                #     sps30.reset_output_buffer()
                #     print(f'Number of bytes in output buffer {sps30.out_waiting}')
                #     # sps30.write(command.measurement_read)
                #     raise serial.SerialException('bytes in the output buffer')
                # print(f'Number of bytes in output buffer {sps30.out_waiting}')
                response = sps30.read()
                #print(response)
                hex_byte = response.hex()
                if hex_byte != '7e':
                    continue
                frame_number += 1
                response_frames[frame_number] = [hex_byte]
                current_frame = True
                while current_frame:
                    #hex_byte = sps30.read().hex()
                    response = sps30.read()
                    #print(response)
                    hex_byte = response.hex()
                    if hex_byte == '' or hex_byte == '7e':
                        current_frame = False
                    response_frames[frame_number].append(hex_byte)
                frame = response_frames[frame_number]
                # track number of measurement frames and empty frames between measurements
                if frame[0:5] == measurement_start_frame_start_bits:
                    new_frame_number = frame_number
                    diff = new_frame_number - measurement_frame_number
                    #measurements converted to proper format
                    prepare_measurements(frame, measurement_frame_number, diff)
                    # print(measurements)
                    # publish.single(MEASUREMENTS_TOPIC, f'{measurements}', hostname=IP_ADDRESS, auth=login)
                    client.publish(MEASUREMENTS_TOPIC, json.dumps(measurements))
                    time.sleep(MEASUREMENT_DELAY)
                    measurement_frame_number = frame_number
                client.loop()
    # except serial.SerialException as e:
    #     print(type(e).__name__)
    #     print(e)
    #     print(traceback.format_exc())
    except Exception as e: #catches all exceptions
        print(type(e).__name__)
        print(e)
        print(traceback.format_exc())
        time.sleep(5)
