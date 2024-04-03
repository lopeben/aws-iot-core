import json

from random import uniform
from awsiotcore import AWSIoTConnect
from secrets import IOT_ENDPOINT


rootcafile = "./certificates/AmazonRootCA1.pem"
certfile   = "./certificates/32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-certificate.pem.crt"
keyfile    =  "./certificates/32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-private.pem.key"


def Welcome_Status_Change(obj, shadow_document, shadow_type):

    DESIRED_WELCOME_STATUS       = ""
    SHADOW_STATE_DOC_WELCOME_ON  = """{"state" : {"reported" : {"welcome" : "ON" }}}"""
    SHADOW_STATE_DOC_WELCOME_OFF = """{"state" : {"reported" : {"welcome" : "OFF"}}}"""

    # Parse Welcome Status from Shadow
    shadow_state = json.loads(shadow_document)

    if shadow_type == "DELTA":
        DESIRED_WELCOME_STATUS = shadow_state['state']['welcome']
    elif shadow_type == "GET_REQ":
        DESIRED_WELCOME_STATUS = shadow_state['state']['desired']['welcome']
    else:
        print( "---ERROR--- Unhandled Type.")

    print( "Desired LED Status: " + DESIRED_WELCOME_STATUS )

    # Resolve Shadow Delta in Cloud"  
    if DESIRED_WELCOME_STATUS == "ON":
        print( "Welcome ON. Reporting status to shadow..." )
        obj.mqttc.publish(obj.SHADOW_UPDATE_TOPIC, SHADOW_STATE_DOC_WELCOME_ON, qos=1)
    elif DESIRED_WELCOME_STATUS == "OFF":
        print( "Welcome OFF. Reporting status back to shadow..." )
        obj.mqttc.publish(obj.SHADOW_UPDATE_TOPIC, SHADOW_STATE_DOC_WELCOME_OFF, qos=1)
    else:
        print( "---ERROR--- Invalid STATUS." )


# User-defined shadow callback functions
def shadow_update_delta_callback(obj, shadow_document, Type):
    Welcome_Status_Change(obj, shadow_document, Type)

def shadow_get_accepted_callback(obj, shadow_document, Type):
    Welcome_Status_Change(obj, shadow_document, Type)

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

def publish_user_callback(obj):
    tempreading = 25.0 #uniform(20.0, 25.0) # can change this to a tuya source
    mtopic = obj.topic
    mdata  = json.dumps({"temperature": tempreading})
    srate  = 2

    return (mtopic, mdata, srate) 

shadowcallbacks = [shadow_update_delta_callback, 
                   shadow_get_accepted_callback, 
                   shadow_get_rejected_callback, 
                   shadow_update_accepted_callback, 
                   shadow_update_rejected_callback, 
                   subscribe_user_callback, 
                   publish_user_callback]

def main():
    clientid  = 'iotcore-paho'
    thingname = 'iotcore-paho-sub'
    aws = AWSIoTConnect(clientid, thingname, IOT_ENDPOINT, topic = "test/event", listener = True, usercallbacks=shadowcallbacks)
    
    aws.set_credentials(rootcafile, certfile, keyfile)
    aws.connect_attempt()
   
    aws.monitor()

if __name__ == '__main__':
    main()
    