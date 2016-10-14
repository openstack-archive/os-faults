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

import copy

import mock

from os_faults.api import error
from os_faults.api import power_management
from os_faults.drivers import fuel
from os_faults.tests.unit import test


class FuelNodeCollectionTestCase(test.TestCase):

    def setUp(self):
        super(FuelNodeCollectionTestCase, self).setUp()
        self.mock_cloud_management = mock.Mock(spec=fuel.FuelManagement)
        self.mock_power_management = mock.Mock(
            spec=power_management.PowerManagement)
        self.hosts = [
            dict(ip='10.0.0.2', mac='09:7b:74:90:63:c1', fqdn='node1.com'),
            dict(ip='10.0.0.3', mac='09:7b:74:90:63:c2', fqdn='node2.com'),
            dict(ip='10.0.0.4', mac='09:7b:74:90:63:c3', fqdn='node3.com'),
            dict(ip='10.0.0.5', mac='09:7b:74:90:63:c4', fqdn='node4.com'),
        ]

        self.node_collection = fuel.FuelNodeCollection(
            cloud_management=self.mock_cloud_management,
            power_management=self.mock_power_management,
            hosts=copy.deepcopy(self.hosts))

    def test_len(self):
        self.assertEqual(4, len(self.node_collection))

    def test_get_ips(self):
        self.assertEqual(['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5'],
                         self.node_collection.get_ips())

    def test_get_macs(self):
        self.assertEqual(['09:7b:74:90:63:c1',
                          '09:7b:74:90:63:c2',
                          '09:7b:74:90:63:c3',
                          '09:7b:74:90:63:c4'],
                         self.node_collection.get_macs())

    def test_iterate_hosts(self):
        self.assertEqual(self.hosts,
                         list(self.node_collection.iterate_hosts()))

    def test_pick(self):
        one = self.node_collection.pick()
        self.assertEqual(1, len(one))
        self.assertIn(one.hosts[0], self.hosts)

    def test_run_task(self):
        self.node_collection.run_task({'foo': 'bar'}, raise_on_error=False)
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            ['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5'], {'foo': 'bar'},
            raise_on_error=False)

    def test_pick_count(self):
        two = self.node_collection.pick(count=2)
        self.assertEqual(2, len(two))
        self.assertIn(two.hosts[0], self.hosts)
        self.assertIn(two.hosts[1], self.hosts)

    def test_pick_exception(self):
        self.assertRaises(
            error.NodeCollectionError, self.node_collection.pick, count=10)

    def test_poweroff(self):
        self.node_collection.poweroff()
        self.mock_power_management.poweroff.assert_called_once_with(
            ['09:7b:74:90:63:c1', '09:7b:74:90:63:c2',
             '09:7b:74:90:63:c3', '09:7b:74:90:63:c4'])

    def test_poweron(self):
        self.node_collection.poweron()
        self.mock_power_management.poweron.assert_called_once_with(
            ['09:7b:74:90:63:c1', '09:7b:74:90:63:c2',
             '09:7b:74:90:63:c3', '09:7b:74:90:63:c4'])

    def test_reset(self):
        self.node_collection.reset()
        self.mock_power_management.reset.assert_called_once_with(
            ['09:7b:74:90:63:c1', '09:7b:74:90:63:c2',
             '09:7b:74:90:63:c3', '09:7b:74:90:63:c4'])

    def test_connect(self):
        self.node_collection.connect(network_name='storage')
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            ['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5'],
            {'fuel_network_mgmt': {'operation': 'up',
                                   'network_name': 'storage'}})

    def test_disconnect(self):
        self.node_collection.disconnect(network_name='storage')
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            ['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5'],
            {'fuel_network_mgmt': {'operation': 'down',
                                   'network_name': 'storage'}})

    def test_reboot(self):
        self.node_collection.reboot()
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            ['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5'],
            {'command': 'reboot now'})
