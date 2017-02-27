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

from pyghmi import exceptions as pyghmi_exception
from pyghmi.ipmi import command as ipmi_command

from os_faults.api import error
from os_faults.api import power_management
from os_faults import utils

LOG = logging.getLogger(__name__)


BMC_SCHEMA = {
    'type': 'object',
    'properties': {
        'address': {'type': 'string'},
        'username': {'type': 'string'},
        'password': {'type': 'string'},
    },
    'required': ['address', 'username', 'password']
}


class IPMIDriver(power_management.PowerDriver):
    """IPMI driver.

    **Example configuration:**

    .. code-block:: yaml

        power_managements:
        - driver: ipmi
          args:
            mac_to_bmc:
              aa:bb:cc:dd:ee:01:
                address: 170.0.10.50
                username: admin1
                password: Admin_123
              aa:bb:cc:dd:ee:02:
                address: 170.0.10.51
                username: admin2
                password: Admin_123
            fqdn_to_bmc:
              node3.local:
                address: 170.0.10.52
                username: admin1
                password: Admin_123

    parameters:

    - **mac_to_bmc** - list of dicts where keys are the node MACs and
      values are the corresponding BMC configurations with the folowing
      fields:

      - **address** - ip address of IPMI server
      - **username** - IPMI user
      - **password** - IPMI password
    """

    NAME = 'ipmi'
    DESCRIPTION = 'IPMI power management driver'
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'mac_to_bmc': {
                'type': 'object',
                'patternProperties': {
                    utils.MACADDR_REGEXP: BMC_SCHEMA
                }
            },
            'fqdn_to_bmc': {
                'type': 'object',
                'patternProperties': {
                    utils.FQDN_REGEXP: BMC_SCHEMA
                }
            },
        },
        'anyOf': [
            {'required': ['mac_to_bmc']},
            {'required': ['fqdn_to_bmc']},
        ],
        'additionalProperties': False,
    }

    def __init__(self, params):
        self.mac_to_bmc = params.get('mac_to_bmc', {})
        self.fqdn_to_bmc = params.get('fqdn_to_bmc', {})
        # TODO(astudenov): make macs lowercased

    def _find_bmc_by_host(self, host):
        if host.mac in self.mac_to_bmc:
            return self.mac_to_bmc[host.mac]
        if host.fqdn in self.fqdn_to_bmc:
            return self.fqdn_to_bmc[host.fqdn]

        raise error.PowerManagementError(
            'BMC for {!r} not found!'.format(host))

    def _run_set_power_cmd(self, host, cmd, expected_state=None):
        bmc = self._find_bmc_by_host(host)
        try:
            ipmicmd = ipmi_command.Command(bmc=bmc['address'],
                                           userid=bmc['username'],
                                           password=bmc['password'])
            ret = ipmicmd.set_power(cmd, wait=True)
        except pyghmi_exception.IpmiException:
            msg = 'IPMI cmd {!r} failed on bmc {!r}, {!r}'.format(
                cmd, bmc['address'], host)
            LOG.error(msg, exc_info=True)
            raise

        LOG.debug('IPMI response: {}'.format(ret))
        if ret.get('powerstate') != expected_state or 'error' in ret:
            msg = ('Failed to change power state to {!r} on bmc {!r}, '
                   '{!r}'.format(expected_state, bmc['address'], host))
            raise error.PowerManagementError(msg)

    def supports(self, host):
        try:
            self._find_bmc_by_host(host)
        except error.PowerManagementError:
            return False
        return True

    def poweroff(self, host):
        LOG.debug('Power off Node: %s', host)
        self._run_set_power_cmd(host, cmd='off', expected_state='off')
        LOG.info('Node powered off: %s', host)

    def poweron(self, host):
        LOG.debug('Power on Node: %s', host)
        self._run_set_power_cmd(host, cmd='on', expected_state='on')
        LOG.info('Node powered on: %s', host)

    def reset(self, host):
        LOG.debug('Reset Node: %s', host)
        # boot -- If system is off, then 'on', else 'reset'
        self._run_set_power_cmd(host, cmd='boot')
        # NOTE(astudenov): This command does not wait for node to boot
        LOG.info('Node reset: %s', host)

    def shutdown(self, host):
        LOG.debug('Shutdown Node: %s', host)
        self._run_set_power_cmd(host, cmd='shutdown', expected_state='off')
        LOG.info('Node is off: %s', host)
