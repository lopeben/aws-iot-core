import os
import ssl
import json
import random
import logging

import paho.mqtt as pversion
import paho.mqtt.client as paho

from enum import Enum
from time import sleep
from random import uniform

logging.basicConfig(level=logging.INFO)

# Refactored original source - https://github.com/mariocannistra/python-paho-mqtt-for-aws-iot


class CallbackIndex(Enum):
    UPDATE_DELTA    = 0
    GET_ACCEPTED    = 1
    GET_REJECTED    = 2
    UPDATE_ACCEPTED = 3
    UPDATE_REJECTED = 4
    DELETE_ACCEPTED = 5
    DELETE_REJECTED = 6
    UPDATE_DOCUMENT = 7
    SUBSCRIBE_USER  = 8
    PUBLISH_USER    = 9


class AWSIoTConnect(object):

    def __init__(self, thingname, endpoint, clientid = None, topic = "default", listener = False, usercallbacks = None):
        self.connect   = False
        self.listener  = listener
        self.topic     = topic
        self.logger    = logging.getLogger(repr(self))
        self.caPath    = ''
        self.certPath  = ''
        self.keyPath   = ''
        self.thingName = thingname
        self.awshost   = endpoint
        self.awsport   = 8883
        self.shadow_document = ''

        if clientid == None:
            clientid = f'awsiot-core-{random.randint(0, 1000)}'

        MQTTVERSION = 2
        major, minor, patch = self.__checkversion()
        if (major < MQTTVERSION):
            self.mqttc = paho.Client(clientid)
        else:
            self.mqttc = paho.Client(paho.CallbackAPIVersion.VERSION1, clientid)
        
        
        self.mqttc.on_connect = self.__on_connect
        self.mqttc.on_message = self.__on_message
        
        self.SHADOW_UPDATE_TOPIC          = "$aws/things/" + self.thingName + "/shadow/update"
        self.SHADOW_UPDATE_ACCEPTED_TOPIC = "$aws/things/" + self.thingName + "/shadow/update/accepted"
        self.SHADOW_UPDATE_REJECTED_TOPIC = "$aws/things/" + self.thingName + "/shadow/update/rejected"
        self.SHADOW_UPDATE_DELTA_TOPIC    = "$aws/things/" + self.thingName + "/shadow/update/delta"
        self.SHADOW_UPDATE_DOCUMENT_TOPIC = "$aws/things/" + self.thingName + "/shadow/update/documents" 
        
        self.SHADOW_GET_TOPIC             = "$aws/things/" + self.thingName + "/shadow/get"
        self.SHADOW_GET_ACCEPTED_TOPIC    = "$aws/things/" + self.thingName + "/shadow/get/accepted"
        self.SHADOW_GET_REJECTED_TOPIC    = "$aws/things/" + self.thingName + "/shadow/get/rejected"

        self.SHADOW_DELETE_TOPIC          = "$aws/things/" + self.thingName + "/shadow/delete"
        self.SHADOW_DELETE_ACCEPTED_TOPIC = "$aws/things/" + self.thingName + "/shadow/accepted" 
        self.SHADOW_DELETE_REJECTED_TOPIC = "$aws/things/" + self.thingName + "/shadow/rejected" 
        
        if None == usercallbacks:
            self.callbacks = [self.__stub] * len(list(CallbackIndex))
        else:
            self.callbacks = usercallbacks

    def __stub(self):
        pass

    def __checkversion(self):
        mqtt_version = pversion.__version__
        # Split the version into major, minor, and patch numbers
        major, minor, patch = map(int, mqtt_version.split('.'))

        return major, minor, patch

    def __on_connect(self, client, userdata, flags, rc):
        self.logger.debug("{0}".format(rc))

        if self.listener:
            self.mqttc.subscribe(self.SHADOW_UPDATE_DELTA_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_UPDATE_ACCEPTED_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_UPDATE_REJECTED_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_UPDATE_DOCUMENT_TOPIC, 1)	
            self.mqttc.subscribe(self.SHADOW_GET_ACCEPTED_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_GET_REJECTED_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_DELETE_ACCEPTED_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_DELETE_REJECTED_TOPIC, 1)
            
            self.mqttc.subscribe(self.topic)

        self.connect = True
        
    def __on_message(self, client, userdata, msg):
        self.logger.debug("{0}, {1} - {2}".format(userdata, msg.topic, msg.payload))

        if str(msg.topic) == self.SHADOW_UPDATE_DELTA_TOPIC:
            self.logger.debug( "###SHADOW_UPDATE_DELTA_TOPIC###")
            self.logger.debug( "Response JSON: " + str(msg.payload) )

            self.callbacks[CallbackIndex.UPDATE_DELTA.value](self, msg.payload, "DELTA")

        elif str(msg.topic) == self.SHADOW_GET_ACCEPTED_TOPIC:
            self.logger.debug( "###SHADOW_GET_ACCEPTED_TOPIC###" )
            self.logger.debug( "Response JSON: " + str(msg.payload) )

            self.callbacks[CallbackIndex.GET_ACCEPTED.value](self, msg.payload, "GET_REQ")

        elif str(msg.topic) == self.SHADOW_GET_REJECTED_TOPIC:
            self.logger.debug( "###SHADOW_GET_REJECTED_TOPIC###")
            self.logger.debug( "Error Code: " + str(msg.payload) )
            
            self.callbacks[CallbackIndex.GET_REJECTED.value]()

        elif str(msg.topic) == self.SHADOW_UPDATE_ACCEPTED_TOPIC:
            self.logger.debug( "###SHADOW_UPDATE_ACCEPTED_TOPIC###" )
            self.logger.debug( "Response JSON: " + str(msg.payload) )

            self.callbacks[CallbackIndex.UPDATE_ACCEPTED.value]()

        elif str(msg.topic) == self.SHADOW_UPDATE_REJECTED_TOPIC:
            self.logger.debug( "###SHADOW_UPDATE_REJECTED_TOPIC###" )
            self.logger.debug( "Response JSON: " + str(msg.payload) )

            self.callbacks[CallbackIndex.UPDATE_REJECTED.value]()

        elif str(msg.topic) == self.SHADOW_DELETE_ACCEPTED_TOPIC:
            self.logger.debug( "###SHADOW_DELETE_ACCEPTED_TOPIC###" )
            self.logger.debug( "Response JSON: " + str(msg.payload) )

            self.callbacks[CallbackIndex.DELETE_ACCEPTED.value]()

        elif str(msg.topic) == self.SHADOW_DELETE_REJECTED_TOPIC:
            self.logger.debug( "###SHADOW_DELETE_REJECTED_TOPIC###" )
            self.logger.debug( "Response JSON: " + str(msg.payload) )

            self.callbacks[CallbackIndex.DELETE_REJECTED.value]()

        elif str(msg.topic) == self.SHADOW_UPDATE_DOCUMENT_TOPIC:
            self.logger.debug( "###SHADOW_UPDATE_DOCUMENT_TOPIC###" )
            self.logger.debug( "Response JSON: " + str(msg.payload) )
            
            self.__store_shadow_document(msg.payload)
            self.callbacks[CallbackIndex.UPDATE_DOCUMENT.value]()
        
        else:
            self.logger.debug( "###OTHER PUBSUB_TOPIC###" )
            self.logger.debug( "Response JSON: " + str(msg.payload) )
            
            self.callbacks[CallbackIndex.SUBSCRIBE_USER.value](client, userdata, msg)
        
    def __on_subscribe(self, mosq, obj, mid, granted_qos):
        #As we are subscribing to 3 Topics, wait till all 3 topics get subscribed
        #for each subscription mid will get incremented by 1 (starting with 1)
        #print("Subscribed: %d" % mid)
        if mid == 3:
            # Fetch current Shadow status. Useful for re-connection scenario. 
            self.mqttc.publish(self.SHADOW_GET_TOPIC, "", qos=1)

    def __on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print( "Disconnected from AWS IoT. Trying to auto-reconnect..." )
            self.connect = False

    def __on_log(self, client, userdata, level, buf):
        self.logger.debug("{0}, {1}, {2}, {3}".format(client, userdata, level, buf))
    
    def __store_shadow_document(self, shadow_document):
        if self.connect == True:
            self.shadow_document = ''
            self.shadow_document = shadow_document
        
    def set_credentials(self, rootcafile, certfile, keyfile):
        self.caPath = rootcafile
        self.certPath = certfile
        self.keyPath = keyfile
        
    def set_iot_endpoint(self, endpoint, port):
        self.awshost = endpoint
        self.awsport = port
        
    def set_on_log_callback(self, atlog):
        self.mqttc.on_log = atlog

    def set_topic(self, topic):
        self.topic = topic

    def set_callback(self, index, callbackfn):
        self.callbacks[index] = callbackfn

    def set_shadow_document(self, shadow_document):
        if self.connect == True:
            self.mqttc.publish(self.SHADOW_UPDATE_TOPIC, shadow_document, qos=1)

    def get_shadow_document(self):
        return self.shadow_document
    
    def is_connected(self):
        return self.connect

    def connect_attempt(self):

        self.mqttc.on_subscribe  = self.__on_subscribe
        self.mqttc.on_disconnect = self.__on_disconnect

        self.mqttc.tls_set(self.caPath, certfile=self.certPath, keyfile=self.keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
        result_of_connection = self.mqttc.connect(self.awshost, self.awsport, keepalive=120)

        if result_of_connection == 0:
            self.connect = True
            return True
        else:
            self.connect = False
            return False
            
    def publish(self, data):
        if self.connect == True:
            self.mqttc.publish(self.topic, data, qos=1)
        else:
            self.logger.debug("Can not send. Connection not established")
        
    def listen(self):
        if self.connect == True:
            self.mqttc.loop_start()
        else:
            self.logger.debug("Can not start. Connection not established")
            
    def spinlock(self):
        if self.connect == True:
            self.mqttc.loop_forever()
        else:
            self.logger.debug("Can not start. Connection not established")

    def telemetry(self):
        self.mqttc.loop_start()
        while True:
            mtopic, mdata, srate, gate = self.callbacks[CallbackIndex.PUBLISH_USER.value](self)
            sleep(srate)
            if (self.connect == True) and (gate == True):
                self.mqttc.publish(mtopic, mdata, qos=1)

    def test(self):
        self.mqttc.loop_start()

        while True:
            sleep(5)
            if self.connect == True:
                tempreading = uniform(20.0, 25.0)
                self.mqttc.publish(self.topic, json.dumps({"temperature": tempreading}), qos=1)
            else:
                self.logger.debug("Attempting to connect.")