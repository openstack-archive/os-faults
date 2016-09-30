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

import ddt
import mock
from pyghmi import exceptions as pyghmi_exc

from os_faults.drivers import ipmi
from os_faults import error
from os_faults.tests.unit import test


@ddt.ddt
class IPMIDriverTestCase(test.TestCase):

    def setUp(self):
        super(IPMIDriverTestCase, self).setUp()

        self.params = {
            'mac_to_bmc': {
                '00:00:00:00:00:00': {
                    'address': '55.55.55.55',
                    'username': 'foo',
                    'password': 'bar'
                }
            }
        }
        self.driver = ipmi.IPMIDriver(self.params)

    def test__find_bmc_by_mac_address(self):
        bmc = self.driver._find_bmc_by_mac_address('00:00:00:00:00:00')
        self.assertEqual(bmc, self.params['mac_to_bmc']['00:00:00:00:00:00'])

    def test__find_bmc_by_mac_address_mac_address_not_found(self):
        self.assertRaises(error.PowerManagementError,
                          self.driver._find_bmc_by_mac_address,
                          '00:00:00:00:00:01')

    @mock.patch('pyghmi.ipmi.command.Command')
    def test__run_set_power_cmd(self, mock_command):
        ipmicmd = mock_command.return_value
        ipmicmd.set_power.return_value = {'powerstate': 'off'}

        self.driver._run_set_power_cmd('00:00:00:00:00:00',
                                       'off', expected_state='off')
        ipmicmd.set_power.assert_called_once_with('off', wait=True)

    @mock.patch('pyghmi.ipmi.command.Command')
    def test__run_set_power_cmd_ipmi_exc(self, mock_command):
        ipmicmd = mock_command.return_value
        ipmicmd.set_power.side_effect = pyghmi_exc.IpmiException()

        self.assertRaises(pyghmi_exc.IpmiException,
                          self.driver._run_set_power_cmd,
                          '00:00:00:00:00:00', 'off', expected_state='off')

    @mock.patch('pyghmi.ipmi.command.Command')
    def test__run_set_power_cmd_unexpected_power_state(self, mock_command):
        ipmicmd = mock_command.return_value
        ipmicmd.set_power.return_value = {'powerstate': 'unexpected state'}

        self.assertRaises(error.PowerManagementError,
                          self.driver._run_set_power_cmd,
                          '00:00:00:00:00:00', 'off', expected_state='off')

    @mock.patch('os_faults.drivers.ipmi.IPMIDriver._run_set_power_cmd')
    @ddt.data(('_poweroff', 'off'), ('_poweron', 'on'), ('_reset', 'boot'))
    def test__driver_actions(self, actions, mock__run_set_power_cmd):
        getattr(self.driver, actions[0])('00:00:00:00:00:00')
        if actions[0] in ('_poweroff', '_poweron'):
            mock__run_set_power_cmd.assert_called_once_with(
                '00:00:00:00:00:00', cmd=actions[1], expected_state=actions[1])
        else:
            mock__run_set_power_cmd.assert_called_once_with(
                '00:00:00:00:00:00', cmd=actions[1])

    @mock.patch('os_faults.utils.run')
    @ddt.data('poweroff', 'poweron', 'reset')
    def test_driver_actions(self, action, mock_run):
        macs_list = ['00:00:00:00:00:00', '00:00:00:00:00:01']
        getattr(self.driver, action)(macs_list)
        mock_run.assert_called_once_with(getattr(self.driver, '_%s' % action),
                                         macs_list)
