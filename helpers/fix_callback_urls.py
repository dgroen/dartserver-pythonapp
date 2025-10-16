#!/usr/bin/env python3
"""
Fix WSO2 callback URLs to allow both login and logout redirects
"""
import xml.etree.ElementTree as ET

import requests

requests.packages.urllib3.disable_warnings()

WSO2_IS_URL = "https://localhost:9443"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
APP_NAME = "DartsApp"

CALLBACK_PATTERN = "regexp=https://letsplaydarts\\.eu(/callback|/)"

session = requests.Session()
session.auth = (ADMIN_USER, ADMIN_PASS)
session.verify = False

soap_url = f"{WSO2_IS_URL}/services/IdentityApplicationManagementService"

get_app_soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://org.apache.axis2/xsd">
   <soapenv:Header/>
   <soapenv:Body>
      <xsd:getApplication>
         <xsd:applicationName>{APP_NAME}</xsd:applicationName>
      </xsd:getApplication>
   </soapenv:Body>
</soapenv:Envelope>"""

print(f"🔍 Getting application: {APP_NAME}")
response = session.post(
    soap_url,
    data=get_app_soap,
    headers={"Content-Type": "text/xml", "SOAPAction": "urn:getApplication"},
    timeout=10,
)

if response.status_code != 200:
    print(f"❌ Failed to get application: {response.status_code}")
    print(response.text)
    exit(1)

root = ET.fromstring(response.content)
ns = {
    "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
    "ns": "http://org.apache.axis2/xsd",
    "ax2324": "http://model.common.application.identity.carbon.wso2.org/xsd",
}

oauth_config = root.find(
    ".//ax2324:inboundAuthenticationConfig/ax2324:inboundAuthenticationRequestConfigs", ns
)

if oauth_config is None:
    print("❌ No OAuth configuration found")
    exit(1)

for config in oauth_config.findall("ax2324:inboundAuthenticationRequestConfigs", ns):
    auth_type = config.find("ax2324:inboundAuthType", ns)
    if auth_type is not None and auth_type.text == "oauth2":
        callback_elem = config.find(
            'ax2324:properties/ax2324:properties[ax2324:name="callbackUrl"]/ax2324:value', ns
        )
        if callback_elem is not None:
            current_callback = callback_elem.text
            print(f"📋 Current callback: {current_callback}")
            callback_elem.text = CALLBACK_PATTERN
            print(f"✏️  New callback: {CALLBACK_PATTERN}")
        break

app_xml = ET.tostring(root.find(".//ns:return", ns), encoding="unicode")

update_soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://org.apache.axis2/xsd">
   <soapenv:Header/>
   <soapenv:Body>
      <xsd:updateApplication>
         <xsd:serviceProvider>
            {app_xml}
         </xsd:serviceProvider>
      </xsd:updateApplication>
   </soapenv:Body>
</soapenv:Envelope>"""

print("📤 Updating application...")
update_response = session.post(
    soap_url,
    data=update_soap,
    headers={"Content-Type": "text/xml", "SOAPAction": "urn:updateApplication"},
    timeout=10,
)

if update_response.status_code == 200:
    print("✅ Successfully updated callback URLs!")
    print("   Allows both:")
    print("   - https://letsplaydarts.eu/callback (login)")
    print("   - https://letsplaydarts.eu/ (logout)")
else:
    print(f"❌ Failed to update: {update_response.status_code}")
    print(update_response.text)
