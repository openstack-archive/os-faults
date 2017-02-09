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
from os_faults.ansible import executor

from os_faults.api import cloud_management
from os_faults.api import node_collection
from os_faults.common import service
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


class FooServiceInDocker(service.ServiceInDocker):
    SERVICE_NAME = 'foo'
    GREP_CONTAINER = 'bar'
    GREP_PROCESS = 'baz'


class ServiceInDockerTestCase(test.TestCase):

    def setUp(self):
        super(ServiceInDockerTestCase, self).setUp()

        self.mock_cloud_management = mock.Mock(
            spec=cloud_management.CloudManagement)

        self.hosts = [
            node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                 fqdn='node1.com'),
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c2',
                                 fqdn='node2.com'),
            node_collection.Host(ip='10.0.0.4', mac='09:7b:74:90:63:c3',
                                 fqdn='node3.com'),
        ]

        self.nodes = node_collection.NodeCollection(
            cloud_management=self.mock_cloud_management,
            hosts=self.hosts)
        self.mock_cloud_management.get_nodes.return_value = self.nodes

        self.fake_get_nodes_result = [
            fakes.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
            fakes.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3'),
            fakes.FakeAnsibleResult(status=executor.STATUS_FAILED,
                                    payload={'stdout': ''},
                                    host='10.0.0.3'),
        ]
        self.mock_cloud_management.execute_on_cloud.side_effect = [
            self.fake_get_nodes_result,
        ]

        self.service = FooServiceInDocker(
            node_collection.NodeCollection, self.mock_cloud_management)

    def test_get_nodes(self):
        self.assertEqual(['10.0.0.2', '10.0.0.3'],
                         self.service.get_nodes().get_ips())
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            ['10.0.0.2', '10.0.0.3', '10.0.0.4'],
            {'docker_grep': {'grep': 'bar'}}, False)

    def test_kill(self):
        self.mock_cloud_management.execute_on_cloud.side_effect = [
            self.fake_get_nodes_result,
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]]
        self.service.kill()
        self.mock_cloud_management.execute_on_cloud.assert_has_calls((
            mock.call(['10.0.0.2', '10.0.0.3', '10.0.0.4'],
                      {'docker_grep': {'grep': 'bar'}}, False),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'docker_kill': {'grep_container': 'bar',
                                       'grep_process': 'baz',
                                       'sig': 9}}),
        ))

    def test_freeze(self):
        self.mock_cloud_management.execute_on_cloud.side_effect = [
            self.fake_get_nodes_result,
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]]
        self.service.freeze()
        self.mock_cloud_management.execute_on_cloud.assert_has_calls((
            mock.call(['10.0.0.2', '10.0.0.3', '10.0.0.4'],
                      {'docker_grep': {'grep': 'bar'}}, False),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'docker_kill': {'grep_container': 'bar',
                                       'grep_process': 'baz',
                                       'sig': 19}}),
        ))

    def test_freeze_sec(self):
        self.mock_cloud_management.execute_on_cloud.side_effect = [
            self.fake_get_nodes_result,
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]]
        self.service.freeze(sec=5)
        self.mock_cloud_management.execute_on_cloud.assert_has_calls((
            mock.call(['10.0.0.2', '10.0.0.3', '10.0.0.4'],
                      {'docker_grep': {'grep': 'bar'}}, False),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'docker_freeze': {'grep_container': 'bar',
                                         'grep_process': 'baz',
                                         'sec': 5}}),
        ))

    def test_unfreeze(self):
        self.mock_cloud_management.execute_on_cloud.side_effect = [
            self.fake_get_nodes_result,
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]]
        self.service.unfreeze()
        self.mock_cloud_management.execute_on_cloud.assert_has_calls((
            mock.call(['10.0.0.2', '10.0.0.3', '10.0.0.4'],
                      {'docker_grep': {'grep': 'bar'}}, False),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'docker_kill': {'grep_container': 'bar',
                                       'grep_process': 'baz',
                                       'sig': 18}}),
        ))
