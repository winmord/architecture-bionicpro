#!/bin/bash

ACCESS_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" | jq -r '.access_token')

curl -X POST "http://localhost:8080/admin/realms/reports-realm/components" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ldap-eu",
    "providerId": "ldap",
    "providerType": "org.keycloak.storage.UserStorageProvider",
    "parentId": "reports-realm",
    "config": {
      "enabled": ["true"],
      "priority": ["0"],
      "importEnabled": ["true"],
      "editMode": ["READ_ONLY"],
      "syncRegistrations": ["false"],
      "vendor": ["other"],
      "usernameLDAPAttribute": ["uid"],
      "rdnLDAPAttribute": ["uid"],
      "userObjectClasses": ["inetOrgPerson, organizationalPerson"],
      "connectionUrl": ["ldap://openldap:389"],
      "usersDn": ["ou=users,dc=bionicpro,dc=eu"],
      "authType": ["simple"],
      "bindDn": ["cn=admin,dc=bionicpro,dc=eu"],
      "bindCredential": ["admin123"]
    }
  }'