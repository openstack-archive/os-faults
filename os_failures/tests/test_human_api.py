# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock

from os_failures.api import human
from os_failures.api import node_collection
from os_failures.api import service as service_api
from os_failures.tests import base


class TestHumanAPI(base.TestCase):

    def test_restart_keystone_service(self):
        distractor = mock.MagicMock()
        service = mock.MagicMock(service_api.Service)

        distractor.get_service = mock.MagicMock(return_value=service)

        command = 'Restart keystone service'
        human.execute(distractor, command)

        distractor.get_service.assert_called_once_with(name='keystone')
        service.restart.assert_called_once_with()

    def test_reboot_one_mysql_node(self):
        distractor = mock.MagicMock()
        service = mock.MagicMock(service_api.Service)
        nodes = mock.MagicMock(node_collection.NodeCollection)
        nodes2 = mock.MagicMock(node_collection.NodeCollection)

        distractor.get_service = mock.MagicMock(return_value=service)
        service.get_nodes = mock.MagicMock(return_value=nodes)
        nodes.pick = mock.MagicMock(return_value=nodes2)

        command = 'Reboot one MySQL node'
        human.execute(distractor, command)

        distractor.get_service.assert_called_once_with(name='mysql')
        nodes.pick.assert_called_once()
        nodes2.reboot.assert_called_once()

    def test_reboot_node_by_fqdn(self):
        distractor = mock.MagicMock()
        nodes = mock.MagicMock(node_collection.NodeCollection)

        distractor.get_service = mock.MagicMock(return_value=None)
        distractor.get_nodes = mock.MagicMock(return_value=nodes)

        command = 'Reboot node-2.domain.tld'
        human.execute(distractor, command)

        distractor.get_nodes.assert_called_once_with(
            fqdns=['node-2.domain.tld'])
        nodes.reboot.assert_called_once()
