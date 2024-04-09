import time
import json
import datetime
import RPi.GPIO as GPIO

from random import uniform
from awsiotprovision import AWSIoTProvision
from awsiotcore import AWSIoTConnect, CallbackIndex
from secrets import IOT_ENDPOINT, CVM_BASE_URL



RUN  = YELLOW = GPIO17 = 17 
HLT  = GREEN  = GPIO27 = 27 
FWD  = BLUE   = GPIO22 = 22 
REV  = VIOLET = GPIO23 = 23 

## ROLL_UP, ROLL_DOWN, HALT, RUN

ESCALATOR_STATE_XXX = "UNKNOWN"
ESCALATOR_STATE_RUN = "RUNNING"
ESCALATOR_STATE_STP = "STOPPED"

ESCALATOR_DIRECTION_XX = "UNKNOWN"
ESCALATOR_DIRECTION_UP = "UP"
ESCALATOR_DIRECTION_DN = "DOWN"

previous_state     = ''
previous_direction = ''
count = 0


def initialize_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(GPIO17, GPIO.IN, GPIO.PUD_DOWN) 
    GPIO.setup(GPIO27, GPIO.IN, GPIO.PUD_DOWN) 
    GPIO.setup(GPIO22, GPIO.IN, GPIO.PUD_DOWN) 
    GPIO.setup(GPIO23, GPIO.IN, GPIO.PUD_DOWN) 

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



def escalalator_monitoring_callback(aws):

    global previous_state
    global previous_direction
    global count

    id = 0
    
    gpio0 = GPIO.input(RUN)     ## Running
    gpio1 = GPIO.input(HLT)     ## Halted
    #print("State0: {0}".format(gpio0))
    #print("State1: {0}".format(gpio1))
    if gpio0 and not gpio1:
        current_state = ESCALATOR_STATE_RUN
    elif not gpio0 and gpio1:
        current_state = ESCALATOR_STATE_STP
    else:
        current_state = ESCALATOR_STATE_XXX
    

    gpio2 = GPIO.input(FWD)  ## Going up
    gpio3 = GPIO.input(REV)  ## Going down
    #print("State2: {0}".format(gpio2))
    #print("State3: {0}".format(gpio3))
    if gpio2 and not gpio3:
        current_direction = ESCALATOR_DIRECTION_UP
    elif not gpio2 and gpio3:
        current_direction = ESCALATOR_DIRECTION_DN
    else:
        current_direction = ESCALATOR_DIRECTION_XX
    
    
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    ## Check if running state has changed
    if current_state == previous_state:
        gate1 = False
    else:
        gate1 = True
        previous_state = current_state

    ## Check if direction has changed
    if current_direction == previous_direction:
        gate2 = False
    else:
        gate2 = True
        previous_direction = current_direction

    gate = gate1 or gate2
    count = count + 1
    if count > 300: #300 seconds 
        gate = True
        count = 0        

    escalator_status = { "device_time"  : "{0}".format(timestamp),
                        "escalator_id" : "{0}".format(id), 
                        "state" : "{0}".format(current_state),
                        "direction" : "{0}".format(current_direction)
                        }

    #print(escalator_status)    
    
    sampling_rate  = 1 # second
    mtopic = aws.topic
    mdata  = json.dumps(escalator_status)
    return (mtopic, mdata, sampling_rate, gate) 


def main():

    initialize_gpio()

    thingname = 'EscalatorSim02'
    macaddress = '1234567890AC'
    pubsubtopic = 'cic/otis/escalator/01'

    thing = AWSIoTProvision(CVM_BASE_URL, thingname)

    if thing.has_certificates():
        print("Root CA: " + thing.get_rootca_file() )
        print("Certificate: " + thing.get_certiticate_file() )
        print("Private Key: " + thing.get_privatekey_file() )
    else:
        if thing.register(thingname, macaddress):
            print("Registration success")
        else: 
            print("Registration failed")
            thing.unregister(thingname, macaddress)
            return False

    clientid  = 'iotcore-paho'
    thingname = thingname
    aws = AWSIoTConnect(thingname, IOT_ENDPOINT, clientid, topic = pubsubtopic, listener = True)

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
    aws.set_callback(CallbackIndex.PUBLISH_USER.value, escalalator_monitoring_callback)
    
    aws.connect_attempt()

    print("Attempting shadow update")
    SHADOW_DOCUMENT  = '''{"state" : {"desired" : {"relay_state": "false"}, "reported" : {"relay_state" : "false" }}}'''
    aws.set_shadow_document(SHADOW_DOCUMENT)
        
    time.sleep(5)
    print("New shadow docuemnt: " + str(aws.get_shadow_document()) )
   
    aws.telemetry()

if __name__ == '__main__':
    main()
    