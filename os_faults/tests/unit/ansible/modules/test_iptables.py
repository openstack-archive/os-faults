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

from os_faults.ansible.modules import iptables
from os_faults.tests.unit import test


class IptablesTestCase(test.TestCase):

    @mock.patch("os_faults.ansible.modules.iptables.AnsibleModule")
    def test_main_unblock(self, mock_ansible_module):
        ansible_module_inst = mock_ansible_module.return_value
        ansible_module_inst.run_command.return_value = [
            'myrc', 'mystdout', 'mystderr']
        ansible_module_inst.params = {
            'service': 'foo',
            'action': 'unblock',
            'port': 5555,
            'protocol': 'tcp',
        }
        iptables.main()

        cmd = (
            'bash -c "rule=`iptables -L INPUT -n --line-numbers | '
            'grep "foo_temporary_DROP" | cut -d \' \' -f1`; for arg in $rule;'
            ' do iptables -D INPUT -p tcp --dport 5555 '
            '-j DROP -m comment --comment "foo_temporary_DROP"; done"')
        ansible_module_inst.exit_json.assert_called_once_with(
            cmd=cmd,
            rc='myrc',
            stdout='mystdout',
            stderr='mystderr',
        )

    @mock.patch("os_faults.ansible.modules.iptables.AnsibleModule")
    def test_main_block(self, mock_ansible_module):
        ansible_module_inst = mock_ansible_module.return_value
        ansible_module_inst.run_command.return_value = [
            'myrc', 'mystdout', 'mystderr']
        ansible_module_inst.params = {
            'service': 'foo',
            'action': 'block',
            'port': 5555,
            'protocol': 'tcp',
        }
        iptables.main()

        cmd = (
            'bash -c "iptables -I INPUT 1 -p tcp --dport 5555 '
            '-j DROP -m comment --comment "foo_temporary_DROP""')
        ansible_module_inst.exit_json.assert_called_once_with(
            cmd=cmd,
            rc='myrc',
            stdout='mystdout',
            stderr='mystderr',
        )
