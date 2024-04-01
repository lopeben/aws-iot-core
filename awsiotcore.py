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

class AWSIoTConnect(object):

    def __init__(self, clientid = "iotcore-paho", listener = False, topic = "default", ):
        self.connect = False
        self.listener = listener
        self.topic = topic
        self.logger = logging.getLogger(repr(self))
        self.caPath = ''
        self.certPath = ''
        self.keyPath = ''
        self.thingName = "led-controller"
        self.awshost = IOT_ENDPOINT
        self.awsport = 8883
        self.mqttc = paho.Client(clientid)
        self.mqttc.on_connect = self.__on_connect
        #self.mqttc.on_message = self.__on_message

    def __on_connect(self, client, userdata, flags, rc):
        self.connect = True
        
        if self.listener:
            self.mqttc.subscribe(self.topic)

        self.logger.debug("{0}".format(rc))

    def __on_message(self, client, userdata, msg):
        self.logger.info("{0}, {1} - {2}".format(userdata, msg.topic, msg.payload))

    def __on_log(self, client, userdata, level, buf):
        self.logger.debug("{0}, {1}, {2}, {3}".format(client, userdata, level, buf))
        
    def set_credentials(self, rootcafile, certfile, keyfile):
        self.caPath = rootcafile
        self.certPath = certfile
        self.keyPath = keyfile
        
    def set_thing_name(self, thingname):
        self.thingName = thingname
        
    def set_iot_endpoint(self, endpoint, port):
        self.awshost = endpoint
        self.awsport = port
        
    def set_on_connect_callback(self, atconnect):
        self.mqttc.on_connect = atconnect
        
    def set_on_message_callback(self, atmessage):
        self.mqttc.on_message = atmessage
        
    def set_on_log_callback(self, atlog):
        self.mqttc.on_log = self.atlog
        
    def iotconnect(self):
        self.mqttc.tls_set(self.caPath, certfile=self.certPath, keyfile=self.keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

        result_of_connection = self.mqttc.connect(self.awshost, self.awsport, keepalive=120)

        if result_of_connection == 0:
            self.connect = True
            return True
        else:
            self.connect = False
            return False
            
    def send(self, data):
        if self.connect == True:
            self.mqttc.publish(self.topic, data, qos=1)
        else:
            self.logger.debug("Can not send. Connect not established")
        
    def start(self):
        if self.connect == True:
            self.mqttc.loop_start()
        else:
            self.logger.debug("Can not start. Connect not established")

    def test_start(self):
        self.mqttc.loop_start()

        while True:
            sleep(1)
            if self.connect == True:
                tempreading = uniform(20.0, 25.0)
                self.mqttc.publish(self.topic, json.dumps({"temperature": tempreading}), qos=1)
            else:
                self.logger.debug("Attempting to connect.")