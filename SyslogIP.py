# coding=utf-8
import requests
import getpass
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET


API_URL = "Place vCD URL Here" #Cloud API URL ending in /api/
EDGE_NAME = 'Place Edge Name Here' #Edge Gateway Name
SYSLOG_IP = 'Place Syslog IP Here' #IP of syslog server
USERNAME = 'Place Username Here' #Username@orgname E.g: email@domain.com@org
PASSWORD = 'Place Password Here' #Password

class SyslogServerSettings():
    xml_string = """
    <vmext:SyslogServerSettings xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmext="http://www.vmware.com/vcloud/extension/v1.5"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.vmware.com/vcloud/v1.5">
        <vmext:TenantSyslogServerSettings>
            <vmext:SyslogServerIp>{syslog_ip}</vmext:SyslogServerIp>
        </vmext:TenantSyslogServerSettings>
    </vmext:SyslogServerSettings>
    """
    def __init__(self, edge_url, auth_token, ip='0.0.0.0'):
        self.syslog_ip = ip
        self.edge_url = edge_url
        self.api_endpoint = '/action/configureSyslogServerSettings'
        self.headers = {'accept':'application/*+xml;version=5.6',
                   'x-vcloud-authorization':auth_token}

    def submit_changes(self):
        print('Submitting syslog IP changes: IP', self.syslog_ip)
        xml_out = self.xml_string.format(syslog_ip=self.syslog_ip)
        submit_url = self.edge_url + self.api_endpoint
        result = requests.post(submit_url, headers=self.headers, data=xml_out)
        print('API Endpoint: ', result.request.url)
        print('Status: {} {}'.format(result.status_code, result.reason))

class Cloud():

    def __init__(self, api_url, username=None, password=None):
        self.token = None
        self.headers = {'accept':'application/*+xml;version=5.7'}
        self._api_url = api_url
        self._username = username
        self._password = password

    def login(self):
        username = self._username or input('Username: ')
        password = self._password or getpass.getpass(prompt='Password: ')
        api_url = self._api_url+'sessions'
        print('Logging in to [%s]...' % api_url)
        r = requests.post(api_url, auth=HTTPBasicAuth(username, password),
                          headers=self.headers, proxies=None)
        print('Status:', r.status_code, r.reason)
        self.token = r.headers.get('x-vcloud-authorization')
        self.headers['x-vcloud-authorization'] = self.token
        print('Auth Token:', self.token)

    def query_edge_url(self, name):
        print('Querying edges for {}'.format(name))
        params = {'type': 'edgeGateway',
                   'format': 'references'}
        response = self.run_query(params)
        xml_tree = ET.fromstring(response.text)
        for item in xml_tree:
            if item.get('name') == name:
                return item.get('href')

    def run_query(self, query_parameters):
        query_url = self._api_url + 'query'
        response = requests.get(query_url, headers=self.headers,
                            params=query_parameters)
        return response

def main():
    vca = Cloud(API_URL, username=USERNAME, password=PASSWORD)
    vca.login()
    edge_url = vca.query_edge_url(EDGE_NAME)
    syslog = SyslogServerSettings(edge_url, vca.token, SYSLOG_IP)
    syslog.submit_changes()

if __name__ == '__main__':
    main()
