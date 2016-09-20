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


class IPMIDriver(power_management.PowerManagement):
    NAME = 'ipmi'
    DESCRIPTION = 'IPMI power management driver'

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
            logging.error(msg)
            raise

        logging.debug('IPMI response: {}'.format(ret))
        if ret.get('powerstate') != expected_state or 'error' in ret:
            msg = ('Failed to change power state to {!r} on bmc {!r}, '
                   'Node({})'.format(expected_state,
                                     bmc['address'],
                                     mac_address))
            raise error.PowerManagementError(msg)

    def _poweroff(self, mac_address):
        logging.info('Power off Node with MAC address: %s', mac_address)
        self._run_set_power_cmd(
            mac_address, cmd='off', expected_state='off')
        logging.info('Node(%s) was powered off' % mac_address)

    def _poweron(self, mac_address):
        logging.info('Power on Node with MAC address: %s', mac_address)
        self._run_set_power_cmd(
            mac_address, cmd='on', expected_state='on')
        logging.info('Node(%s) was powered on' % mac_address)

    def _reset(self, mac_address):
        logging.info('Reset Node with MAC address: %s', mac_address)
        # boot -- If system is off, then 'on', else 'reset'
        self._run_set_power_cmd(mac_address, cmd='boot')
        # NOTE(astudenov): This command does not wait for node to boot
        logging.info('Node(%s) was reset' % mac_address)

    def poweroff(self, mac_addresses_list):
        utils.run(self._poweroff, mac_addresses_list)

    def poweron(self, mac_addresses_list):
        utils.run(self._poweron, mac_addresses_list)

    def reset(self, mac_addresses_list):
        utils.run(self._reset, mac_addresses_list)
