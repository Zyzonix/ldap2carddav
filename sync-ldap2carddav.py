#!/usr/bin/env python3
#
# written by Zyzonix
# published by xerberosDevelopments
#
# Copyright (c) 2025 xerberosDevelopments
#
# date created  | 27-12-2025 20:12:46
# 
# file          | sync-ldap2carddav.py
# project       | ldap2carddav
# version       | 2.0
#

LDAP_URL = ''
LDAP_BIND_DN = ''
LDAP_BIND_PASSWORD = ''
LDAP_FILTER = "(|(objectClass=person)(objectClass=contact))"

CARDDAV_USERNAME = ''
CARDDAV_PASSWORD = ''

ADDRESSBOOKS = [
    {
        "ADDRESSBOOK_URL" : "https://<yourmailsrv>/SOGo/dav/<user>/Contacts/<UID>/",
        "LDAP_BASE_DN" : "ou=XX,dc=XX,dc=XX",
        "NOT_MEMBER_OF" : ["CN=XX,OU=XX,OU=XX,DC=XX,DC=XX"]
    }
]

DEBUG = False

# ------------------------- #
# end of custom config part #
# ------------------------- #

import ldap3
import requests
import vobject
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from datetime import datetime

headers = {
    'Content-Type': 'text/vcard; charset=utf-8',
#    'If-None-Match': '*'  
}

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


def convert_ldif_to_vcards(object):
    objectAttributes = object['attributes']
    vCard = vobject.vCard()

    # will not be used
    objectGuid = objectAttributes.get('objectGUID').replace("{", "").replace("}", "")
    #vCard.add('guid').value = objectGuid
    #print(objectGuid)

    # last name
    objectSn = objectAttributes.get('sn')
    # first name
    objectGivenName = objectAttributes.get('givenName')
    # complete name
    objectDisplayName = objectAttributes.get('displayName')
    # description
    objectDescription = objectAttributes.get('description')
    # telephone number
    objectTelephoneNumber = objectAttributes.get('telephoneNumber')
    # mobile number
    objectMobile = objectAttributes.get('mobile')
    # email
    objectEmail = objectAttributes.get('mail')

    # use email as ID
    vCard.add('guid').value = objectEmail

    if objectGivenName and objectSn: vCard.add('n').value = vobject.vcard.Name(given=objectGivenName, family=objectSn)
    if objectDisplayName: 
        vCard.add('fn').value = objectDisplayName
    elif objectSn or objectGivenName:
        if objectSn and objectGivenName:
            vCard.add('fn').value = objectGivenName + objectSn
        else:
            vCard.add('fn').value = objectEmail
    else: 
        vCard.add('fn').value = objectEmail
    if objectTelephoneNumber: vCard.add('tel;TYPE=WORK').value = objectTelephoneNumber
    if objectMobile: vCard.add('tel;TYPE=cell').value = objectMobile
    if objectDescription: vCard.add('note').value = str(objectDescription[0])

    vCard.add('email;type=WORK').value = objectEmail

    return vCard


def upload_vcard(vCard, ADDRESSBOOK_URL):
    url = ADDRESSBOOK_URL + str(vCard.guid.value) + ".vcf"
    data = vCard.serialize().encode()
    result = requests.put(url, data=data, auth=(CARDDAV_USERNAME, CARDDAV_PASSWORD), headers=headers)
    result.raise_for_status()
    result.close()


def delete_old_entries(vCard, url):
    vCardURL = url + vCard
    result = requests.delete(vCardURL, auth=(CARDDAV_USERNAME, CARDDAV_PASSWORD), headers=headers)
    result.raise_for_status()
    result.close()


def discover_addressbook(url):
    result = requests.request(
        method='PROPFIND',
        url=url,
        headers=headers,
        auth=(CARDDAV_USERNAME, CARDDAV_PASSWORD)
    )
    return result.content.decode()

# init
if __name__ == '__main__':

    for addressbook in ADDRESSBOOKS:
        logging.write("Selected " + addressbook["ADDRESSBOOK_URL"])
        addressbookContent = discover_addressbook(addressbook["ADDRESSBOOK_URL"])
        baseTree = ET.fromstring(addressbookContent)
        
        # Namespaces (common in WebDAV/CardDAV)
        NS = {'d': 'DAV:'}

        vCardsInAddressbook = []

        # Iterate over each <response>
        for response in baseTree.findall('d:response', NS):
            href = response.find('d:href', NS).text
            href = unquote(href)  # Decode URL-encoded parts
            hrefSplit = href.rsplit("/", 1)
            vCardRaw = hrefSplit[1]
            vCardsInAddressbook.append(vCardRaw)

        logging.write("Found " + str(len(vCardsInAddressbook)) + " vCards in addressbook")

        count = 0
        vCardsUploaded = []

        for object in download_ldif(addressbook["LDAP_BASE_DN"]):
            
            objectAttributes = object["attributes"]
            objectMemberOf = objectAttributes.get("memberOf")
            objectAttributeMail = objectAttributes.get("mail")
            if objectAttributeMail:
                logging.write("Processing: " + objectAttributeMail)

                # if object is member of any group, check if group is not wanted
                if objectMemberOf and addressbook["NOT_MEMBER_OF"]: 
                    for group in addressbook["NOT_MEMBER_OF"]:
                        if not group in objectMemberOf:
                            vCard = convert_ldif_to_vcards(object)
                            upload_vcard(vCard, addressbook["ADDRESSBOOK_URL"])
                            count += 1
                            vCardsUploaded.append(vCard.guid.value + ".vcf") 

                # if object is member of nothing take it anyway
                else:
                    vCard = convert_ldif_to_vcards(object)
                    upload_vcard(vCard, addressbook["ADDRESSBOOK_URL"])
                    count += 1
                    vCardsUploaded.append(vCard.guid.value + ".vcf") 

        logging.write('Successfully uploaded {} vcards.'.format(count))

        # cards to be removed / not found in ldap
        vCardToDelete = []

        for vCard in vCardsInAddressbook:
            if vCard not in vCardsUploaded:
                vCardToDelete.append(vCard)
        
        if len(vCardToDelete) > 0:
            if not DEBUG: print("Found " + str(len(vCardToDelete)) + " vCards to delete")
            else: logging.write("Found " + str(len(vCardToDelete)) + " vCards to delete")
            for vCard in vCardToDelete:
                if not DEBUG: print(f"Deleting: {vCard}")
                else: logging.write(f"Deleting: {vCard}")
                delete_old_entries(vCard, url=addressbook["ADDRESSBOOK_URL"])
        else:
            logging.write("No vCards to delete found.")



