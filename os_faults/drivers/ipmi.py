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


class IPMIDriver(power_management.PowerManagement):
    NAME = 'ipmi'
    DESCRIPTION = 'IPMI power management driver'
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'mac_to_bmc': {
                'type': 'object',
                'patternProperties': {
                    '^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$': {
                        'type': 'object',
                        'properties': {
                            'address': {'type': 'string'},
                            'username': {'type': 'string'},
                            'password': {'type': 'string'},
                        },
                        'required': ['address', 'username', 'password']
                    }
                }
            }
        },
        'required': ['mac_to_bmc'],
        'additionalProperties': False,
    }

    def __init__(self, params):
        self.mac_to_bmc = params['mac_to_bmc']

    def _find_bmc_by_mac_address(self, mac_address):
        if mac_address not in self.mac_to_bmc:
            raise error.PowerManagementError(
                'BMC for Node(%s) not found!' % mac_address)

        return self.mac_to_bmc[mac_address]

    def _run_set_power_cmd(self, mac_address, cmd, expected_state=None):
        bmc = self._find_bmc_by_mac_address(mac_address)
        try:
            ipmicmd = ipmi_command.Command(bmc=bmc['address'],
                                           userid=bmc['username'],
                                           password=bmc['password'])
            ret = ipmicmd.set_power(cmd, wait=True)
        except pyghmi_exception.IpmiException:
            msg = 'IPMI cmd {!r} failed on bmc {!r}, Node({})'.format(
                cmd, bmc['address'], mac_address)
            LOG.error(msg, exc_info=True)
            raise

        LOG.debug('IPMI response: {}'.format(ret))
        if ret.get('powerstate') != expected_state or 'error' in ret:
            msg = ('Failed to change power state to {!r} on bmc {!r}, '
                   'Node({})'.format(expected_state,
                                     bmc['address'],
                                     mac_address))
            raise error.PowerManagementError(msg)

    def _poweroff(self, mac_address):
        LOG.debug('Power off Node with MAC address: %s', mac_address)
        self._run_set_power_cmd(
            mac_address, cmd='off', expected_state='off')
        LOG.info('Node powered off: %s', mac_address)

    def _poweron(self, mac_address):
        LOG.debug('Power on Node with MAC address: %s', mac_address)
        self._run_set_power_cmd(
            mac_address, cmd='on', expected_state='on')
        LOG.info('Node powered on: %s', mac_address)

    def _reset(self, mac_address):
        LOG.debug('Reset Node with MAC address: %s', mac_address)
        # boot -- If system is off, then 'on', else 'reset'
        self._run_set_power_cmd(mac_address, cmd='boot')
        # NOTE(astudenov): This command does not wait for node to boot
        LOG.info('Node reset: %s', mac_address)

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
