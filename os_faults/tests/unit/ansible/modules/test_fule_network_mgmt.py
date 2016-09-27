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

from os_faults.ansible.modules import fuel_network_mgmt
from os_faults.tests.unit import test


@ddt.ddt
class FuelNetworkManagementTestCase(test.TestCase):

    def setUp(self):
        super(FuelNetworkManagementTestCase, self).setUp()

    @ddt.data(['management', 'up', 'ip link set br-mgmt up'],
              ['management', 'down', 'ip link set br-mgmt down'],
              ['public', 'up', 'ip link set br-ex up'],
              ['public', 'down', 'ip link set br-ex down'],
              ['private', 'up', 'ip link set br-prv up'],
              ['private', 'down', 'ip link set br-prv down'],
              ['storage', 'up', 'ip link set br-storage up'],
              ['storage', 'down', 'ip link set br-storage down'])
    @ddt.unpack
    @mock.patch("os_faults.ansible.modules.fuel_network_mgmt.AnsibleModule")
    def test_main(self, network_name, operation, cmd, mock_ansible_module):
        ansible_module_inst = mock_ansible_module.return_value
        ansible_module_inst.run_command.return_value = [
            'myrc', 'mystdout', 'mystderr']
        ansible_module_inst.params = {
            'network_name': network_name,
            'operation': operation,
        }
        fuel_network_mgmt.main()
        ansible_module_inst.exit_json.assert_called_once_with(
            cmd=cmd,
            rc='myrc',
            stdout='mystdout',
            stderr='mystderr',
        )
