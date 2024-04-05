import time

from awsiotprovision import AWSIoTProvision
from secrets import CVM_BASE_URL

def main():

    serial = 'SPRPiSimulator'
    macaddress ='1234567890AB'

    aws = AWSIoTProvision(CVM_BASE_URL, serial )

    if aws.has_certificates():
        print("Root CA: " + aws.get_rootca_file() )
        print("Certificate: " + aws.get_certiticate_file() )
        print("Private Key: " + aws.get_privatekey_file() )
    else:
        if aws.register(serial, macaddress):
            print("Registration success")
        else: 
            print("Registration failed")

    time.sleep(10)

    if aws.unregister(serial, macaddress):
        print("Unregistration success")
    else:
        print("Unregistration failed")


if __name__ == "__main__":
    main()