import time
import json

from random import uniform
from awsiotprovision import AWSIoTProvision
from awsiotcore import AWSIoTConnect, CallbackIndex
from secrets import IOT_ENDPOINT, CVM_BASE_URL




def master_switch(aws, shadow_document, shadow_type):

    DESIRED_STATUS          = ""
    SHADOW_STATE_REPORT_ON  = """{"state" : {"reported" : {"relay_state" : "true" }}}"""
    SHADOW_STATE_REPORT_OFF = """{"state" : {"reported" : {"relay_state" : "false" }}}"""

    # Parse Welcome Status from Shadow
    shadow_state = json.loads(shadow_document)
    # print(shadow_state)

    if shadow_type == "DELTA":
        DESIRED_STATUS = shadow_state['state']['relay_state']
        #print( "DELTA Desired Status: " + DESIRED_STATUS )
    elif shadow_type == "GET_REQ":
        DESIRED_STATUS = shadow_state['state']['desired']['relay_state']
        #print( "GETREQ Desired Status: " + DESIRED_STATUS )
    else:
        print( "---ERROR--- Unhandled Type.")

    

    # Resolve Shadow Delta in Cloud"  
    if DESIRED_STATUS == "true":
        print("User can add Switching ON controls here")



        #print( "Desired ON. Reporting status back to shadow..." )
        aws.mqttc.publish(aws.SHADOW_UPDATE_TOPIC, SHADOW_STATE_REPORT_ON, qos=1)
    elif DESIRED_STATUS == "false":
        print("User can add Switching OFF controls here")



        #print( "Desired OFF. Reporting status back to shadow..." )
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
    pass

def shadow_update_accepted_callback():
    #print( "ACTION for: shadow_update_accepted_callback")
    pass

def shadow_update_rejected_callback():
    print( "ACTION for: shadow_update_rejected_callback")
    pass

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

    serial = 'SPRPiSimu00002'
    macaddress = '1234567890AC'

    thing = AWSIoTProvision(CVM_BASE_URL, serial)

    if thing.has_certificates():
        print("Root CA: " + thing.get_rootca_file() )
        print("Certificate: " + thing.get_certiticate_file() )
        print("Private Key: " + thing.get_privatekey_file() )
    else:
        if thing.register(serial, macaddress):
            print("Registration success")
        else: 
            print("Registration failed")
            thing.unregister(serial, macaddress)
            return False

    clientid  = 'iotcore-paho'
    thingname = serial
    aws = AWSIoTConnect(thingname, IOT_ENDPOINT, clientid, topic = "test/event", listener = True)

    rootcafile = thing.get_rootca_file()
    certfile   = thing.get_certiticate_file()
    keyfile    = thing.get_privatekey_file()

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
    SHADOW_DOCUMENT  = '''{"state" : {"desired" : {"relay_state": "false"}, "reported" : {"relay_state" : "false" }}}'''
    aws.set_shadow_document(SHADOW_DOCUMENT)
        
    time.sleep(5)
    print("New shadow docuemnt: " + str(aws.get_shadow_document()) )
   
    aws.telemetry()

if __name__ == '__main__':
    main()
    