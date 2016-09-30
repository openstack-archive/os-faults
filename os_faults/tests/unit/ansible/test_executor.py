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

import ansible
import mock
import unittest

from os_faults.ansible import executor
from os_faults.tests.unit import test


class ExecutorTestCase(test.TestCase):

    @mock.patch.object(executor, 'AnsibleExecutionRecord')
    def test_MyCallback_init(self, mk):
        ex = executor.MyCallback(mk)
        self.assertEqual(ex.storage, mk)

    @mock.patch.object(ansible.utils, 'display')
    @mock.patch.object(executor, 'AnsibleExecutionRecord')
    def test_MyCallback_init_display(self, mk, mock_display):
        mock_display.verbosity = 1
        ex = executor.MyCallback(mk, mock_display)
        self.assertEqual(ex._display, mock_display)

    def test_MyCallback_store(self,):
        ex = executor.MyCallback(mock.Mock())

        my_host = 'my_host'
        my_task = 'my_task'
        my_result = 'my_result'
        r = mock.Mock()
        r._host.get_name.return_value = my_host
        r._task.get_name.return_value = my_task
        r._result = my_result
        stat = 'Ok'

        ex._store(r, stat)
        ex.storage.append.assert_called_once_with(
            executor.AnsibleExecutionRecord(host=my_host, status=stat,
                                            task=my_task, payload=my_result))

    @mock.patch('ansible.plugins.callback.CallbackBase.v2_runner_on_failed')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_failed_super(self, mock_store,
                                                        mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_failed(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_failed(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_failed(result)
        mock_store.assert_called_once_with(result, executor.STATUS_FAILED)

    @mock.patch('ansible.plugins.callback.CallbackBase.v2_runner_on_ok')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_ok_super(self, mock_store,
                                                    mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_ok(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_ok(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_ok(result)
        mock_store.assert_called_once_with(result, executor.STATUS_OK)

    @mock.patch('ansible.plugins.callback.CallbackBase.v2_runner_on_skipped')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_skipped_super(self,
                                                         mock_store,
                                                         mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_skipped(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_skipped(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_skipped(result)
        mock_store.assert_called_once_with(result, executor.STATUS_SKIPPED)

    @mock.patch(
        'ansible.plugins.callback.CallbackBase.v2_runner_on_unreachable')
    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_unreachable_super(self,
                                                             mock_store,
                                                             mock_callback):
        ex = executor.MyCallback(mock.Mock())
        result = mock.Mock()
        ex.v2_runner_on_unreachable(result)
        mock_callback.assert_called_once_with(result)

    @mock.patch('os_faults.ansible.executor.MyCallback._store')
    def test_MyCallback_store_v2_runner_on_unreachable(self, mock_store):
        result = mock.Mock()
        ex = executor.MyCallback(mock.Mock())
        ex.v2_runner_on_unreachable(result)
        mock_store.assert_called_once_with(result, executor.STATUS_UNREACHABLE)

    @mock.patch('os_faults.ansible.executor.os.path.exists')
    def test_ressolve_path_not_exists(self, mock_exist):
        mock_exist.return_value = False
        r = executor.resolve_relative_path('')
        self.assertIsNone(r)

    @mock.patch('os_faults.ansible.executor.os.path.exists')
    def test_ressolve_path_is_exist(self, mock_exist):
        mock_exist.return_value = True
        r = executor.resolve_relative_path('')
        self.assertIsNot(r, None)

    def test_AnsibleRunner_jump_host(self):
        host = 'my_host'
        ssh_common_args = executor.SSH_COMMON_ARGS
        ar = executor.AnsibleRunner(jump_host=host)
        self.assertLess(len(ssh_common_args), len(ar.options.ssh_common_args))

    @mock.patch.object(executor, 'Options')
    def test_AnsibleRunner_options(self, mock_options):
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

    def test_AnsibleRunner_run_play(self):
        z = executor.AnsibleRunner()
        s = z._run_play({'hosts': ['0.0.0.0']})
        self.assertEqual(s, [executor.AnsibleExecutionRecord(
            host='0.0.0.0', status='UNREACHABLE', task='setup',
            payload={'msg': 'Failed to connect to the host via ssh.',
                     'unreachable': True, 'changed': False})])
        pass

if __name__ == '__main__':
    unittest.main()
