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

import os_faults
from os_faults.api import node_collection
from os_faults.drivers.power import ipmi
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
            },
            'fqdn_to_bmc': {
                'node2.com': {
                    'address': '55.55.55.56',
                    'username': 'ham',
                    'password': 'eggs'
                }
            }
        }
        self.driver = ipmi.IPMIDriver(self.params)
        self.host = node_collection.Host(
            ip='10.0.0.2', mac='00:00:00:00:00:00', fqdn='node1.com')
        self.host2 = node_collection.Host(
            ip='10.0.0.3', mac='00:00:00:00:00:01', fqdn='node2.com')

    @ddt.data(
        {
            'mac_to_bmc': {
                '00:00:00:00:00:00': {
                    'address': '55.55.55.55',
                    'username': 'foo',
                    'password': 'bar'
                }
            }
        },
        {
            'fqdn_to_bmc': {
                'node2.com': {
                    'address': '55.55.55.56',
                    'username': 'ham',
                    'password': 'eggs'
                }
            }
        },
        {
            'mac_to_bmc': {
                '00:00:00:00:00:00': {
                    'address': '55.55.55.55',
                    'username': 'foo',
                    'password': 'bar'
                }
            },
            'fqdn_to_bmc': {
                'node2.com': {
                    'address': '55.55.55.56',
                    'username': 'ham',
                    'password': 'eggs'
                }
            }
        },
    )
    def test_init(self, config):
        os_faults._init_driver({'driver': 'ipmi', 'args': config})

    def test_supports(self):
        self.assertTrue(self.driver.supports(self.host))
        self.assertTrue(self.driver.supports(self.host2))

    def test_supports_false(self):
        host = node_collection.Host(
            ip='10.0.0.2', mac='00:00:00:00:00:01', fqdn='node1.com')
        self.assertFalse(self.driver.supports(host))

    @mock.patch('pyghmi.ipmi.command.Command')
    def test__run_set_power_cmd(self, mock_command):
        ipmicmd = mock_command.return_value
        ipmicmd.set_power.return_value = {'powerstate': 'off'}

        self.driver._run_set_power_cmd(self.host, 'off', expected_state='off')
        ipmicmd.set_power.assert_called_once_with('off', wait=True)

    @mock.patch('pyghmi.ipmi.command.Command')
    def test__run_set_power_cmd_ipmi_exc(self, mock_command):
        ipmicmd = mock_command.return_value
        ipmicmd.set_power.side_effect = pyghmi_exc.IpmiException()

        self.assertRaises(pyghmi_exc.IpmiException,
                          self.driver._run_set_power_cmd,
                          self.host, 'off', expected_state='off')

    @mock.patch('pyghmi.ipmi.command.Command')
    def test__run_set_power_cmd_unexpected_power_state(self, mock_command):
        ipmicmd = mock_command.return_value
        ipmicmd.set_power.return_value = {'powerstate': 'unexpected state'}

        self.assertRaises(error.PowerManagementError,
                          self.driver._run_set_power_cmd,
                          self.host, 'off', expected_state='off')

    @mock.patch('os_faults.drivers.power.ipmi.IPMIDriver._run_set_power_cmd')
    @ddt.data(('poweroff', 'off', 'off'),
              ('poweron', 'on', 'on'),
              ('reset', 'boot'),
              ('shutdown', 'shutdown', 'off'))
    def test_driver_actions(self, actions, mock__run_set_power_cmd):
        getattr(self.driver, actions[0])(self.host)
        if len(actions) == 3:
            mock__run_set_power_cmd.assert_called_once_with(
                self.host, cmd=actions[1], expected_state=actions[2])
        else:
            mock__run_set_power_cmd.assert_called_once_with(
                self.host, cmd=actions[1])
