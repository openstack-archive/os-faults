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

from os_faults.ansible.modules import docker_grep
from os_faults.tests.unit import test


class DockerGrepTestCase(test.TestCase):

    @mock.patch("os_faults.ansible.modules.docker_grep.AnsibleModule")
    def test_main(self, mock_ansible_module):
        ansible_module_inst = mock_ansible_module.return_value
        ansible_module_inst.run_command.return_value = [
            'myrc', 'mystdout', 'mystderr']
        ansible_module_inst.params = {'grep': 'foo'}
        docker_grep.main()

        cmd = (
            'bash -c "docker ps -q | xargs docker inspect --format '
            '\'{{.Path}} {{ range $arg := .Args }}{{$arg}} {{end}}\' | '
            'grep foo"')
        ansible_module_inst.exit_json.assert_called_once_with(
            cmd=cmd,
            rc='myrc',
            stdout='mystdout',
            stderr='mystderr',
        )
