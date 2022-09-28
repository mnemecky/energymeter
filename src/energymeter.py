#/usr/bin/python

import usb
import sys,time
from arduino.usbdevice import ArduinoUsbDevice
import paho.mqtt.client as mqtt
import os
sys.path.append("..")


# Read env variables
delay = int(os.getenv("DELAY")) or 300
mqtt_host = os.getenv("MQTT_HOST") or "localhost"
mqtt_topic = os.getenv("MQTT_TOPIC") or "/meter"
mqtt_client = os.getenv("MQTT_CLIENT") or "energymeter"
mqtt_lwt = os.getenv("MQTT_LWT") or "lwt"
debug = os.getenv("DEBUG").lower() == "on" or os.getenv("DEBUG").lower() == "true"

# MQTT topics
topic = mqtt_topic + '/' + mqtt_client
topic_power = topic + '/power'
topic_counter = topic + '/counter'
topic_cmd = topic + '/cmd'
topic_lwt = topic + '/lwt'

# MQTT commands
CMD_RESET = 'reset'
CMD_READENERGY = 'energy'


# global variables
digiCounter = 0
lastRead = 0

#
# Digistump device routines
#

# connect to device
def digi_connectDevice():
    try:
        dev = ArduinoUsbDevice(idVendor=0x16c0, idProduct=0x05df)
    except Exception as e:
        print( "Error: ", str(e) )
        exit()

    return dev


# reset counter
def digi_resetCounter(dev):
    dev.write(ord('Z'))
    return 0


# read counter
def digi_readCounter(dev):

    resp = ""
    dev.write(ord('R'))

    while 1 == 1:
        try:
            x = chr(device.read())
        except Exception as e:
            resp = "0"
            break

        if( x == '\n' ):
            break
        else:
            resp += x

    return int( resp )


#
# MQTT routines
#

# callback on connect
def cb_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        # connection succesfull
        client.connected_flag = True
        if debug: print("debug: MQTT connection successfull")
        client.subscribe(topic_cmd)
        client.publish(topic_lwt,"ON",0,True)
    else:
        print("debug: MQTT connection failed, error ",rc)

# callback on message
def cb_mqtt_message(client, userdata, message):
    command = message.payload.decode("utf-8")
    if command == CMD_RESET:
        resetCounter()
    elif command == CMD_READENERGY:
        energy = readEnergy()

# connect to MQTT server
def mqtt_connect():
    client = mqtt.Client(mqtt_client)
    client.connected_flag = False
    client.on_connect = cb_mqtt_connect
    client.will_set(topic_lwt,"OFF",0,True)
    client.loop_start()
    client.connect(mqtt_host)

    while not client.connected_flag:
        if debug: print("debug: waiting for MQTT connection...")
        time.sleep(1)

    # register message callback
    client.on_message = cb_mqtt_message

    return client


def readEnergy(device):
    global digiCounter
    global lastRead

    # read counter from Digistump
    result = digi_readCounter(device)
    now = time.time()
    deltaT = now - lastRead

    # calculate power usage in Watt
    # the meter produces 1000 impulses per kWh
    power = ( result - digiCounter ) * ( 3600 / deltaT )
    if( power < 0 ):
        digiCounter = resetCounter(device)
        lastRead = time.time()
    else:
        if debug: print('Power usage %d W, measurement period %d s' % (power, deltaT) )
        digiCounter = result
        lastRead = now

    return power


if __name__ == "__main__":

    # connect to Digistump device, reset counter
    device = digi_connectDevice()
    count = digi_resetCounter(device)
    lastRead = time.time()
    if debug: print('connected to Digistump device')

    # connect to MQTT broker
    mqtt_conn = mqtt_connect()

    # main loop
    while 1 == 1:

        time.sleep( delay )

        # read counter from Digistump
        power = readEnergy(device)
        mqtt_conn.publish(mqtt_topic + '/power', power )

    mqtt_conn.publish(topic_lwt,"OFF",0,True)
    mqtt_conn.loop_stop()
    mqtt_conn.disconnect()
