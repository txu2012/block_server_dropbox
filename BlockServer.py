#!/usr/bin/env python

import sys
import os
import logging

sys.path.append('gen-py')

from blockServer import BlockServerService
from blockServer.ttypes import *
from shared.ttypes import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.server import TServer
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

class BlockServerHandler():

    def __init__(self, configpath):
        # Initialize using config file, intitalize state etc
        self.config_path = configpath
        self.port = self.readServerPort()
        self.hashBlocks = {}
        #pass

    def storeBlock(self, hashBlock):
        # Store hash block, called by client during upload
        self.hashBlocks[hashBlock.hash] = hashBlock
        r = response()
        r.message = responseType.OK

        return r
        #pass

    def getBlock(self, hash):
        # Retrieve block using hash, called by client during download
        print "Searching in local data structure"
        if hash in self.hashBlocks:
            hb = self.hashBlocks[hash]
            return hb
        else:
            print "Hash block not found, returning a null block with ERROR as status"
            hb = hashBlock()
            hb.status = "ERROR"
            return hb
        #pass

    def deleteBlock(self, hash):
        # Delete the particular hash : block pair
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
                if 'blockserver' in line:
                    # Important to make port as an integer
                    return int(line.split()[1].lstrip().rstrip())

        # Exit if you did not get blockserver information
        print "ERROR: blockserver information not found in config file"
        exit(1)
        #pass
    def hasBlock(self, file):
        r = uploadResponse()
        missing_blocks = []
        for hashes in file.hashList:
            if hashes in self.hashBlocks:
                r.status = uploadResponseType.OK

            else:
                r.status = uploadResponseType.MISSING_BLOCKS
                missing_blocks.append(hashes)
        
        if len(missing_blocks) > 0:
            r.hashList = missing_blocks
            r.status = uploadResponseType.MISSING_BLOCKS
            
        return r
    
    def readServerPort(self):
        # In this function read the configuration file and get the port number for the server
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

        # Add your functions here

# Add additional classes and functions here if needed


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Invocation <executable> <config_file>"
        exit(-1)

    config_path = sys.argv[1]

    print "Initializing block server"
    handler = BlockServerHandler(config_path)
    # Retrieve the port number from the config file so that you could strt the server
    port = handler.readServerPort()
    # Define parameters for thrift server
    processor = BlockServerService.Processor(handler)
    transport = TSocket.TServerSocket(port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    # Create a server object
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    print "Starting server on port : ", port
    logging.basicConfig(level=logging.DEBUG)

    try:
        server.serve()
    except (Exception, KeyboardInterrupt) as e:
        print "\nExecption / Keyboard interrupt occured: ", e
        exit(0)
