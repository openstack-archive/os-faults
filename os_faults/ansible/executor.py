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
from ansible.parsing import dataloader
from ansible.playbook import play
from ansible.plugins import callback as callback_pkg

try:
    from ansible.inventory.manager import InventoryManager as Inventory
    from ansible.vars.manager import VariableManager
    PRE_24_ANSIBLE = False
except ImportError:
    # pre-2.4 Ansible
    from ansible.inventory import Inventory
    from ansible.vars import VariableManager
    PRE_24_ANSIBLE = True

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


def make_module_path_option():
    if PRE_24_ANSIBLE:
        # it was a string of colon-separated directories
        module_path = os.pathsep.join(get_module_paths())
    else:
        # now it is a list of strings (MUST have > 1 element)
        module_path = list(get_module_paths())
        if len(module_path) == 1:
            module_path += [module_path[0]]
    return module_path


Options = collections.namedtuple(
    'Options',
    ['connection', 'module_path', 'forks',
     'remote_user', 'private_key_file',
     'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
     'scp_extra_args', 'become', 'become_method',
     'become_user', 'verbosity', 'check', 'diff'])


class AnsibleRunner(object):
    def __init__(self, remote_user='root', password=None, forks=100,
                 jump_host=None, jump_user=None, private_key_file=None,
                 become=None, become_password=None, serial=None):
        super(AnsibleRunner, self).__init__()

        ssh_common_args = SSH_COMMON_ARGS
        if jump_host:
            ssh_common_args += self._build_proxy_arg(
                jump_host=jump_host,
                jump_user=jump_user or remote_user,
                private_key_file=private_key_file)

        self.passwords = dict(conn_pass=password, become_pass=become_password)
        self.options = Options(
            connection='smart',
            module_path=make_module_path_option(),
            forks=forks, remote_user=remote_user,
            private_key_file=private_key_file,
            ssh_common_args=ssh_common_args, ssh_extra_args=None,
            sftp_extra_args=None, scp_extra_args=None,
            become=become, become_method='sudo', become_user='root',
            verbosity=100, check=False, diff=None)
        self.serial = serial or 10

    @staticmethod
    def _build_proxy_arg(jump_user, jump_host, private_key_file=None):
        key = '-i ' + private_key_file if private_key_file else ''
        return (' -o ProxyCommand="ssh %(key)s -W %%h:%%p %(ssh_args)s '
                '%(user)s@%(host)s"'
                % dict(key=key, user=jump_user,
                       host=jump_host, ssh_args=SSH_COMMON_ARGS))

    def _run_play(self, play_source, host_vars):
        host_list = play_source['hosts']

        loader = dataloader.DataLoader()

        # FIXME(jpena): we need to behave differently if we are using
        # Ansible >= 2.4.0.0. Remove when only versions > 2.4 are supported
        if PRE_24_ANSIBLE:
            variable_manager = VariableManager()
            inventory_inst = Inventory(loader=loader,
                                       variable_manager=variable_manager,
                                       host_list=host_list)
            variable_manager.set_inventory(inventory_inst)
        else:
            inventory_inst = Inventory(loader=loader,
                                       sources=','.join(host_list) + ',')
            variable_manager = VariableManager(loader=loader,
                                               inventory=inventory_inst)

        for host, variables in host_vars.items():
            host_inst = inventory_inst.get_host(host)
            for var_name, value in variables.items():
                if value is not None:
                    variable_manager.set_host_variable(
                        host_inst, var_name, value)

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

    def run_playbook(self, playbook, host_vars):
        result = []

        for play_source in playbook:
            play_source['gather_facts'] = 'no'

            result += self._run_play(play_source, host_vars)

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
        LOG.debug('Executing task: %s on hosts: %s with serial: %s',
                  task, hosts, self.serial)

        host_vars = {h.ip: self._build_host_vars(h) for h in hosts}
        task_play = {'hosts': [h.ip for h in hosts],
                     'tasks': [task],
                     'serial': self.serial}
        result = self.run_playbook([task_play], host_vars)

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

    def _build_host_vars(self, host):
        if not host.auth:
            return {}

        ssh_common_args = None
        if 'jump' in host.auth:
            ssh_common_args = SSH_COMMON_ARGS
            ssh_common_args += self._build_proxy_arg(
                jump_host=host.auth['jump']['host'],
                jump_user=host.auth['jump'].get(
                    'username', self.options.remote_user),
                private_key_file=host.auth['jump'].get(
                    'private_key_file', self.options.private_key_file))

        return {
            'ansible_user': host.auth.get('username'),
            'ansible_ssh_pass': host.auth.get('password'),
            'ansible_become': host.auth.get('become') or host.auth.get('sudo'),
            'ansible_become_password': host.auth.get('become_password'),
            'ansible_ssh_private_key_file': host.auth.get('private_key_file'),
            'ansible_ssh_common_args': ssh_common_args,
        }
