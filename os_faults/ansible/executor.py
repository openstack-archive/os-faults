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

import collections
import copy
import logging
import os

from ansible.executor import task_queue_manager
from ansible import inventory
from ansible.parsing import dataloader
from ansible.playbook import play
from ansible.plugins import callback as callback_pkg
from ansible.vars import VariableManager

from os_faults.api import error

LOG = logging.getLogger(__name__)

STATUS_OK = 'OK'
STATUS_FAILED = 'FAILED'
STATUS_UNREACHABLE = 'UNREACHABLE'
STATUS_SKIPPED = 'SKIPPED'

DEFAULT_ERROR_STATUSES = {STATUS_FAILED, STATUS_UNREACHABLE}

SSH_COMMON_ARGS = ('-o UserKnownHostsFile=/dev/null '
                   '-o StrictHostKeyChecking=no '
                   '-o ConnectTimeout=60')

STDOUT_LIMIT = 4096  # Symbols count


class AnsibleExecutionException(Exception):
    pass


class AnsibleExecutionUnreachable(AnsibleExecutionException):
    pass


AnsibleExecutionRecord = collections.namedtuple(
    'AnsibleExecutionRecord', ['host', 'status', 'task', 'payload'])


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


MODULE_PATHS = {
    resolve_relative_path('os_faults/ansible/modules'),
}


def get_module_paths():
    global MODULE_PATHS
    return MODULE_PATHS


def add_module_paths(paths):
    global MODULE_PATHS
    for path in paths:
        if not os.path.exists(path):
            raise error.OSFError('{!r} does not exist'.format(path))
        # find all subfolders
        dirs = [x[0] for x in os.walk(path)]
        MODULE_PATHS.update(dirs)


Options = collections.namedtuple(
    'Options',
    ['connection', 'module_path', 'forks',
     'remote_user', 'private_key_file',
     'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
     'scp_extra_args', 'become', 'become_method',
     'become_user', 'verbosity', 'check'])


class AnsibleRunner(object):
    def __init__(self, remote_user='root', password=None, forks=100,
                 jump_host=None, jump_user=None, private_key_file=None,
                 become=None):
        super(AnsibleRunner, self).__init__()

        ssh_common_args = SSH_COMMON_ARGS
        if jump_host:
            ssh_common_args += (
                ' -o ProxyCommand="ssh -i %(key)s -W %%h:%%p %(ssh_args)s '
                '%(user)s@%(host)s"'
                % dict(key=private_key_file, user=jump_user or remote_user,
                       host=jump_host, ssh_args=SSH_COMMON_ARGS))

        self.passwords = dict(conn_pass=password, become_pass=password)
        self.options = Options(
            connection='smart',
            module_path=os.pathsep.join(get_module_paths()),
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

        storage = []
        callback = MyCallback(storage)

        tqm = task_queue_manager.TaskQueueManager(
            inventory=inventory_inst,
            variable_manager=variable_manager,
            loader=loader,
            options=self.options,
            passwords=self.passwords,
            stdout_callback=callback,
        )

        # create play
        play_inst = play.Play().load(play_source,
                                     variable_manager=variable_manager,
                                     loader=loader)

        # actually run it
        try:
            tqm.run(play_inst)
        finally:
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

        log_result = copy.deepcopy(result)
        LOG.debug('Execution completed with %s result(s):' % len(log_result))
        for lr in log_result:
            if 'stdout' in lr.payload:
                if len(lr.payload['stdout']) > STDOUT_LIMIT:
                    lr.payload['stdout'] = (
                        lr.payload['stdout'][:STDOUT_LIMIT] + '... <cut>')
            if 'stdout_lines' in lr.payload:
                del lr.payload['stdout_lines']
            LOG.debug(lr)

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

        return result
