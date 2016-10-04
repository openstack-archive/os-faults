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
        self.assertIsNot(r, None)

    def test___init__jump_host(self):
        host = 'my_host'
        ssh_common_args = executor.SSH_COMMON_ARGS
        ar = executor.AnsibleRunner(jump_host=host)
        self.assertLess(len(ssh_common_args), len(ar.options.ssh_common_args))

    @mock.patch.object(executor, 'Options')
    def test___init__options(self, mock_options):
        executor.AnsibleRunner()
        module_path = executor.resolve_relative_path(
            'os_faults/ansible/modules')
        mock_options.assert_called_once_with(
            become=None, become_method='sudo', become_user='root',
            check=False, connection='smart', forks=100,
            module_path=module_path, password=None, private_key_file=None,
            remote_user='root', scp_extra_args=None, sftp_extra_args=None,
            ssh_common_args=executor.SSH_COMMON_ARGS,
            ssh_extra_args=None, verbosity=100)

    @mock.patch.object(executor.task_queue_manager, 'TaskQueueManager')
    @mock.patch('ansible.playbook.play.Play.load')
    @mock.patch('ansible.inventory.Inventory')
    @mock.patch('ansible.vars.VariableManager.set_inventory')
    @mock.patch('ansible.parsing.dataloader.DataLoader')
    def test__run_play(self, mock_dataloader, mock_vmanager, mock_inventory,
                       mock_play_load, mock_taskqm):
        mock_play_load.return_value = 'my_load'
        ex = executor.AnsibleRunner()
        ex._run_play({'hosts': ['0.0.0.0']})

        mock_taskqm.assert_called_once()
        self.assertEqual(mock_taskqm.mock_calls[1], mock.call().run('my_load'))
        self.assertEqual(mock_taskqm.mock_calls[2], mock.call().cleanup())

    @mock.patch('os_faults.ansible.executor.AnsibleRunner._run_play')
    def test_run_playbook(self, mock_run_play):
        ex = executor.AnsibleRunner()
        my_playbook = [{'gather_facts': 'yes'}, {'gather_facts': 'no'}]
        ex.run_playbook(my_playbook)

        self.assertEqual(my_playbook, [{'gather_facts': 'no'},
                                       {'gather_facts': 'no'}])
        self.assertEqual(mock_run_play.call_count, 2)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute(self, mock_run_playbook):
        my_hosts = ['0.0.0.0', '255.255.255.255']
        my_tasks = 'my_task'
        ex = executor.AnsibleRunner()
        ex.execute(my_hosts, my_tasks)
        mock_run_playbook.assert_called_once_with(
            [{'tasks': ['my_task'],
              'hosts': ['0.0.0.0', '255.255.255.255']}])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_status_unreachable(self, mock_run_playbook):
        my_hosts = ['0.0.0.0', '255.255.255.255']
        my_tasks = 'my_task'
        my_statuses = {executor.STATUS_FAILED,
                       executor.STATUS_SKIPPED, executor.STATUS_UNREACHABLE}
        r0 = mock.Mock()
        r0.host = my_hosts[0]
        r0.status = executor.STATUS_OK
        r1 = mock.Mock()
        r1.host = my_hosts[1]
        r1.status = executor.STATUS_UNREACHABLE

        mock_run_playbook.return_value = [r0, r1]
        ex = executor.AnsibleRunner()

        err = self.assertRaises(executor.AnsibleExecutionException,
                                ex.execute, my_hosts, my_tasks, my_statuses)
        self.assertEqual(type(err), executor.AnsibleExecutionUnreachable)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner.run_playbook')
    def test_execute_status_failed(self, mock_run_playbook):
        my_hosts = ['0.0.0.0', '255.255.255.255']
        my_tasks = 'my_task'
        my_statuses = {executor.STATUS_OK, executor.STATUS_FAILED,
                       executor.STATUS_SKIPPED, executor.STATUS_UNREACHABLE}
        r0 = mock.Mock()
        r0.host = my_hosts[0]
        r0.status = executor.STATUS_OK
        r1 = mock.Mock()
        r1.host = my_hosts[1]
        r1.status = executor.STATUS_UNREACHABLE

        mock_run_playbook.return_value = [r0, r1]
        ex = executor.AnsibleRunner()

        err = self.assertRaises(executor.AnsibleExecutionException,
                                ex.execute, my_hosts, my_tasks, my_statuses)
        self.assertEqual(type(err), executor.AnsibleExecutionException)
