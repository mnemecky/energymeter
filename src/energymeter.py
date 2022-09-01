#/usr/bin/python

import usb
import sys,time
sys.path.append("..")
from arduino.usbdevice import ArduinoUsbDevice
import paho.mqtt.client as mqtt
import os

# Read env variables
delay = os.getenv("DELAY") or 300
mqtt_host = os.getenv("MQTT_HOST") or "localhost"
mqtt_topic = os.getenv("MQTT_TOPIC") or "/meter/energymeter"
mqtt_client = os.getenv("MQTT_CLIENT") or "energymeter"

def connectDigistump():
    try:
        dev = ArduinoUsbDevice(idVendor=0x16c0, idProduct=0x05df)
    except Exception as e:
        print( "Error: ", str(e) )
        exit()

    return dev


def resetCounter(dev):
    dev.write(ord('Z'))
    return 0


def readCounter(dev):
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


if __name__ == "__main__":

    # connect to Digistump device, reset counter
    device = connectDigistump()
    count = resetCounter(device)
    print('connected to Digistump device')

    # connect to MQTT broker
    mqtt = mqtt.Client(mqtt_client)
    mqtt.connect(mqtt_host)
    print('MQTT connected to %s, using topic %s' % (mqtt_host, mqtt_topic) )

    while 1 == 1:

        # read counter from Digistump
        result = readCounter(device)

        # calculate power usage in Watt
        power = ( result - count ) * ( 3600 / delay )
        if( power < 0 ):
            count = resetCounter(device)
        else:
            mqtt.publish(mqtt_topic + '/power', power )
            print('Power usage %d W, measurement period %d s' % (power, delay) )
            count = result

        time.sleep( delay )

