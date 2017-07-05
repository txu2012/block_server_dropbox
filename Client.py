#!/usr/bin/env python

import sys
import os
import hashlib
import time

sys.path.append('gen-py')

# Thrift specific imports
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from shared.ttypes import *
from metadataServer.ttypes import *
from blockServer.ttypes import *

from blockServer import *
from shared import *
from metadataServer import *

currentBlocks = {}

# Add classes / functions as required here
block_size = 4194304   

def getBlockServerPort(config_path):
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


def getBlockServerSocket(port):
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

def getMetadataPort(config_path):
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
    
def getMetadataServerSocket(port):
    # This function creates a socket to metadata server and returns it

    # Make socket
    transportMeta = TSocket.TSocket('localhost', port)
    # Buffering is critical. Raw sockets are very slow
    transportMeta = TTransport.TBufferedTransport(transportMeta)
    # Wrap in a protocol
    protocolMeta = TBinaryProtocol.TBinaryProtocol(transportMeta)
    # Create a client to use the protocol encoder
    clientMeta = MetadataServerService.Client(protocolMeta)

    # Connect!
    print "Connecting to metadata server on port", port
    try:
        transportMeta.open()
    except Exception as e:
        print "ERROR: Exception while connecting to metadata server, check if server is running on port", port
        print e
        exit(1)

    return clientMeta
    
def getLocalFiles(base_dir):
    print "Getting Local Files in base directory"
    files = []
    for getFile in os.listdir(base_dir):
        if os.path.isfile(os.path.join(base_dir,getFile)):
            files.append(getFile)
    
    for currentFile in files:
        path = os.path.join(base_dir,currentFile)
        
        getFile = open(path,'rb')
    
        blockNumber = os.path.getsize(path)/block_size
        if os.path.getsize(path) % block_size  != 0:
            blockNumber += 1
        
        fileSize = os.path.getsize(path)
        for blocks in range(blockNumber):
            if fileSize > block_size: #
                block = getFile.read(block_size)
                m.update(block)
                hashString = m.hexdigest()
                currentBlocks[hashString] = getFile.read(block_size)
                fileSize = fileSize - block_size
            else:
                block = getFile.read(block_size)
                m.update(block)
                hashString = m.hexdigest()
                currentBlocks[hashString] = getFile.read()
        
# Download method        
def downloadFile(pathName, downloadFile):
    print "download file"
    try:
        hashDownload = []
        hashFiles = []
        
        downloadHashes = metaSock.getFile(downloadFile)
        for hashes in downloadHashes.hashList:
            if hashes in currentBlocks:
                hashFiles.append(currentBlocks[hashes])
            else:
                #hashDownload.append(hashes)
                downloaded = blockSock.getBlock(hashes)
                hashFiles.append(downloaded.block)
                currentBlocks[hashes] = downloaded.block
                
        if len(downloadHashes.hashList) == 1:
            downloaded = blockSock.getBlock(downloadHashes.hashList[0])
            createFile = open(pathName, 'wb')
            newFileBytes = bytearray(downloaded.block)
            createFile.write(newFileBytes)
        else:     
            createFile = open(pathName, 'w')
            newFileBytes = bytearray(hashFiles)
            createFile.write(newFileBytes)
 
        print 'OK'
    
    except Thrift.TException, tx:
        print 'ERROR'
    
    
def uploadFile(name,fileN):
    print "upload file"
    try:
        getHashList = []
        getHashBlocks = {}
        getFile = open(name,'rb')
        print name
                
        blockNumber = os.path.getsize(name)/block_size
        if os.path.getsize(name) % block_size  != 0:
            blockNumber += 1
                        
        fileSize = os.path.getsize(name)
            # Generate hash list and blocks of the file
        for blocks in range(blockNumber):
            if fileSize > block_size:
                block = getFile.read(block_size)
                m.update(block)
                hashString = m.hexdigest()
                print hashString
                getHashBlocks[hashString] = block
                getHashList.append(hashString)
                fileSize = fileSize - block_size
            else:
                block = getFile.read()
                m.update(block)
                hashString = m.hexdigest()
                print hashString
                getHashBlocks[hashString] = block
                getHashList.append(hashString)
            
        missedBlocks = {}
            # Check list in metadata server
        newFile = file()
        newFile.filename = fileN
        newFile.hashList = list(getHashList)
            
            # Check if any blocks are missing and store hashList to metadata server
        response = metaSock.storeFile(newFile)
                
        if response.status != uploadResponseType.OK: 
            for missBlocks in response.hashList:
                uploadBlock = hashBlock()
                uploadBlock.hash = missBlocks
                uploadBlock.block = getHashBlocks[missBlocks]
                blockResponse = blockSock.storeBlock(uploadBlock)
                
        print 'OK'
    
    except Thrift.TException, tx:
        print 'ERROR'

def deleteFile(fileN):
    try:
        print "delete file 
        delFile = file()
        delFile.filename = fileN
        r = metaSock.deleteFile(delFile)
        print r.message
        print 'OK'
    
    except Thrift.TException, tx:
        print 'ERROR'


if __name__ == "__main__":

    if len(sys.argv) < 5:
        print "Invocation : <executable> <config_file> <base_dir> <command> <filename>"
        exit(-1)

    config_path = sys.argv[1]
    print "Starting client"
    servPort = getBlockServerPort(config_path)
    metaPort = getMetadataPort(config_path)
    blockSock = getBlockServerSocket(servPort)
    metaSock = getMetadataServerSocket(metaPort)
    
    m = hashlib.sha256()
    baseFolder = sys.argv[2]
    fileName = sys.argv[4]
    filePath = baseFolder + '/' +  fileName
    getLocalFiles(sys.argv[2])
    
    if sys.argv[3] == 'download':
        downloading = downloadFile(filePath, fileName)
      
    if sys.argv[3] == 'upload':
        uploading = uploadFile(filePath, fileName)
        
    if sys.argv[3] == 'delete':
        deleting = deleteFile(fileName)
