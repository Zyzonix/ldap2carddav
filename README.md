# Sync LDAP2CardDAV / Grant Addressbook access for SOGo
- Synchronise LDAP Contacts/Users to a CardDAV-Addressbook via HTTP(e.g. SOGo)
- Grant access to an addressbook in SOGo and auto subscribe

## Requirements / Setup
To use both scripts install on Debian:
```
apt install python3-ldap3 python3-vobject 
```
Go to ```/etc/sogo/``` and clone:
```
git clone https://github.com/Zyzonix/ldap2carddav
```
Move crontab to ```/etc/cron.d``` and make it executeable:
```
cp ldap2carddav /etc/cron.d/
chmod +x /etc/cron.d/ldap2carddav
```
Configure scripts, comment out the script that shouldn't run. Maybe adjust paths, if clone to somewhere else:

### Variables
```sync-ldap2carddav.py```
- ```LDAP_URL``` String: URL to LDAP server
- ```LDAP_BIND_DN``` String: Bind-User LDAP path
- ```LDAP_BIND_PASSWORD``` String: PW for LDAP user
- ```LDAP_BASE_DN``` String: Base LDAP path to search for users for addressbook
- ```LDAP_FILTER``` String: LDAP filter e.g. ```(|(objectClass=person)(objectClass=contact))```
- ```CARDDAV_USERNAME``` String: Username to Carddav
- ```CARDDAV_PASSWORD``` String: Password to Carddav
- ```CARDDAV_URL``` String: URL to Carddav-Server e.g. ```https://server/SOGo/dav/user/```
- ```NOT_MEMBER_OF``` List: of LDAP-Groups which members should be ignored when adding to addressbook
- ```DEBUG``` Boolean: en/disable debug output

The ```mail``` attribute muste be not null, otherwise the user will be ignored.

```grant-sogoAddressbook2ldapGroup.py```
- ```LDAP_URL``` String: URL to LDAP server
- ```LDAP_BIND_DN``` String: Bind-User LDAP path
- ```LDAP_BIND_PASSWORD``` String: PW for LDAP user
- ```LDAP_FILTER``` String: LDAP filter e.g. ```(objectClass=user)```
- ```DEBUG``` Boolean: en/disable debug output

- ```ADDRESSBOOKS``` List with Dicts as values
    - ```UID``` String: UID of the addressbook
    - ```LDAP_BASE_DN``` String: Base LDAP path to search for users for addressbook
    - ```OWNER``` String: username of addressbooks owner
    - ```SUBSCRIBE``` Boolean: subscribe automatically to all users

Example:
``` 
    {
        "UID": "6672-69528880-1-3D46204",
        "LDAP_BASE_DN": 'ou=Staff,dc=myad,dc=com',
        "OWNER": "user1",
        "SUBSCRIBE": True
    }
```


## Versioning
```sync-ldap2carddav.py```
- ```1.0``` Initial version

```grant-sogoAddressbook2ldapGroup.py```
- ```1.0``` Iniitial version


## Features to add
- Export multiple addressbooks from different sources