from awsiotcore import AWSIoTConnect

rootcafile = "./certificates/AmazonRootCA1.pem"
certfile = "./certificates/32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-certificate.pem.crt"
keyfile =  "./certificates/32e466d32d1620eccc4580dde00f25fb8285d06f31be894f60a223c69ebd4122-private.pem.key"

    
def atmessage(client, userdata, msg):
    print("Userdata: {0}, Topic: {1}, Payload: {2}".format(userdata, msg.topic, msg.payload))

    
def main():
    aws = AWSIoTConnect(listener = True, topic = "test/event")
      
    aws.set_on_message_callback(atmessage)
    
    aws.set_credentials(rootcafile, certfile, keyfile)
    aws.connect_attempt()
   
    aws.test_start()


if __name__ == '__main__':
    main()
    