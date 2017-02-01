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

from os_faults.ansible.modules import freeze
from os_faults.tests.unit import test


class FreezeTestCase(test.TestCase):

    @mock.patch("os_faults.ansible.modules.freeze.AnsibleModule")
    def test_main(self, mock_ansible_module):
        ansible_module_inst = mock_ansible_module.return_value
        ansible_module_inst.run_command.return_value = [
            'myrc', 'mystdout', 'mystderr']
        ansible_module_inst.params = {
            'grep': 'foo',
            'sec': 15,
        }
        freeze.main()

        cmd = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
               'echo -n \'#!\' > $tf; '
               'echo -en \'/bin/bash\\npids=`ps ax | '
               'grep -v grep | '
               'grep foo | awk {{\\047print $1\\047}}`; '
               'echo $pids | xargs kill -19; sleep 15; '
               'echo $pids | xargs kill -18; rm \' >> $tf; '
               'echo -n $tf >> $tf; '
               'chmod 770 $tf; nohup $tf &"')
        ansible_module_inst.exit_json.assert_called_once_with(
            cmd=cmd,
            rc='myrc',
            stdout='mystdout',
            stderr='mystderr',
        )
