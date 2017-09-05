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

from oslo_utils import importutils

from os_faults.api import error
from os_faults.api import power_management

LOG = logging.getLogger(__name__)


class LibvirtDriver(power_management.PowerDriver):
    """Libvirt driver.

    **Example configuration:**

    .. code-block:: yaml

        power_managements:
        - driver: libvirt
          args:
            connection_uri: qemu+unix:///system

    parameters:

    - **connection_uri** - libvirt uri

    """

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
            libvirt_module = importutils.try_import('libvirt')
            if not libvirt_module:
                raise error.OSFError('libvirt-python is required '
                                     'to use LibvirtDriver')
            self._cached_conn = libvirt_module.open(self.connection_uri)

        return self._cached_conn

    def _find_domain_by_host(self, host):
        for domain in self.conn.listAllDomains():
            if host.libvirt_name and host.libvirt_name == domain.name():
                return domain
            if host.mac and host.mac in domain.XMLDesc():
                return domain

        raise error.PowerManagementError(
            'Domain not found for host %s.' % host)

    def supports(self, host):
        try:
            self._find_domain_by_host(host)
        except error.PowerManagementError:
            return False
        return True

    def poweroff(self, host):
        domain = self._find_domain_by_host(host)
        LOG.debug('Power off domain with name: %s', host.mac)
        domain.destroy()
        LOG.info('Domain powered off: %s', host.mac)

    def poweron(self, host):
        domain = self._find_domain_by_host(host)
        LOG.debug('Power on domain with name: %s', domain.name())
        domain.create()
        LOG.info('Domain powered on: %s', domain.name())

    def reset(self, host):
        domain = self._find_domain_by_host(host)
        LOG.debug('Reset domain with name: %s', domain.name())
        domain.reset()
        LOG.info('Domain reset: %s', domain.name())

    def shutdown(self, host):
        domain = self._find_domain_by_host(host)
        LOG.debug('Shutdown domain with name: %s', domain.name())
        domain.shutdown()
        LOG.info('Domain is off: %s', domain.name())

    def snapshot(self, host, snapshot_name, suspend):
        domain = self._find_domain_by_host(host)
        LOG.debug('Create snapshot "%s" for domain with name: %s',
                  snapshot_name, domain.name())
        if suspend:
            domain.suspend()
        domain.snapshotCreateXML(
            '<domainsnapshot><name>{}</name></domainsnapshot>'.format(
                snapshot_name))
        if suspend:
            domain.resume()
        LOG.debug('Created snapshot "%s" for domain with name: %s',
                  snapshot_name, domain.name())

    def revert(self, host, snapshot_name, resume):
        domain = self._find_domain_by_host(host)
        LOG.debug('Revert snapshot "%s" for domain with name: %s',
                  snapshot_name, domain.name())
        snapshot = domain.snapshotLookupByName(snapshot_name)
        if domain.isActive():
            domain.destroy()
        domain.revertToSnapshot(snapshot)
        if resume:
            domain.resume()
        LOG.debug('Reverted snapshot "%s" for domain with name: %s',
                  snapshot_name, domain.name())
