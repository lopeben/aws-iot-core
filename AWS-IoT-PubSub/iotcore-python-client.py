import paho.mqtt.client as paho
import os
import socket
import ssl
from time import sleep
from random import uniform
from secrets import IOT_ENDPOINT
import json

import logging
logging.basicConfig(level=logging.INFO)

# Refactored original source - https://github.com/mariocannistra/python-paho-mqtt-for-aws-iot

class PubSub(object):

    def __init__(self, listener = False, topic = "default"):
        self.connect = False
        self.listener = listener
        self.topic = topic
        self.logger = logging.getLogger(repr(self))


    def __on_connect(self, client, userdata, flags, rc):
        self.connect = True
        
        if self.listener:
            self.mqttc.subscribe(self.topic)

        self.logger.debug("{0}".format(rc))


    def __on_message(self, client, userdata, msg):
        self.logger.info("{0}, {1} - {2}".format(userdata, msg.topic, msg.payload))


    def __on_log(self, client, userdata, level, buf):
        self.logger.debug("{0}, {1}, {2}, {3}".format(client, userdata, level, buf))


    def bootstrap_mqtt(self):

        self.mqttc = paho.Client()
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_message = self.__on_message
        self.mqttc.on_log = self.__on_log

        awshost = IOT_ENDPOINT
        awsport = 8883
        clientId = "iotcore-paho"
        thingName = "led-controller" #"iotcore-paho"
        
        caPath = "./AmazonRootCA1.pem"
        certPath = "./32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-certificate.pem.crt" #./6a0629b851b19118983e03e1c2d010fc51a59a2932668e901237079ee1f7f85c-certificate.pem.crt"
        keyPath =  "./32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-private.pem.key"     #./6a0629b851b19118983e03e1c2d010fc51a59a2932668e901237079ee1f7f85c-private.pem.key"

        self.mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

        result_of_connection = self.mqttc.connect(awshost, awsport, keepalive=120)

        if result_of_connection == 0:
            self.connect = True

        return self


    def start(self):
        self.mqttc.loop_start()

        while True:
            sleep(2)
            if self.connect == True:
                tempreading = uniform(20.0, 25.0)
                self.mqttc.publish(self.topic, json.dumps({"temperature": tempreading}), qos=1)
            else:
                self.logger.debug("Attempting to connect.")


if __name__ == '__main__':
    
    PubSub(listener = True, topic = "test/event").bootstrap_mqtt().start()
    
    