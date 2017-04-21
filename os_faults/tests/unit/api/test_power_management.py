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

import mock

from os_faults.api import error
from os_faults.api import node_collection
from os_faults.api import power_management
from os_faults.tests.unit import test


class PowerManagerTestCase(test.TestCase):

    def setUp(self):
        super(PowerManagerTestCase, self).setUp()

        self.dummy_driver1 = mock.Mock(spec=power_management.PowerDriver)
        self.dummy_driver1.supports.side_effect = lambda host: 'c1' in host.mac

        self.dummy_driver2 = mock.Mock(spec=power_management.PowerDriver)
        self.dummy_driver2.supports.side_effect = lambda host: 'c2' in host.mac

        self.dummy_drivers = [self.dummy_driver1, self.dummy_driver2]
        self.hosts = [
            node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                 fqdn='node1.com'),
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c2',
                                 fqdn='node2.com'),
        ]
        self.pm = power_management.PowerManager()
        self.pm.add_driver(self.dummy_driver1)
        self.pm.add_driver(self.dummy_driver2)

    def test_poweroff(self):
        self.pm.poweroff(self.hosts)

        self.dummy_driver1.poweroff.called_once_with(host=self.hosts[0])
        self.dummy_driver2.poweroff.called_once_with(host=self.hosts[1])

    def test_poweron(self):
        self.pm.poweron(self.hosts)

        self.dummy_driver1.poweron.called_once_with(host=self.hosts[0])
        self.dummy_driver2.poweron.called_once_with(host=self.hosts[1])

    def test_reset(self):
        self.pm.reset(self.hosts)

        self.dummy_driver1.reset.called_once_with(host=self.hosts[0])
        self.dummy_driver2.reset.called_once_with(host=self.hosts[1])

    def test_shutdown(self):
        self.pm.shutdown(self.hosts)

        self.dummy_driver1.shutdown.called_once_with(host=self.hosts[0])
        self.dummy_driver2.shutdown.called_once_with(host=self.hosts[1])

    def test_snapshot(self):
        self.pm.snapshot(self.hosts, 'snap1', suspend=False)

        self.dummy_driver1.snapshot.called_once_with(host=self.hosts[0],
                                                     snapshot_name='snap1',
                                                     suspend=False)
        self.dummy_driver2.snapshot.called_once_with(host=self.hosts[1],
                                                     snapshot_name='snap1',
                                                     suspend=False)

    def test_revert(self):
        self.pm.revert(self.hosts, 'snap1', resume=False)

        self.dummy_driver1.revert.called_once_with(host=self.hosts[0],
                                                   snapshot_name='snap1',
                                                   resume=False)
        self.dummy_driver2.revert.called_once_with(host=self.hosts[1],
                                                   snapshot_name='snap1',
                                                   resume=False)

    def test_run_error(self):
        self.dummy_driver2.reset.side_effect = Exception()

        exc = self.assertRaises(error.PowerManagementError,
                                self.pm.reset, self.hosts)
        self.assertEqual("There are some errors when working the driver. "
                         "Please, check logs for more details.", str(exc))

    def test_run_no_supported_driver(self):
        self.dummy_driver2.supports.side_effect = None
        self.dummy_driver2.supports.return_value = False

        exc = self.assertRaises(error.PowerManagementError,
                                self.pm.reset, self.hosts)
        self.assertEqual("No supported driver found for host "
                         "Host(ip='10.0.0.3', mac='09:7b:74:90:63:c2', "
                         "fqdn='node2.com', libvirt_name=None)", str(exc))

    def test_run_no_drivers(self):
        self.pm = power_management.PowerManager()

        exc = self.assertRaises(error.PowerManagementError,
                                self.pm.reset, self.hosts)
        self.assertEqual("No supported driver found for host "
                         "Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1', "
                         "fqdn='node1.com', libvirt_name=None)", str(exc))
