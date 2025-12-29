#!/usr/bin/env python3
#
# written by Zyzonix
# published by xerberosDevelopments
#
# Copyright (c) 2025 xerberosDevelopments
#
# date created  | 28-12-2025 19:20:26
# 
# file          | grant-sogoAddressbook2ldapGroup.py
# project       | ldap2carddav
# version       | 1.0
#

LDAP_URL = ''
LDAP_BIND_DN = ''
LDAP_BIND_PASSWORD = ''
LDAP_FILTER = ""

# ADDRESSBOOK requires following keys: UID <string>, LDAP_BASE_DN <string>, OWNER <string>, SUBSCRIBE <boolean>
ADDRESSBOOKS = [
    {
        "UID": "",
        "LDAP_BASE_DN": 'ou=XX,dc=XX,dc=XX',
        "OWNER": "",
        "SUBSCRIBE": True
    }
]

DEBUG = False

# ------------------------- #
# end of custom config part #
# ------------------------- #

import ldap3
from datetime import datetime
import subprocess
import json
import time

# time for logging / console out
class ctime():
    def getTime():
        curTime = "" + str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        return curTime

# main log function
class logging():

    LOGGING_ENABLED = False

    def toFile(msg):
        if logging.LOGGING_ENABLED:
            try:
                logFile = open(logging.LOGFILEDIR + logging.LOGFILENAME, "a")
                logFile.write(msg + "\n")
                logFile.close()
            except:
                logging.LOGGING_ENABLED = False
                logging.writeError("Failed to open logfile directory, maybe a permission error?")

    def write(msg):
        message = str(ctime.getTime() + " INFO   | " + str(msg))
        if DEBUG: print(message)
        logging.toFile(message)

    def writeError(msg):
        message = str(ctime.getTime() + " ERROR  | " + msg)
        if DEBUG: print(message)
        logging.toFile(message)

    # log/print error stack trace
    def writeExecError(msg):
        message = str(msg)
        if DEBUG: print(message)
        logging.toFile(message)
    
    def writeSubprocessout(msg):
        for line in msg:
            line = str(line)
            line = line[:-3]
            line = line[3:]
            logging.write("SYS   | " + line)
    
    def writeNix(self):
        logging.toFile(self, "")
        if DEBUG: print()

def download_ldif(LDAP_BASE_DN):
    server = ldap3.Server(LDAP_URL)
    connection = ldap3.Connection(server, user=LDAP_BIND_DN,
        password=LDAP_BIND_PASSWORD, auto_bind=ldap3.AUTO_BIND_TLS_BEFORE_BIND)
    searchResult = connection.extend.standard.paged_search(LDAP_BASE_DN, LDAP_FILTER,
        attributes=ldap3.ALL_ATTRIBUTES, paged_size=10, generator=True)
    return searchResult


# init
if __name__ == '__main__':
    for addressbook in ADDRESSBOOKS:
        
        addressbookLdapDN = addressbook["LDAP_BASE_DN"]

        # get current permissions
        full_command_get = ["sudo", "-u", "sogo", "/usr/sbin/sogo-tool", "manage-acl", "get", addressbook["OWNER"], "Contacts/" + addressbook["UID"], "ALL"]
        logging.write("Executing: " + str(full_command_get))
        
        # Run the command and capture output
        result = subprocess.run(full_command_get, capture_output=True, text=True)

        # Check the result
        logging.write("Return code: " + str(result.returncode))  # 0 means success
        print(result.stderr)
        if not result.returncode == 0:
            print("Stdout:", result.stdout)
            print("Stderr:", result.stderr)
        
        adressbookRights = result.stderr

        for object in download_ldif(addressbookLdapDN):
            objectAttributes = object["attributes"]
            objectAttributeName = objectAttributes.get("sAMAccountName")
            objectAttributeMail = objectAttributes.get("mail")
            if objectAttributeMail:

                # skip already added and owner
                if  (objectAttributeName not in adressbookRights) and not (objectAttributeName == addressbook["OWNER"]):
                    logging.write("Granting permission to: " + objectAttributeName)
                    
                    # set permissions
                    rights = ["ObjectViewer"]
                    rights_json = json.dumps(rights)
                    full_command_add = ["sudo", "-u", "sogo", "/usr/sbin/sogo-tool", "manage-acl", "add", addressbook["OWNER"], "Contacts/" + addressbook["UID"], objectAttributeName, rights_json]                
                    
                    logging.write("Executing: " + str(full_command_add))
                    result = subprocess.run(full_command_add, capture_output=True, text=True)

                    # Check the result
                    logging.write("Return code: " + str(result.returncode))  # 0 means success
                    if not result.returncode == 0:
                        print("Stdout:", result.stdout)
                        print("Stderr:", result.stderr)

                # automatically subscribe if enabled, skip owner
                if addressbook["SUBSCRIBE"] and not (objectAttributeName == addressbook["OWNER"]):
                    time.sleep(0.1)
                    full_command_subscribe = ["sudo", "-u", "sogo", "/usr/sbin/sogo-tool", "manage-acl", "subscribe", addressbook["OWNER"], "Contacts/" + addressbook["UID"], objectAttributeName]
                    
                    logging.write("Executing: " + str(full_command_subscribe))
                    result = subprocess.run(full_command_subscribe, capture_output=True, text=True)

                    # Check the result
                    logging.write("Return code: " + str(result.returncode))  # 0 means success
                    if not result.returncode == 0:
                        print("Stdout:", result.stdout)
                        print("Stderr:", result.stderr)
        
        full_command_restart_services = ["sudo", "systemctl", "restart", "memcached", "sogo"]
        logging.write("Executing: " + str(full_command_restart_services))
        
        # Run the command and capture output
        result = subprocess.run(full_command_restart_services, capture_output=True, text=True)

        # Check the result
        logging.write("Return code: " + str(result.returncode))  # 0 means success


        # finally show permissions 
        full_command_get = ["sudo", "-u", "sogo", "/usr/sbin/sogo-tool", "manage-acl", "get", addressbook["OWNER"], "Contacts/" + addressbook["UID"], "ALL"]
        logging.write("Executing: " + str(full_command_get))
        
        # Run the command and capture output
        result = subprocess.run(full_command_get, capture_output=True, text=True)

        # Check the result
        logging.write("Return code: " + str(result.returncode))  # 0 means success
        print(result.stdout)
        print(result.stderr)
        if not result.returncode == 0:
            print("Stdout:", result.stdout)
            print("Stderr:", result.stderr)