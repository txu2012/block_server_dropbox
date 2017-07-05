#!/usr/bin/env python

import sys
import os
import logging

sys.path.append('gen-py')

# Thrift specific imports
from thrift import Thrift
from thrift.transport import TSocket
from thrift.server import TServer
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

# Protocol specific imports
from metadataServer import MetadataServerService
from shared.ttypes import *
from blockServer import *
from BlockServer import *

class MetadataServerHandler():

    def __init__(self, config_path, my_id):
        # Initialize block
        self.hashListBlocks = {}
        self.configpath = config_path

    def getFile(self, filename):
        # Function to handle download request from file
        # pass
        newFile = file()
        newFile.hashList = self.hashListBlocks[filename]
        newFile.filename = filename
        return newFile
        
    def storeFile(self, file):
        # Function to handle upload request
        self.hashListBlocks[file.filename] = file.hashList    
        checker = sock.hasBlock(file)
        
        return checker

    def deleteFile(self, filename):
        # Function to handle download request from file
        r = response()
        if self.hashListBlocks[filename.filename] == None:
            r.message = responseType.ERROR
        else:
            self.hashListBlocks[filename.filename] = None
            r.message = responseType.OK
        
        return r
        
    def readServerPort(self):
        # Get the server port from the config file.
        # id field will determine which metadata server it is 1, 2 or n
        # Your details will be then either metadata1, metadata2 ... metadatan
        # return the port
        #pass
        print "Checking config path"
        if not os.path.exists(config_path):
            print "ERROR: Config path is invalid"
            exit(1)
        if not os.path.isfile(config_path):
            print "ERROR: Config path is not a file"
            exit(1)
            
        print "Reading file"
        with open(config_path, 'r') as conffile:
            lines = conffile.readlines()
            for line in lines:
                if 'metadata1' in line:
                    # Important to make port as an integer
                    return int(line.split()[1].lstrip().rstrip())
    
        # Exit if you did not get blockserver information
        print "ERROR: metadata information not found in config file"
        exit(1)

    # Add other member functions if needed
    def getBlockServerPort(self,config_path):
    # This function reads config file and gets the port for block server

        print "Checking validity of the config path"
        if not os.path.exists(config_path):
            print "ERROR: Config path is invalid"
            exit(1)
        if not os.path.isfile(config_path):
            print "ERROR: Config path is not a file"
            exit(1)
    
        print "Reading config file"
        with open(config_path, 'r') as conffile:
            lines = conffile.readlines()
            for line in lines:
                if 'block' in line:
                    # Important to make port as an integer
                    return int(line.split()[1].lstrip().rstrip())
    
        # Exit if you did not get blockserver information
        print "ERROR: blockserver information not found in config file"
        exit(1)


    def getBlockServerSocket(self,port):
        # This function creates a socket to block server and returns it
    
        # Make socket
        transport = TSocket.TSocket('localhost', port)
        # Buffering is critical. Raw sockets are very slow
        transport = TTransport.TBufferedTransport(transport)
        # Wrap in a protocol
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        # Create a client to use the protocol encoder
        client = BlockServerService.Client(protocol)
    
        # Connect!
        print "Connecting to block server on port", port
        try:
            transport.open()
        except Exception as e:
            print "ERROR: Exception while connecting to block server, check if server is running on port", port
            print e
            exit(1)
    
        return client

    def checkHash():
        return self.hashListBlocks
# Add additional classes and functions here if needed


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "Invocation <executable> <config_file> <id>"
        exit(-1)

    config_path = sys.argv[1]
    my_id = sys.argv[2]
    

    print "Initializing metadata server"
    handler = MetadataServerHandler(config_path, my_id)
    port = handler.readServerPort()
    # Define parameters for thrift server
    processor = MetadataServerService.Processor(handler)
    transport = TSocket.TServerSocket(port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    # Create a server object
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    print "Starting server on port : ", port

    servPort = handler.getBlockServerPort(config_path)
    sock = handler.getBlockServerSocket(servPort)
    logging.basicConfig(level=logging.DEBUG)
    try:
        server.serve()
    except (Exception, KeyboardInterrupt) as e:
        print "\nExecption / Keyboard interrupt occured: ", e
        exit(0)
