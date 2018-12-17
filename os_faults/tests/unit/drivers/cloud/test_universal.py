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

from os_faults.api import error
from os_faults.drivers.cloud import universal
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


@ddt.ddt
class UniversalCloudManagementTestCase(test.TestCase):

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data((
        dict(),
        dict(),
    ))
    @ddt.unpack
    def test_init(self, config, expected_runner_call, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value

        cloud = universal.UniversalCloudManagement(config)

        mock_ansible_runner.assert_called_with(**expected_runner_call)
        self.assertIs(cloud.cloud_executor, ansible_runner_inst)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_no_discovery(self, mock_ansible_runner):
        address = '10.0.0.10'
        ansible_result = fakes.FakeAnsibleResult(
            payload=dict(stdout='openstack.local'))
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [ansible_result]
        ]

        cloud = universal.UniversalCloudManagement(dict(address=address))
        self.assertRaises(error.OSFError, cloud.verify)
