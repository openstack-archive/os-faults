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

from os_faults.api import error
from os_faults.api import power_management
from os_faults import utils

LOG = logging.getLogger(__name__)


class LibvirtDriver(power_management.PowerManagement):
    NAME = 'libvirt'
    DESCRIPTION = 'Libvirt power management driver'
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'connection_uri': {'type': 'string'},
        },
        'required': ['connection_uri'],
        'additionalProperties': False,
    }

    def __init__(self, params):
        self.connection_uri = params['connection_uri']
        self._cached_conn = None

    @property
    def conn(self):
        return self._get_connection()

    def _get_connection(self):
        if self._cached_conn is None:
            try:
                import libvirt
            except ImportError:
                raise error.OSFError('libvirt-python is required '
                                     'to use LibvirtDriver')
            self._cached_conn = libvirt.open(self.connection_uri)

        return self._cached_conn

    def _find_domain_by_mac_address(self, mac_address):
        for domain in self.conn.listAllDomains():
            if mac_address in domain.XMLDesc():
                return domain

        raise error.PowerManagementError(
            'Domain with MAC address %s not found!' % mac_address)

    def _poweroff(self, mac_address):
        LOG.debug('Power off domain with MAC address: %s', mac_address)
        domain = self._find_domain_by_mac_address(mac_address)
        domain.destroy()
        LOG.info('Domain powered off: %s', mac_address)

    def _poweron(self, mac_address):
        LOG.debug('Power on domain with MAC address: %s', mac_address)
        domain = self._find_domain_by_mac_address(mac_address)
        domain.create()
        LOG.info('Domain powered on: %s', mac_address)

    def _reset(self, mac_address):
        LOG.debug('Reset domain with MAC address: %s', mac_address)
        domain = self._find_domain_by_mac_address(mac_address)
        domain.reset()
        LOG.info('Domain reset: %s', mac_address)

    def _snapshot(self, mac_address, snapshot_name, suspend):
        LOG.debug('Create snapshot "%s" for domain with MAC address: %s',
                  snapshot_name, mac_address)
        domain = self._find_domain_by_mac_address(mac_address)
        if suspend:
            domain.suspend()
        domain.snapshotCreateXML(
            '<domainsnapshot><name>{}</name></domainsnapshot>'.format(
                snapshot_name))
        if suspend:
            domain.resume()
        LOG.debug('Created snapshot "%s" for domain with MAC address: %s',
                  snapshot_name, mac_address)

    def _revert(self, mac_address, snapshot_name, resume):
        LOG.debug('Revert snapshot "%s" for domain with MAC address: %s',
                  snapshot_name, mac_address)
        domain = self._find_domain_by_mac_address(mac_address)
        snapshot = domain.snapshotLookupByName(snapshot_name)
        if domain.isActive():
            domain.destroy()
        domain.revertToSnapshot(snapshot)
        if resume:
            domain.resume()
        LOG.debug('Reverted snapshot "%s" for domain with MAC address: %s',
                  snapshot_name, mac_address)

    def poweroff(self, mac_addresses_list):
        kwargs_list = [dict(mac_address=mac_address)
                       for mac_address in mac_addresses_list]
        utils.run(self._poweroff, kwargs_list)

    def poweron(self, mac_addresses_list):
        kwargs_list = [dict(mac_address=mac_address)
                       for mac_address in mac_addresses_list]
        utils.run(self._poweron, kwargs_list)

    def reset(self, mac_addresses_list):
        kwargs_list = [dict(mac_address=mac_address)
                       for mac_address in mac_addresses_list]
        utils.run(self._reset, kwargs_list)

    def snapshot(self, mac_addresses_list, snapshot_name, suspend=True):
        kwargs_list = [dict(mac_address=mac_address,
                            snapshot_name=snapshot_name,
                            suspend=suspend)
                       for mac_address in mac_addresses_list]
        utils.run(self._snapshot, kwargs_list)

    def revert(self, mac_addresses_list, snapshot_name, resume=True):
        kwargs_list = [dict(mac_address=mac_address,
                            snapshot_name=snapshot_name,
                            resume=resume)
                       for mac_address in mac_addresses_list]
        utils.run(self._revert, kwargs_list)
