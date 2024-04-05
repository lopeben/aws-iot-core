import time
import json

from random import uniform
from awsiotcore import AWSIoTConnect, CallbackIndex
from secrets import CONCEPT_LAB


rootcafile = "./certificates/AmazonRootCA1.pem"
certfile   = "./certificates/32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-certificate.pem.crt"
keyfile    = "./certificates/32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-private.pem.key"


def master_switch(aws, shadow_document, shadow_type):

    DESIRED_STATUS       = ""
    SHADOW_STATE_REPORT_ON  = """{"state" : {"reported" : {"switch" : "ON" }}}"""
    SHADOW_STATE_REPORT_OFF = """{"state" : {"reported" : {"switch" : "OFF"}}}"""

    # Parse Welcome Status from Shadow
    shadow_state = json.loads(shadow_document)

    if shadow_type == "DELTA":
        DESIRED_STATUS = shadow_state['state']['switch1']
    elif shadow_type == "GET_REQ":
        DESIRED_STATUS = shadow_state['state']['desired']['switch1']
    else:
        print( "---ERROR--- Unhandled Type.")

    print( "Desired Status: " + DESIRED_STATUS )

    # Resolve Shadow Delta in Cloud"  
    if DESIRED_STATUS == "ON":
        print( "Desired ON. Reporting status to shadow..." )
        aws.mqttc.publish(aws.SHADOW_UPDATE_TOPIC, SHADOW_STATE_REPORT_ON, qos=1)
    elif DESIRED_STATUS == "OFF":
        print( "Desired OFF. Reporting status back to shadow..." )
        aws.mqttc.publish(aws.SHADOW_UPDATE_TOPIC, SHADOW_STATE_REPORT_OFF, qos=1)
    else:
        print( "---ERROR--- Invalid STATUS." )


# User-defined shadow callback functions
def shadow_update_delta_callback(aws, shadow_document, Type):
    master_switch(aws, shadow_document, Type)

def shadow_get_accepted_callback(aws, shadow_document, Type):
    master_switch(aws, shadow_document, Type)

def shadow_get_rejected_callback():
    print( "ACTION for: shadow_get_rejected_callback")

def shadow_update_accepted_callback():
    print( "ACTION for: shadow_update_accepted_callback")

def shadow_update_rejected_callback():
    print( "ACTION for: shadow_update_rejected_callback")

def subscribe_user_callback(client, userdata, msg):
    print( "\nAWS Response Topic: " + str(msg.topic) )
    #print( "QoS: " + str(msg.qos) )
    print( "Payload: " + str(msg.payload) )

def publish_user_callback(aws):
    tempreading = 25.0 #uniform(20.0, 25.0) # can change this to a tuya source
    mtopic = aws.topic
    mdata  = json.dumps({"temperature": tempreading})
    srate  = 2

    return (mtopic, mdata, srate) 


def main():
    clientid  = 'iotcore-paho'
    thingname = 'iotcore-paho-sub'
    aws = AWSIoTConnect(clientid, thingname, CONCEPT_LAB, topic = "test/event", listener = True)
    
    aws.set_credentials(rootcafile, certfile, keyfile)

    aws.set_callback(CallbackIndex.UPDATE_DELTA.value, shadow_update_delta_callback)
    aws.set_callback(CallbackIndex.GET_ACCEPTED.value, shadow_get_accepted_callback)
    aws.set_callback(CallbackIndex.GET_REJECTED.value, shadow_get_rejected_callback)
    aws.set_callback(CallbackIndex.UPDATE_ACCEPTED.value, shadow_update_accepted_callback)
    aws.set_callback(CallbackIndex.UPDATE_REJECTED.value, shadow_update_rejected_callback)
    aws.set_callback(CallbackIndex.SUBSCRIBE_USER.value, subscribe_user_callback)
    aws.set_callback(CallbackIndex.PUBLISH_USER.value, publish_user_callback)
    
    aws.connect_attempt()

    print("Attempting shadow update")
    SHADOW_DOCUMENT  = """{"state" : {"desired" : {"switch1": "OFF"}, "reported" : {"switch" : "ON" }}}"""
    aws.set_shadow_document(SHADOW_DOCUMENT)
        
    time.sleep(5)
    print("New shadow docuemnt: " + str(aws.get_shadow_document()) )
   
    aws.telemetry()

if __name__ == '__main__':
    main()
    