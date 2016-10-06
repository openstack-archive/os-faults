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

from collections import namedtuple
import copy
import os

from ansible.executor import task_queue_manager
from ansible import inventory
from ansible.parsing import dataloader
from ansible.playbook import play
from ansible.plugins import callback as callback_pkg
from ansible.vars import VariableManager
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

STATUS_OK = 'OK'
STATUS_FAILED = 'FAILED'
STATUS_UNREACHABLE = 'UNREACHABLE'
STATUS_SKIPPED = 'SKIPPED'

DEFAULT_ERROR_STATUSES = {STATUS_FAILED, STATUS_UNREACHABLE}

SSH_COMMON_ARGS = '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'


class AnsibleExecutionException(Exception):
    pass


class AnsibleExecutionUnreachable(AnsibleExecutionException):
    pass


AnsibleExecutionRecord = namedtuple('AnsibleExecutionRecord',
                                    ['host', 'status', 'task', 'payload'])


class MyCallback(callback_pkg.CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'myown'

    def __init__(self, storage, display=None):
        super(MyCallback, self).__init__(display)
        self.storage = storage

    def _store(self, result, status):
        record = AnsibleExecutionRecord(
            host=result._host.get_name(), status=status,
            task=result._task.get_name(), payload=result._result)
        self.storage.append(record)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        super(MyCallback, self).v2_runner_on_failed(result)
        self._store(result, STATUS_FAILED)

    def v2_runner_on_ok(self, result):
        super(MyCallback, self).v2_runner_on_ok(result)
        self._store(result, STATUS_OK)

    def v2_runner_on_skipped(self, result):
        super(MyCallback, self).v2_runner_on_skipped(result)
        self._store(result, STATUS_SKIPPED)

    def v2_runner_on_unreachable(self, result):
        super(MyCallback, self).v2_runner_on_unreachable(result)
        self._store(result, STATUS_UNREACHABLE)


def resolve_relative_path(file_name):
    path = os.path.normpath(os.path.join(
        os.path.dirname(__import__('os_faults').__file__), '../', file_name))
    if os.path.exists(path):
        return path


Options = namedtuple('Options',
                     ['connection', 'password', 'module_path', 'forks',
                      'remote_user', 'private_key_file',
                      'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                      'scp_extra_args', 'become', 'become_method',
                      'become_user', 'verbosity', 'check'])


class AnsibleRunner(object):
    def __init__(self, remote_user='root', password=None, forks=100,
                 jump_host=None, private_key_file=None, become=None):
        super(AnsibleRunner, self).__init__()

        module_path = resolve_relative_path('os_faults/ansible/modules')

        ssh_common_args = SSH_COMMON_ARGS
        if jump_host:
            ssh_common_args += (
                ' -o ProxyCommand="ssh -i %(key)s -W %%h:%%p '
                '%(user)s@%(host)s"'
                % dict(key=private_key_file, user=remote_user, host=jump_host))

        self.options = Options(
            connection='smart', password=password, module_path=module_path,
            forks=forks, remote_user=remote_user,
            private_key_file=private_key_file,
            ssh_common_args=ssh_common_args, ssh_extra_args=None,
            sftp_extra_args=None, scp_extra_args=None,
            become=become, become_method='sudo', become_user='root',
            verbosity=100, check=False)

    def _run_play(self, play_source):
        host_list = play_source['hosts']

        loader = dataloader.DataLoader()
        variable_manager = VariableManager()
        inventory_inst = inventory.Inventory(loader=loader,
                                             variable_manager=variable_manager,
                                             host_list=host_list)
        variable_manager.set_inventory(inventory_inst)
        passwords = dict(vault_pass='secret')

        # create play
        play_inst = play.Play().load(play_source,
                                     variable_manager=variable_manager,
                                     loader=loader)

        storage = []
        callback = MyCallback(storage)

        # actually run it
        tqm = None
        try:
            tqm = task_queue_manager.TaskQueueManager(
                inventory=inventory_inst,
                variable_manager=variable_manager,
                loader=loader,
                options=self.options,
                passwords=passwords,
                stdout_callback=callback,
            )
            tqm.run(play_inst)
        finally:
            if tqm is not None:
                tqm.cleanup()

        return storage

    def run_playbook(self, playbook):
        result = []

        for play_source in playbook:
            play_source['gather_facts'] = 'no'

            result += self._run_play(play_source)

        return result

    def execute(self, hosts, task, raise_on_statuses=DEFAULT_ERROR_STATUSES):
        """Executes the task on every host from the list

        Raises exception if any of the commands fails with one of specified
        statuses.
        :param hosts: list of host addresses
        :param task: Ansible task
        :param raise_on_statuses: raise exception if any of commands return
        any of these statuses
        :return: execution result, type AnsibleExecutionRecord
        """
        LOG.debug('Executing task: %s on hosts: %s', task, hosts)

        task_play = {'hosts': hosts, 'tasks': [task]}
        result = self.run_playbook([task_play])

        if raise_on_statuses:
            errors = []
            only_unreachable = True

            for r in result:
                if r.status in raise_on_statuses:
                    if r.status != STATUS_UNREACHABLE:
                        only_unreachable = False
                    errors.append(r)

            if errors:
                msg = 'Execution failed: %s' % ', '.join((
                    '(host: %s, status: %s)' % (r.host, r.status))
                    for r in errors)
                ek = (AnsibleExecutionUnreachable if only_unreachable
                      else AnsibleExecutionException)
                raise ek(msg)

        log_result = copy.deepcopy(result)
        for r in log_result:
            if len(r.payload['stdout'].encode('utf-8')) > 4096:
                msg = '<Output is removed because its size is more than 4 KB!>'
                r.payload['stdout'] = r.payload['stdout_lines'] = msg
        LOG.debug('Execution result: %s' % log_result)

        return result
