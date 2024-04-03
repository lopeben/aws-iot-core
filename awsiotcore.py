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

SHADOW_UPDATE_DELTA_CB    = 0
SHADOW_GET_ACCEPTED_CB    = 1
SHADOW_GET_REJECTED_CB    = 2
SHADOW_UPDATE_ACCEPTED_CB = 3
SHADOW_UPDATE_REJECTED_CB = 4

class AWSIoTConnect(object):

    def __init__(self, clientid = 'iotcore-paho', thingname = 'default', endpoint = IOT_ENDPOINT, listener = False, topic = "default", usrcallbacks = None):
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
        
        self.mqttc            = paho.Client(clientid)
        self.mqttc.on_connect = self.__on_connect
        #self.mqttc.on_message = self.__on_message
        
        self.SHADOW_UPDATE_TOPIC          = "$aws/things/" + self.thingName + "/shadow/update"
        self.SHADOW_UPDATE_ACCEPTED_TOPIC = "$aws/things/" + self.thingName + "/shadow/update/accepted"
        self.SHADOW_UPDATE_REJECTED_TOPIC = "$aws/things/" + self.thingName + "/shadow/update/rejected"
        self.SHADOW_UPDATE_DELTA_TOPIC    = "$aws/things/" + self.thingName + "/shadow/update/delta"
        self.SHADOW_GET_TOPIC             = "$aws/things/" + self.thingName + "/shadow/get"
        self.SHADOW_GET_ACCEPTED_TOPIC    = "$aws/things/" + self.thingName + "/shadow/get/accepted"
        self.SHADOW_GET_REJECTED_TOPIC    = "$aws/things/" + self.thingName + "/shadow/get/rejected"
        
        self.callbacks  = usrcallbacks

    def __on_connect(self, client, userdata, flags, rc):
        self.connect = True
        
        if self.listener:
          
            # Subscribe to Delta Topic
            self.mqttc.subscribe(self.SHADOW_UPDATE_DELTA_TOPIC, 1)
            # Subscribe to Update Accepted and Rejected Topics
            self.mqttc.subscribe(self.SHADOW_UPDATE_ACCEPTED_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_UPDATE_REJECTED_TOPIC, 1)	
            # Subscribe to Get Accepted and Rejected Topics
            self.mqttc.subscribe(self.SHADOW_GET_ACCEPTED_TOPIC, 1)
            self.mqttc.subscribe(self.SHADOW_GET_REJECTED_TOPIC, 1)
            
            # Subscribe to Standard PubSub topic 
            self.mqttc.subscribe(self.topic)

        self.logger.debug("{0}".format(rc))
        
        ## self.callback()

    def __on_message(self, client, userdata, msg):
        self.logger.info("{0}, {1} - {2}".format(userdata, msg.topic, msg.payload))
        if str(msg.topic) == self.SHADOW_UPDATE_DELTA_TOPIC:
            print( "\nNew Delta Message Received..." )
            SHADOW_STATE_DELTA = msg.payload #str(msg.payload)
            print( SHADOW_STATE_DELTA )
            ## Insert here a user callback function
            #self.callbacks[SHADOW_UPDATE_DELTA_CB]()
            self.callback(SHADOW_UPDATE_DELTA_CB, (SHADOW_STATE_DELTA, "DELTA"))
            ### LED_Status_Change(SHADOW_STATE_DELTA, "DELTA")
        elif str(msg.topic) == self.SHADOW_GET_ACCEPTED_TOPIC:
            print( "\nReceived State Doc with Get Request..." )
            SHADOW_STATE_DOC = msg.payload # str(msg.payload)
            print( SHADOW_STATE_DOC )
            #self.callbacks[SHADOW_GET_ACCEPTED_CB]()
            self.callback(SHADOW_GET_ACCEPTED_CB, (SHADOW_STATE_DOC, "GET_REQ"))
        elif str(msg.topic) == self.SHADOW_GET_REJECTED_TOPIC:
            SHADOW_GET_ERROR = msg.payload #str(msg.payload)
            print( "\n---ERROR--- Unable to fetch Shadow Doc...\nError Response: " + SHADOW_GET_ERROR )
            self.callbacks[SHADOW_GET_REJECTED_CB]()
        elif str(msg.topic) == self.SHADOW_UPDATE_ACCEPTED_TOPIC:
            print( "\nLED Status Change Updated SUCCESSFULLY in Shadow..." )
            print( "Response JSON: " + str(msg.payload) )
            self.callbacks[SHADOW_UPDATE_ACCEPTED_CB]()
        elif str(msg.topic) == self.SHADOW_UPDATE_REJECTED_TOPIC:
            SHADOW_UPDATE_ERROR = msg.payload #str(msg.payload)
            print( "\n---ERROR--- Failed to Update the Shadow...\nError Response: " + SHADOW_UPDATE_ERROR )
            self.callbacks[SHADOW_UPDATE_REJECTED_CB]()
        else:
            print( "AWS Response Topic: " + str(msg.topic) )
            print( "QoS: " + str(msg.qos) )
            print( "Payload: " + str(msg.payload) )
        
    def __on_subscribe(self, mosq, obj, mid, granted_qos):
        #As we are subscribing to 3 Topics, wait till all 3 topics get subscribed
        #for each subscription mid will get incremented by 1 (starting with 1)
        print("Subscribed: %d" % mid)
        if mid == 3:
            # Fetch current Shadow status. Useful for re-connection scenario. 
            self.mqttc.publish(self.SHADOW_GET_TOPIC, "", qos=1)

    def __on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print( "Disconnected from AWS IoT. Trying to auto-reconnect..." )
            self.connect = False

    def __on_log(self, client, userdata, level, buf):
        self.logger.debug("{0}, {1}, {2}, {3}".format(client, userdata, level, buf))
        
    def __callback(self, callbackid, args):
        self.callbacks[callbackid](args)
        
    def set_credentials(self, rootcafile, certfile, keyfile):
        self.caPath = rootcafile
        self.certPath = certfile
        self.keyPath = keyfile
        
    def set_iot_endpoint(self, endpoint, port):
        self.awshost = endpoint
        self.awsport = port
        
    #def set_on_connect_callback(self, atconnect):
    #    self.mqttc.on_connect = atconnect
        
    #def set_on_message_callback(self, atmessage):
    #    self.mqttc.on_message = atmessage
        
    def set_on_log_callback(self, atlog):
        self.mqttc.on_log = atlog

    def set_topic(self, topic):
        self.topic = topic
        
    def connect_attempt(self):
    
        self.mqttc.on_message    = self.__on_message
        self.mqttc.on_connect    = self.__on_connect
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
            self.logger.debug("Can not send. Connect not established")
        
    def listen(self):
        if self.connect == True:
            self.mqttc.loop_start()
        else:
            self.logger.debug("Can not start. Connect not established")
            
    def forever(self):
        if self.connect == True:
            self.mqttc.loop_forever()
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