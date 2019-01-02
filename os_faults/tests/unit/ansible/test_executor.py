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

from os_faults.ansible import executor
from os_faults.api import node_collection
from os_faults.tests.unit import test


@ddt.ddt
class AnsibleRunnerTestCase(test.TestCase):

    @mock.patch('os_faults.ansible.executor.os.path.exists')
    def test_resolve_relative_path_doesnt_exist(self, mock_exist):
        mock_exist.return_value = False
        r = executor.resolve_relative_path('')
        self.assertIsNone(r)

    @mock.patch('os_faults.ansible.executor.os.path.exists')
    def test_resolve_relative_path_exists(self, mock_exist):
        mock_exist.return_value = True
        r = executor.resolve_relative_path('')
        self.assertIsNotNone(r)

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch.object(executor, 'Options')
    @ddt.data((
        {},
        {},
    ), (
        dict(username='root', password='foobar'),
        dict(ansible_user='root', ansible_ssh_pass='foobar',
             ansible_become_user=None, ansible_become_pass=None,
             ansible_become_method=None,
             ansible_ssh_private_key_file=None,
             ansible_ssh_common_args=executor.SSH_COMMON_ARGS),
    ), (
        dict(username='dev', password='foobar', become_password='secret'),
        dict(ansible_user='dev', ansible_ssh_pass='foobar',
             ansible_become_user=None, ansible_become_pass='secret',
             ansible_become_method=None,
             ansible_ssh_private_key_file=None,
             ansible_ssh_common_args=executor.SSH_COMMON_ARGS),
    ), (
        dict(username='dev', jump={'host': 'jhost.com'},
             private_key_file='/path/my.key'),
        dict(ansible_user='dev', ansible_ssh_pass=None,
             ansible_become_user=None, ansible_become_pass=None,
             ansible_become_method=None,
             ansible_ssh_private_key_file='/path/my.key',
             ansible_ssh_common_args=('-o UserKnownHostsFile=/dev/null '
                                      '-o StrictHostKeyChecking=no '
                                      '-o ConnectTimeout=60 '
                                      '-o ProxyCommand='
                                      '"ssh  '
                                      '-W %h:%p '
                                      '-o UserKnownHostsFile=/dev/null '
                                      '-o StrictHostKeyChecking=no '
                                      '-o ConnectTimeout=60 '
                                      'dev@jhost.com"')),
    ), (
        dict(username='dev', jump={'host': 'jhost.com', 'username': 'juser',
                                   'private_key_file': '/path/my.key'}),
        dict(ansible_user='dev', ansible_ssh_pass=None,
             ansible_become_user=None, ansible_become_pass=None,
             ansible_become_method=None,
             ansible_ssh_private_key_file=None,
             ansible_ssh_common_args=('-o UserKnownHostsFile=/dev/null '
                                      '-o StrictHostKeyChecking=no '
                                      '-o ConnectTimeout=60 '
                                      '-o ProxyCommand='
                                      '"ssh -i /path/my.key '
                                      '-W %h:%p '
                                      '-o UserKnownHostsFile=/dev/null '
                                      '-o StrictHostKeyChecking=no '
                                      '-o ConnectTimeout=60 '
                                      'juser@jhost.com"')),
    ))
    @ddt.unpack
    def test___init__options(self, auth, default_host_vars, mock_options, _):
        runner = executor.AnsibleRunner(auth=auth)
        module_path = executor.make_module_path_option()
        mock_options.assert_called_once_with(
            module_path=module_path, connection='smart', forks=100)
        self.assertEqual(default_host_vars, runner.default_host_vars)

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner._run_play')
    def test_run_playbook(self, mock_run_play, _):
        ex = executor.AnsibleRunner()
        my_playbook = [{'gather_facts': 'yes'}, {'gather_facts': 'no'}]
        ex.run_playbook(my_playbook, {})

        self.assertEqual(my_playbook, [{'gather_facts': 'no'},
                                       {'gather_facts': 'no'}])
        self.assertEqual(mock_run_play.call_count, 2)

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute(self, mock_run_playbook, _):
        my_hosts = [node_collection.Host('0.0.0.0'),
                    node_collection.Host('255.255.255.255')]
        my_tasks = 'my_task'
        ex = executor.AnsibleRunner()
        ex.execute(my_hosts, my_tasks)
        mock_run_playbook.assert_called_once_with(
            [{'tasks': ['my_task'],
              'hosts': ['0.0.0.0', '255.255.255.255'],
              'serial': 10}], {'0.0.0.0': {}, '255.255.255.255': {}})

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_with_host_vars(self, mock_run_playbook, _):
        my_hosts = [
            node_collection.Host('0.0.0.0', auth={'username': 'foo',
                                                  'password': 'bar',
                                                  'become_username': 'root'}),
            node_collection.Host('255.255.255.255',
                                 auth={'jump': {'host': '192.168.1.100',
                                                'username': 'foo'}})]
        my_tasks = 'my_task'
        ex = executor.AnsibleRunner()
        ex.execute(my_hosts, my_tasks)
        mock_run_playbook.assert_called_once_with(
            [{'tasks': ['my_task'],
              'hosts': ['0.0.0.0', '255.255.255.255'],
              'serial': 10}],
            {
                '0.0.0.0': {
                    'ansible_user': 'foo',
                    'ansible_ssh_pass': 'bar',
                    'ansible_become_method': None,
                    'ansible_become_user': 'root',
                    'ansible_become_pass': None,
                    'ansible_ssh_private_key_file': None,
                    'ansible_ssh_common_args': executor.SSH_COMMON_ARGS,
                },
                '255.255.255.255': {
                    'ansible_user': None,
                    'ansible_ssh_pass': None,
                    'ansible_become_method': None,
                    'ansible_become_user': None,
                    'ansible_become_pass': None,
                    'ansible_ssh_private_key_file': None,
                    'ansible_ssh_common_args':
                        '-o UserKnownHostsFile=/dev/null '
                        '-o StrictHostKeyChecking=no '
                        '-o ConnectTimeout=60 '
                        '-o ProxyCommand="'
                        'ssh  -W %h:%p '
                        '-o UserKnownHostsFile=/dev/null '
                        '-o StrictHostKeyChecking=no '
                        '-o ConnectTimeout=60 '
                        'foo@192.168.1.100"'}})

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_with_serial(self, mock_run_playbook, _):
        my_hosts = [node_collection.Host('0.0.0.0'),
                    node_collection.Host('255.255.255.255')]
        my_tasks = 'my_task'
        ex = executor.AnsibleRunner(serial=50)
        ex.execute(my_hosts, my_tasks)
        mock_run_playbook.assert_called_once_with(
            [{'tasks': ['my_task'],
              'hosts': ['0.0.0.0', '255.255.255.255'],
              'serial': 50}], {'0.0.0.0': {}, '255.255.255.255': {}})

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_status_unreachable(self, mock_run_playbook, _):
        my_hosts = [node_collection.Host('0.0.0.0'),
                    node_collection.Host('255.255.255.255')]
        my_tasks = 'my_task'
        my_statuses = {executor.STATUS_FAILED,
                       executor.STATUS_SKIPPED, executor.STATUS_UNREACHABLE}
        r0 = executor.AnsibleExecutionRecord(
            host='0.0.0.0', status=executor.STATUS_OK, task={}, payload={})
        r1 = executor.AnsibleExecutionRecord(
            host='255.255.255.255', status=executor.STATUS_UNREACHABLE,
            task={}, payload={})

        mock_run_playbook.return_value = [r0, r1]
        ex = executor.AnsibleRunner()

        err = self.assertRaises(executor.AnsibleExecutionException,
                                ex.execute, my_hosts, my_tasks, my_statuses)
        self.assertEqual(type(err), executor.AnsibleExecutionUnreachable)

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_status_failed(self, mock_run_playbook, _):
        my_hosts = [node_collection.Host('0.0.0.0'),
                    node_collection.Host('255.255.255.255')]
        my_tasks = 'my_task'
        my_statuses = {executor.STATUS_OK, executor.STATUS_FAILED,
                       executor.STATUS_SKIPPED, executor.STATUS_UNREACHABLE}
        r0 = executor.AnsibleExecutionRecord(
            host='0.0.0.0', status=executor.STATUS_OK, task={}, payload={})
        r1 = executor.AnsibleExecutionRecord(
            host='255.255.255.255', status=executor.STATUS_UNREACHABLE,
            task={}, payload={})

        mock_run_playbook.return_value = [r0, r1]
        ex = executor.AnsibleRunner()

        err = self.assertRaises(executor.AnsibleExecutionException,
                                ex.execute, my_hosts, my_tasks, my_statuses)
        self.assertEqual(type(err), executor.AnsibleExecutionException)

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('copy.deepcopy')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_stdout_is_more_than_stdout_limit(
            self, mock_run_playbook, mock_deepcopy, _):
        result = mock.Mock()
        result.payload = {'stdout': 'a' * (executor.STDOUT_LIMIT + 1),
                          'stdout_lines': 'a' * (executor.STDOUT_LIMIT + 1)}
        mock_run_playbook.return_value = [result]

        mock_deepcopy.return_value = [result]
        log_result = mock_deepcopy.return_value[0]

        my_hosts = [node_collection.Host('0.0.0.0'),
                    node_collection.Host('255.255.255.255')]
        my_tasks = 'my_task'
        ex = executor.AnsibleRunner()
        ex.execute(my_hosts, my_tasks)

        self.assertEqual('a' * executor.STDOUT_LIMIT + '... <cut>',
                         log_result.payload['stdout'])

    @mock.patch('os_faults.ansible.executor.find_ansible')
    @mock.patch('os_faults.ansible.executor.LOG.debug')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_payload_without_stdout(self, mock_run_playbook,
                                            mock_debug, _):
        task = {'task': 'foo'}
        host = '0.0.0.0'
        result = executor.AnsibleExecutionRecord(
            host=host, status=executor.STATUS_OK,
            task=task, payload={'foo': 'bar'})
        mock_run_playbook.return_value = [result]

        hosts = [node_collection.Host('0.0.0.0')]
        ex = executor.AnsibleRunner()
        ex.execute(hosts, task)

        mock_debug.assert_has_calls((
            mock.call('Executing task: %s on hosts: %s with serial: %s',
                      task, hosts, 10),
            mock.call('Execution completed with 1 result(s):'),
            mock.call(result),
        ))

    @mock.patch('os_faults.executor.get_module_paths')
    def test_make_module_path_option_ansible_24(self, mock_mp):
        mock_mp.return_value = ['/path/one', 'path/two']
        self.assertEqual(['/path/one', 'path/two'],
                         executor.make_module_path_option())

    @mock.patch('os_faults.executor.get_module_paths')
    def test_make_module_path_option_ansible_24_one_item(self, mock_mp):
        mock_mp.return_value = ['/path/one']
        self.assertEqual(['/path/one', '/path/one'],
                         executor.make_module_path_option())
