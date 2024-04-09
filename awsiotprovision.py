import os
import json
import base64
import logging
import requests

logging.basicConfig(level=logging.INFO)


class AWSIoTProvision(object):

    def __init__(self, endpoint, thingname, dir_path = 'certs'):
        
        self.urlbase   = endpoint
        self.thingname = thingname

        certificate_directory = "./" + thingname + "-" + dir_path
        if not os.path.exists(certificate_directory):
            os.makedirs(certificate_directory)

        self.dirpath = certificate_directory

        self.rootca_file = os.path.join(self.dirpath, 'rootca.rca')
        self.privatekey_file = os.path.join(self.dirpath, self.thingname + '_private.key')
        self.certificate_file = os.path.join(self.dirpath, self.thingname + '_certitficate.pem')

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

    # def set_certdirectory(self, dir_path):
    #     self.dirpath = dir_path

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

    def register(self, thingname, macaddress):

        self.logger.debug("Thing Name: {0}".format(thingname))
        self.logger.debug("MAC Address  : {0}".format(macaddress))      
        b64string = self.__base64encode(thingname, macaddress)

        
        header = {'Authorization': f'Basic {b64string}'}
        self.logger.debug("Header Information: {0}".format(header))

        urlstring = self.urlbase + thingname + '/cert'
        self.logger.debug("POST URL: {0}".format(urlstring))

        response = requests.post(urlstring, headers = header)
        self.logger.debug(response.text)

        jsonstr  = json.loads(response.text)

        if "$metadata" in jsonstr: 
            if jsonstr["$metadata"]["httpStatusCode"] == 200:
                self.thingname = thingname
                self.__filewrite(response)
                return True
        else:
            return False

    def unregister(self, thingname, macaddress):
        success_tag = "Device is successfully removed"
        b64string = self.__base64encode(thingname, macaddress)

        header = {'Authorization': f'Basic {b64string}'}
        self.logger.debug("Header Information: {0}".format(header))

        urlstring = self.urlbase + thingname + '/remove'
        self.logger.debug("POST URL: {0}".format(urlstring))

        response = requests.delete(urlstring, headers = header)
        self.logger.debug(response.text)

        jsonstr  = json.loads(response.text)
        if 'messages' in jsonstr:
            if (jsonstr["messages"] == success_tag) :
                return True
        else:
            return False
