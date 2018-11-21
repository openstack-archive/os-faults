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

from __future__ import print_function

import collections
import copy
import json
import logging
import os
import shlex
import tempfile

from oslo_concurrency import processutils
import yaml

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


def find_ansible():
    stdout, stderr = processutils.execute(
        *shlex.split('which ansible'), check_exit_code=[0, 1])
    if not stdout:
        raise AnsibleExecutionException(
            'Ansible executable is not found in $PATH')
    return stdout[:-1]


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
        self.ansible = find_ansible()

    @staticmethod
    def _build_proxy_arg(jump_user, jump_host, private_key_file=None):
        key = '-i ' + private_key_file if private_key_file else ''
        return (' -o ProxyCommand="ssh %(key)s -W %%h:%%p %(ssh_args)s '
                '%(user)s@%(host)s"'
                % dict(key=key, user=jump_user,
                       host=jump_host, ssh_args=SSH_COMMON_ARGS))

    def _run_play(self, play_source, host_vars):
        inventory = {}

        for host, variables in host_vars.items():
            host_vars = {}

            for var_name, value in variables.items():
                if value is not None:
                    host_vars[var_name] = value
            inventory[host] = host_vars

            inventory[host]['ansible_ssh_common_args'] = (
                self.options.ssh_common_args)
            inventory[host]['ansible_connection'] = self.options.connection

        full_inventory = {'all': {'hosts': inventory}}

        temp_dir = tempfile.mkdtemp(prefix='os-faults')
        inventory_file_name = os.path.join(temp_dir, 'inventory')
        playbook_file_name = os.path.join(temp_dir, 'playbook')

        with open(inventory_file_name, 'w') as fd:
            print(yaml.safe_dump(full_inventory, default_flow_style=False),
                  file=fd)

        play = {
            'hosts': 'all',
            'gather_facts': 'no',
            'tasks': play_source['tasks'],
        }

        with open(playbook_file_name, 'w') as fd:
            print(yaml.safe_dump([play], default_flow_style=False), file=fd)

        cmd = ('%(ansible)s --module-path %(module_path)s '
               '-i %(inventory)s %(playbook)s' %
               {'ansible': self.ansible,
                'module_path': ':'.join(self.options.module_path),
                'inventory': inventory_file_name,
                'playbook': playbook_file_name})

        logging.info('Executing %s' % cmd)
        command_stdout, command_stderr = processutils.execute(
            *shlex.split(cmd),
            env_variables={'ANSIBLE_STDOUT_CALLBACK': 'json'},
            check_exit_code=False)

        d = json.loads(command_stdout[command_stdout.find('{'):])
        h = d['plays'][0]['tasks'][0]['hosts']
        recs = []
        for h, hv in h.items():
            if hv.get('unreachable'):
                status = STATUS_UNREACHABLE
            elif hv.get('failed'):
                status = STATUS_FAILED
            else:
                status = STATUS_OK
            r = AnsibleExecutionRecord(host=h, status=status, task='',
                                       payload=hv)
            recs.append(r)

        return recs

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
