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
import six

from os_faults.api import cloud_management
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.api import power_management
from os_faults.tests.unit import test


class MyNodeCollection(node_collection.NodeCollection):
    pass


class NodeCollectionTestCase(test.TestCase):

    def setUp(self):
        super(NodeCollectionTestCase, self).setUp()
        self.mock_cloud_management = mock.Mock(
            spec=cloud_management.CloudManagement)
        self.mock_power_manager = mock.Mock(
            spec=power_management.PowerManager)
        self.mock_cloud_management.power_manager = self.mock_power_manager
        self.hosts = [
            node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                 fqdn='node1.com'),
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c2',
                                 fqdn='node2.com'),
            node_collection.Host(ip='10.0.0.4', mac='09:7b:74:90:63:c3',
                                 fqdn='node3.com'),
            node_collection.Host(ip='10.0.0.5', mac='09:7b:74:90:63:c4',
                                 fqdn='node4.com'),
        ]

        self.node_collection = node_collection.NodeCollection(
            cloud_management=self.mock_cloud_management,
            hosts=copy.deepcopy(self.hosts))

        self.hosts2 = [
            node_collection.Host(ip='10.0.0.7', mac='09:7b:74:90:63:c7',
                                 fqdn='node6.com'),
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c2',
                                 fqdn='node2.com'),
            node_collection.Host(ip='10.0.0.6', mac='09:7b:74:90:63:c6',
                                 fqdn='node5.com'),
            node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                 fqdn='node1.com'),
        ]

        self.node_collection2 = node_collection.NodeCollection(
            cloud_management=self.mock_cloud_management,
            hosts=copy.deepcopy(self.hosts2))

    def test_check_types_wrong_type(self):
        collection = MyNodeCollection(None, [])
        self.assertRaises(TypeError, self.node_collection._check_nodes_types,
                          collection)
        self.assertRaises(TypeError, collection._check_nodes_types,
                          self.node_collection)

    def test_check_types_wrong_cloud_management(self):
        collection = node_collection.NodeCollection(None, [])
        self.assertRaises(error.NodeCollectionError,
                          self.node_collection._check_nodes_types, collection)
        self.assertRaises(error.NodeCollectionError,
                          collection._check_nodes_types, self.node_collection)

    def test_repr(self):
        self.assertIsInstance(repr(self.node_collection), six.string_types)

    def test_len(self):
        self.assertEqual(4, len(self.node_collection))

    def test_add(self):
        collection = self.node_collection + self.node_collection2
        self.assertEqual(['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5',
                          '10.0.0.6', '10.0.0.7'],
                         collection.get_ips())

    def test_sub(self):
        collection = self.node_collection - self.node_collection2
        self.assertEqual(['10.0.0.4', '10.0.0.5'],
                         collection.get_ips())

    def test_and(self):
        collection = self.node_collection & self.node_collection2
        self.assertEqual(['10.0.0.2', '10.0.0.3'],
                         collection.get_ips())

    def test_or(self):
        collection = self.node_collection | self.node_collection2
        self.assertEqual(['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5',
                          '10.0.0.6', '10.0.0.7'],
                         collection.get_ips())

    def test_xor(self):
        collection = self.node_collection ^ self.node_collection2
        self.assertEqual(['10.0.0.4', '10.0.0.5', '10.0.0.6', '10.0.0.7'],
                         collection.get_ips())

    def test_in(self):
        self.assertIn(self.hosts[0], self.node_collection)

    def test_not_in(self):
        self.assertNotIn(self.hosts2[2], self.node_collection)

    def test_iter(self):
        self.assertEqual(self.hosts, list(self.node_collection))

    def test_getitem(self):
        self.assertEqual(self.hosts[0], self.node_collection[0])

    def test_get_ips(self):
        self.assertEqual(['10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5'],
                         self.node_collection.get_ips())

    def test_get_macs(self):
        self.assertEqual(['09:7b:74:90:63:c1',
                          '09:7b:74:90:63:c2',
                          '09:7b:74:90:63:c3',
                          '09:7b:74:90:63:c4'],
                         self.node_collection.get_macs())

    def test_get_fqdns(self):
        self.assertEqual(['node1.com', 'node2.com', 'node3.com', 'node4.com'],
                         self.node_collection.get_fqdns())

    def test_pick(self):
        one = self.node_collection.pick()
        self.assertEqual(1, len(one))
        self.assertIn(next(iter(one.hosts)), self.hosts)

    def test_filter(self):
        one = self.node_collection.filter(lambda host: host.ip == '10.0.0.2')
        self.assertEqual(1, len(one))
        self.assertEqual(self.hosts[0], one.hosts[0])

    def test_filter_error(self):
        self.assertRaises(error.NodeCollectionError,
                          self.node_collection.filter,
                          lambda host: host.ip == 'foo')

    def test_run_task(self):
        result = self.node_collection.run_task({'foo': 'bar'},
                                               raise_on_error=False)
        mock_execute_on_cloud = self.mock_cloud_management.execute_on_cloud
        expected_result = mock_execute_on_cloud.return_value
        self.assertIs(result, expected_result)
        mock_execute_on_cloud.assert_called_once_with(
            self.hosts, {'foo': 'bar'}, raise_on_error=False)

    def test_pick_count(self):
        two = self.node_collection.pick(count=2)
        self.assertEqual(2, len(two))
        for host in two:
            self.assertIn(host, self.node_collection)

    def test_pick_exception(self):
        self.assertRaises(
            error.NodeCollectionError, self.node_collection.pick, count=10)

    def test_poweroff(self):
        self.node_collection.poweroff()
        self.mock_power_manager.poweroff.assert_called_once_with(self.hosts)

    def test_poweron(self):
        self.node_collection.poweron()
        self.mock_power_manager.poweron.assert_called_once_with(self.hosts)

    def test_reset(self):
        self.node_collection.reset()
        self.mock_power_manager.reset.assert_called_once_with(self.hosts)

    def test_shutdown(self):
        self.node_collection.shutdown()
        self.mock_power_manager.shutdown.assert_called_once_with(self.hosts)

    def test_reboot(self):
        self.node_collection.reboot()
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            self.hosts, {'command': 'reboot now'})

    def test_snapshot(self):
        self.node_collection.snapshot('foo')
        self.mock_power_manager.snapshot.assert_called_once_with(
            self.hosts, 'foo', True)

    def test_revert(self):
        self.node_collection.revert('foo')
        self.mock_power_manager.revert.assert_called_once_with(
            self.hosts, 'foo', True)
