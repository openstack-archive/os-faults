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


class MyCallbackTestCase(test.TestCase):

    def test__store(self,):
        ex = executor.MyCallback(mock.Mock())

        my_host = 'my_host'
        my_task = 'my_task'
        my_result = 'my_result'
        r = mock.Mock()
        r._host.get_name.return_value = my_host
        r._task.get_name.return_value = my_task
        r._result = my_result
        stat = 'OK'

        ex._store(r, stat)
        ex.storage.append.assert_called_once_with(
            executor.AnsibleExecutionRecord(host=my_host, status=stat,
                                            task=my_task, payload=my_result))

    @mock.patch('ansible.plugins.callback.CallbackBase.v2_runner_on_failed')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_failed_super(self, mock_store, mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_failed(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_failed(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_failed(result)
        mock_store.assert_called_once_with(result, executor.STATUS_FAILED)

    @mock.patch('ansible.plugins.callback.CallbackBase.v2_runner_on_ok')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_ok_super(self, mock_store, mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_ok(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_ok(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_ok(result)
        mock_store.assert_called_once_with(result, executor.STATUS_OK)

    @mock.patch('ansible.plugins.callback.CallbackBase.v2_runner_on_skipped')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_skipped_super(self, mock_store, mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_skipped(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_skipped(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_skipped(result)
        mock_store.assert_called_once_with(result, executor.STATUS_SKIPPED)

    @mock.patch(
        'ansible.plugins.callback.CallbackBase.v2_runner_on_unreachable')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_unreachable_super(self, mock_store, mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_unreachable(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_v2_runner_on_unreachable(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_unreachable(result)
        mock_store.assert_called_once_with(result, executor.STATUS_UNREACHABLE)


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

    @mock.patch.object(executor, 'Options')
    @ddt.data((
        {},
        dict(become=None, become_method='sudo', become_user='root',
             check=False, connection='smart', diff=None, forks=100,
             private_key_file=None,
             remote_user='root', scp_extra_args=None, sftp_extra_args=None,
             ssh_common_args=executor.SSH_COMMON_ARGS,
             ssh_extra_args=None, verbosity=100),
        dict(conn_pass=None, become_pass=None),
    ), (
        dict(remote_user='root', password='foobar'),
        dict(become=None, become_method='sudo', become_user='root',
             check=False, connection='smart', diff=None, forks=100,
             private_key_file=None,
             remote_user='root', scp_extra_args=None, sftp_extra_args=None,
             ssh_common_args=executor.SSH_COMMON_ARGS,
             ssh_extra_args=None, verbosity=100),
        dict(conn_pass='foobar', become_pass=None),
    ), (
        dict(remote_user='root', password='foobar', become_password='secret'),
        dict(become=None, become_method='sudo', become_user='root',
             check=False, connection='smart', diff=None, forks=100,
             private_key_file=None,
             remote_user='root', scp_extra_args=None, sftp_extra_args=None,
             ssh_common_args=executor.SSH_COMMON_ARGS,
             ssh_extra_args=None, verbosity=100),
        dict(conn_pass='foobar', become_pass='secret'),
    ), (
        dict(remote_user='root', jump_host='jhost.com',
             private_key_file='/path/my.key'),
        dict(become=None, become_method='sudo', become_user='root',
             check=False, connection='smart', diff=None, forks=100,
             private_key_file='/path/my.key',
             remote_user='root', scp_extra_args=None, sftp_extra_args=None,
             ssh_common_args=('-o UserKnownHostsFile=/dev/null '
                              '-o StrictHostKeyChecking=no '
                              '-o ConnectTimeout=60 '
                              '-o ProxyCommand='
                              '"ssh -i /path/my.key '
                              '-W %h:%p '
                              '-o UserKnownHostsFile=/dev/null '
                              '-o StrictHostKeyChecking=no '
                              '-o ConnectTimeout=60 '
                              'root@jhost.com"'),
             ssh_extra_args=None, verbosity=100),
        dict(conn_pass=None, become_pass=None),
    ), (
        dict(remote_user='root', jump_host='jhost.com', jump_user='juser',
             private_key_file='/path/my.key'),
        dict(become=None, become_method='sudo', become_user='root',
             check=False, connection='smart', diff=None, forks=100,
             private_key_file='/path/my.key',
             remote_user='root', scp_extra_args=None, sftp_extra_args=None,
             ssh_common_args=('-o UserKnownHostsFile=/dev/null '
                              '-o StrictHostKeyChecking=no '
                              '-o ConnectTimeout=60 '
                              '-o ProxyCommand='
                              '"ssh -i /path/my.key '
                              '-W %h:%p '
                              '-o UserKnownHostsFile=/dev/null '
                              '-o StrictHostKeyChecking=no '
                              '-o ConnectTimeout=60 '
                              'juser@jhost.com"'),
             ssh_extra_args=None, verbosity=100),
        dict(conn_pass=None, become_pass=None),
    ))
    @ddt.unpack
    def test___init__options(self, config, options_args, passwords,
                             mock_options):
        runner = executor.AnsibleRunner(**config)
        module_path = executor.make_module_path_option()
        mock_options.assert_called_once_with(module_path=module_path,
                                             **options_args)
        self.assertEqual(passwords, runner.passwords)

    @mock.patch.object(executor.task_queue_manager, 'TaskQueueManager')
    @mock.patch('ansible.playbook.play.Play.load')
    @mock.patch('os_faults.ansible.executor.Inventory')
    @mock.patch('os_faults.ansible.executor.VariableManager')
    @mock.patch('ansible.parsing.dataloader.DataLoader')
    def test__run_play(self, mock_dataloader, mock_vmanager, mock_inventory,
                       mock_play_load, mock_taskqm):
        mock_play_load.return_value = 'my_load'
        variable_manager = mock_vmanager.return_value
        host_inst = mock_inventory.return_value.get_host.return_value
        host_vars = {
            '0.0.0.0': {
                'ansible_user': 'foo',
                'ansible_ssh_pass': 'bar',
                'ansible_become': True,
                'ansible_ssh_private_key_file': None,
                'ansible_ssh_common_args': '-o Option=yes',
            }
        }
        ex = executor.AnsibleRunner()
        ex._run_play({'hosts': ['0.0.0.0']}, host_vars)

        mock_taskqm.assert_called_once()
        self.assertEqual(mock_taskqm.mock_calls[1], mock.call().run('my_load'))
        self.assertEqual(mock_taskqm.mock_calls[2], mock.call().cleanup())

        variable_manager.set_host_variable.assert_has_calls((
            mock.call(host_inst, 'ansible_user', 'foo'),
            mock.call(host_inst, 'ansible_ssh_pass', 'bar'),
            mock.call(host_inst, 'ansible_become', True),
            mock.call(host_inst, 'ansible_ssh_common_args', '-o Option=yes'),
        ), any_order=True)

    @mock.patch.object(executor.task_queue_manager, 'TaskQueueManager')
    @mock.patch('ansible.playbook.play.Play.load')
    @mock.patch('os_faults.ansible.executor.Inventory')
    @mock.patch('os_faults.ansible.executor.VariableManager')
    @mock.patch('ansible.parsing.dataloader.DataLoader')
    def test__run_play_no_host_vars(
            self, mock_dataloader, mock_vmanager, mock_inventory,
            mock_play_load, mock_taskqm):
        mock_play_load.return_value = 'my_load'
        variable_manager = mock_vmanager.return_value
        host_vars = {}
        ex = executor.AnsibleRunner()
        ex._run_play({'hosts': ['0.0.0.0']}, host_vars)

        mock_taskqm.assert_called_once()
        self.assertEqual(mock_taskqm.mock_calls[1], mock.call().run('my_load'))
        self.assertEqual(mock_taskqm.mock_calls[2], mock.call().cleanup())

        self.assertEqual(0, variable_manager.set_host_variable.call_count)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner._run_play')
    def test_run_playbook(self, mock_run_play):
        ex = executor.AnsibleRunner()
        my_playbook = [{'gather_facts': 'yes'}, {'gather_facts': 'no'}]
        ex.run_playbook(my_playbook, {})

        self.assertEqual(my_playbook, [{'gather_facts': 'no'},
                                       {'gather_facts': 'no'}])
        self.assertEqual(mock_run_play.call_count, 2)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute(self, mock_run_playbook):
        my_hosts = [node_collection.Host('0.0.0.0'),
                    node_collection.Host('255.255.255.255')]
        my_tasks = 'my_task'
        ex = executor.AnsibleRunner()
        ex.execute(my_hosts, my_tasks)
        mock_run_playbook.assert_called_once_with(
            [{'tasks': ['my_task'],
              'hosts': ['0.0.0.0', '255.255.255.255'],
              'serial': 10}], {'0.0.0.0': {}, '255.255.255.255': {}})

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_with_host_vars(self, mock_run_playbook):
        my_hosts = [
            node_collection.Host('0.0.0.0', auth={'username': 'foo',
                                                  'password': 'bar',
                                                  'sudo': True}),
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
                    'ansible_become': True,
                    'ansible_become_password': None,
                    'ansible_ssh_private_key_file': None,
                    'ansible_ssh_common_args': None,
                },
                '255.255.255.255': {
                    'ansible_user': None,
                    'ansible_ssh_pass': None,
                    'ansible_become': None,
                    'ansible_become_password': None,
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

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_with_serial(self, mock_run_playbook):
        my_hosts = [node_collection.Host('0.0.0.0'),
                    node_collection.Host('255.255.255.255')]
        my_tasks = 'my_task'
        ex = executor.AnsibleRunner(serial=50)
        ex.execute(my_hosts, my_tasks)
        mock_run_playbook.assert_called_once_with(
            [{'tasks': ['my_task'],
              'hosts': ['0.0.0.0', '255.255.255.255'],
              'serial': 50}], {'0.0.0.0': {}, '255.255.255.255': {}})

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_status_unreachable(self, mock_run_playbook):
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

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_status_failed(self, mock_run_playbook):
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

    @mock.patch('copy.deepcopy')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_stdout_is_more_than_stdout_limit(
            self, mock_run_playbook, mock_deepcopy):
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

    @mock.patch('os_faults.ansible.executor.LOG.debug')
    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_payload_without_stdout(self, mock_run_playbook,
                                            mock_debug):
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
    @mock.patch('os_faults.executor.PRE_24_ANSIBLE', False)
    def test_make_module_path_option_ansible_24(self, mock_mp):
        mock_mp.return_value = ['/path/one', 'path/two']
        self.assertEqual(['/path/one', 'path/two'],
                         executor.make_module_path_option())

    @mock.patch('os_faults.executor.get_module_paths')
    @mock.patch('os_faults.executor.PRE_24_ANSIBLE', False)
    def test_make_module_path_option_ansible_24_one_item(self, mock_mp):
        mock_mp.return_value = ['/path/one']
        self.assertEqual(['/path/one', '/path/one'],
                         executor.make_module_path_option())

    @mock.patch('os_faults.executor.get_module_paths')
    @mock.patch('os_faults.executor.PRE_24_ANSIBLE', True)
    def test_make_module_path_option_ansible_pre24(self, mock_mp):
        mock_mp.return_value = ['/path/one', 'path/two']
        self.assertEqual('/path/one:path/two',
                         executor.make_module_path_option())
