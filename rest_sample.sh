#!/usr/bin/sh

# https://[username]:[apiKey]@api.[service.]softlayer.com/rest/v3/[serviceName]/[initializationParameter].[returnDatatype]

curl https://${SL_USERNAME}:${SL_API_KEY}@api.softlayer.com/rest/v3/SoftLayer_Account.xml
