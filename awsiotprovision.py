import os
import json
import base64
import logging
import requests

logging.basicConfig(level=logging.INFO)


class AWSIoTProvision(object):

    def __init__(self, endpoint, serial, dir_path = '.\certs'):
        
        self.dirpath = dir_path
        self.urlbase   = endpoint

        self.serial = serial

        self.rootca_file = ''
        self.privatekey_file = ''
        self.certificate_file = ''

        if not os.path.exists(self.dirpath):
            os.makedirs(self.dirpath)

        self.rootca_file = os.path.join(dir_path, 'rootca.rca')
        #self.privatekey_file = dir_path + self.serial + '_private.key'
        self.privatekey_file = os.path.join(dir_path, self.serial + '_private.key')
        # self.certificate_file = dir_path + self.serial + '_certitficate.pem'
        self.certificate_file = os.path.join(dir_path, self.serial + '_certitficate.pem')

        self.logger    = logging.getLogger(repr(self))
        self.logger.debug("CVM Endpoint URL: {0}".format(self.urlbase))

    def __base64encode(self, sn, mac):
        
        snmac_string = sn + ":" + mac
        snmac_bytes = snmac_string.encode("UTF-8")
        base64_bytes = base64.b64encode(snmac_bytes)
        b64string = base64_bytes.decode('UTF-8')
        self.logger.debug("Base64 String: {0}".format(b64string))

        return b64string

    def __filewrite(self, response):

        secret = json.loads(response.text)

        with open(self.certificate_file, 'w') as f:
            f.write(secret['certificatePem'])

        with open(self.privatekey_file, 'w') as f:
            f.write(secret['keyPair']['PrivateKey'])

        with open(self.rootca_file, 'w') as f:
            f.write(secret['RootCA'])

    def set_certdirectory(self, dir_path):
        
        self.dirpath = dir_path

    def get_rootca_file(self):

        return self.rootca_file

    def get_certiticate_file(self):
        
        return self.certificate_file

    def get_privatekey_file(self):
        
        return self.privatekey_file
    
    def has_certificates(self):

        if ( os.path.isfile(self.rootca_file) and os.path.isfile(self.certificate_file) and os.path.isfile(self.privatekey_file) ):
            self.logger.debug("All certificates exist")
            return True
        else:
            self.logger.debug("At least one certificate missing")
            return False

    def register(self, serial, macaddress):

        self.logger.debug("Serial Number: {0}".format(serial))
        self.logger.debug("MAC Address  : {0}".format(macaddress))      
        b64string = self.__base64encode(serial, macaddress)

        
        header = {'Authorization': f'Basic {b64string}'}
        self.logger.debug("Header Information: {0}".format(header))

        urlstring = self.urlbase + serial + '/cert'
        self.logger.debug("POST URL: {0}".format(urlstring))

        response = requests.post(urlstring, headers = header)
        self.logger.debug(response.text)

        jsonstr  = json.loads(response.text)

        if "$metadata" in jsonstr: 
            if jsonstr["$metadata"]["httpStatusCode"] == 200:
                self.serial = serial
                self.__filewrite(response)
                return True
        else:
            return False

    def unregister(self, serial, macaddress):
        success_tag = "Device is successfully removed"
        b64string = self.__base64encode(serial, macaddress)

        header = {'Authorization': f'Basic {b64string}'}
        self.logger.debug("Header Information: {0}".format(header))

        urlstring = self.urlbase + serial + '/remove'
        self.logger.debug("POST URL: {0}".format(urlstring))

        response = requests.delete(urlstring, headers = header)
        self.logger.debug(response.text)

        jsonstr  = json.loads(response.text)
        if 'messages' in jsonstr:
            if (jsonstr["messages"] == success_tag) :
                return True
        else:
            return False

    # def unregister(self, *args):
    #     serialnumber = args[0]
    #     macaddress = args[1]
        
    #     success_tag = "Device is successfully removed"
    #     b64string = self.__base64encode(serialnumber, macaddress)

    #     header = {'Authorization': f'Basic {b64string}'}
    #     self.logger.debug("Header Information: {0}".format(header))

    #     response = requests.delete(self.urlstring, headers = header)
    #     jsonstr  = json.loads(response.text)

    #     if (jsonstr["messages"] == success_tag) :
    #         return True
    #     else:
    #         return False


    
    

# base = "https://vquqs6aaik.execute-api.ap-southeast-1.amazonaws.com/dev/plugs/"
# serial = 'SPRPiSimulator'
# path = '/cert'
# urlstring = base + serial + path 
# print(urlstring)

# mac = '1234567890AB'
# snmac_string = serial + ":" + mac
# snmac_bytes = snmac_string.encode("UTF-8")
# base64_bytes = base64.b64encode(snmac_bytes)
# print (base64_bytes.decode('UTF-8'))

# auth = "Authorization"
# type = "Basic"
# b64string = base64_bytes.decode('UTF-8')
#header = auth + ": " + type + " " + b64string
##header = { auth + ": " + type + " " + b64string }

#header = 'Authorization: Basic ' + b64string
# header = {'Authorization': f'Basic {b64string}'}
# print(header)

# response = requests.post(urlstring, headers=header)

# Print the response
# print(response.text)

# secret = json.loads(response.text)

# # Parse the JSON response and write the certificatePem, PrivateKey, and RootCA to separate files
# CERTIFICATE_FILE = 'certificate.pem'
# PRIVATEKEY_FILE  = 'private.key'
# ROOTCA_FILE      = 'rootca.rca'

# dir_path = './certs'

# # Check if the directory exists
# if not os.path.exists(dir_path):
#     # If the directory doesn't exist, create it
#     os.makedirs(dir_path)

# with open(os.path.join(dir_path, CERTIFICATE_FILE), 'w') as f:
#     f.write(secret['certificatePem'])

# with open(os.path.join(dir_path, PRIVATEKEY_FILE), 'w') as f:
#     f.write(secret['keyPair']['PrivateKey'])

# with open(os.path.join(dir_path, ROOTCA_FILE), 'w') as f:
#     f.write(secret['RootCA'])

# Print a success message
# print("The certificatePem, PrivateKey, and RootCA have been successfully saved to certificate.pem, private.key, and root.ca files respectively.")



##curl --location --request DELETE 'https://vquqs6aaik.execute-api.ap-southeast-1.amazonaws.com/dev/plugs/SPRPiSimulator/remove' --header 'Authorization: Basic U1BSUGlTaW11bGF0b3I6MTIzNDU2Nzg5MEFC'
