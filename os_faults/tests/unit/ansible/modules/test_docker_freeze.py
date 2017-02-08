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

from os_faults.ansible.modules import docker_freeze
from os_faults.tests.unit import test


class DockerFreezeTestCase(test.TestCase):

    @mock.patch("uuid.uuid4")
    @mock.patch("os.chmod")
    @mock.patch("os_faults.ansible.modules.docker_freeze.open", create=True)
    @mock.patch("os_faults.ansible.modules.docker_freeze.AnsibleModule")
    def test_main(self, mock_ansible_module, mock_open, mock_os_chmod,
                  mock_uuid4):
        ansible_module_inst = mock_ansible_module.return_value
        ansible_module_inst.run_command.return_value = [
            'myrc', 'mystdout', 'mystderr']
        ansible_module_inst.params = {
            'grep_container': 'spam',
            'grep_process': 'eggs',
            'sec': 10,
        }
        mock_uuid4.return_value = 'foo-uuid4'

        docker_freeze.main()

        ansible_module_inst.exit_json.assert_called_once_with(
            cmd='bash -c "nohup /tmp/script.foo-uuid4 &"',
            rc='myrc',
            stdout='mystdout',
            stderr='mystderr',
        )
        mock_os_chmod.assert_called_once_with('/tmp/script.foo-uuid4', 0o770)

        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write.assert_called_once_with("""#!/bin/bash
cids=`docker ps -q`
cid=`docker inspect --format \
     '{{.Id}} {{.Path}} {{ range $arg := .Args }}{{$arg}} {{end}}' | \
     grep spam | awk '{ print $1 }'`
pids=`docker top $cid | grep eggs | awk '{ print $2 }'`
kill -19 $pids
sleep 10
kill -18 $pids
rm /tmp/script.foo-uuid4
""")
