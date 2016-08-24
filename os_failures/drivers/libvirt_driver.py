# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from xml.dom import minidom

import libvirt

from os_failures.api import power_management


class LibvirtDriver(power_management.PowerManagement):
    def __init__(self, params):
        self.connection_uri = params['connection_uri']
        self._cached_conn = None

    @property
    def conn(self):
        return self._get_connection()

    def _get_connection(self):
        if self._cached_conn is None:
            self._cached_conn = libvirt.open(self.connection_uri)

        return self._cached_conn

    def _find_domain_by_mac_address(self, mac_address):
        for domain in self.conn.listAllDomains():
            xml = minidom.parseString(domain.XMLDesc())
            mac_list = xml.getElementsByTagName('mac')
            for mac in mac_list:
                if mac_address == mac.getAttribute('address'):
                    return domain

        # TODO(ylobankov): Use more specific exception here in the future
        raise Exception('Node with MAC address %s not found!' % mac_address)

    def poweroff(self, mac_addresses_list):
        for mac_address in mac_addresses_list:
            logging.info('Power off domain with MAC address: %s', mac_address)
            domain = self._find_domain_by_mac_address(mac_address)
            domain.destroy()
            logging.info('Domain (%s) was powered off' % mac_address)

    def poweron(self, mac_addresses_list):
        for mac_address in mac_addresses_list:
            logging.info('Power on domain with MAC address: %s', mac_address)
            domain = self._find_domain_by_mac_address(mac_address)
            domain.create()
            logging.info('Domain (%s) was powered on' % mac_address)

    def reset(self, mac_addresses_list):
        for mac_address in mac_addresses_list:
            logging.info('Reset domain with MAC address: %s', mac_address)
            domain = self._find_domain_by_mac_address(mac_address)
            domain.reset()
            logging.info('Domain (%s) was reset' % mac_address)
