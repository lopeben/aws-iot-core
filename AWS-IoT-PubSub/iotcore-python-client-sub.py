#!/usr/bin/python

# this source is part of my Hackster.io project:  https://www.hackster.io/mariocannistra/radio-astronomy-with-rtl-sdr-raspberrypi-and-amazon-aws-iot-45b617

# use this program to test the AWS IoT certificates received by the author
# to participate to the spectrogram sharing initiative on AWS cloud

# this program will subscribe and show all the messages sent by its companion
# awsiotpub.py using the AWS IoT hub

import paho.mqtt.client as paho
import os
import socket
import ssl
from secrets import IOT_ENDPOINT

def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc) )
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/sdk/test/python/temperature" , 1 )

def on_message(client, userdata, msg):
    print("topic: "+msg.topic)
    print("payload: "+str(msg.payload))

#def on_log(client, userdata, level, msg):
#    print(msg.topic+" "+str(msg.payload))

mqttc = paho.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
#mqttc.on_log = on_log

awshost = IOT_ENDPOINT
awsport = 8883
clientId = "iotcore-paho-sub"
thingName = "iotcore-paho-sub"
caPath = "./AmazonRootCA1.pem"
certPath = "./32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-certificate.pem.crt" #"./6a0629b851b19118983e03e1c2d010fc51a59a2932668e901237079ee1f7f85c-certificate.pem.crt"
keyPath = "./32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-private.pem.key" #"./6a0629b851b19118983e03e1c2d010fc51a59a2932668e901237079ee1f7f85c-private.pem.key"

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

print("Attempting connect...")
mqttc.connect(awshost, awsport, keepalive=60)

mqttc.loop_forever()