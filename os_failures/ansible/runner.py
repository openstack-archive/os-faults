# Copyright (c) 2016 OpenStack Foundation
#
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

from ansible.executor import task_queue_manager
from ansible import inventory
from ansible.parsing import dataloader
from ansible.playbook import play
from ansible.plugins import callback as callback_pkg
from ansible.vars import VariableManager
from oslo_log import log as logging

from os_failures import utils

LOG = logging.getLogger(__name__)


def _light_rec(result):
    for r in result:
        c = copy.deepcopy(r)
        if 'records' in c:
            del c['records']
        if 'series' in c:
            del c['series']
        yield c


def _log_result(result):
    # todo check current log level before doing heavy things
    LOG.debug('Execution result (filtered): %s', list(_light_rec(result)))


class MyCallback(callback_pkg.CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'myown'

    def __init__(self, storage, display=None):
        super(MyCallback, self).__init__(display)
        self.storage = storage

    def _store(self, result, status):
        record = dict(host=result._host.get_name(),
                      status=status,
                      task=result._task.get_name(),
                      payload=result._result)
        self.storage.append(record)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        super(MyCallback, self).v2_runner_on_failed(result)
        self._store(result, 'FAILED')

    def v2_runner_on_ok(self, result):
        super(MyCallback, self).v2_runner_on_ok(result)
        self._store(result, 'OK')

    def v2_runner_on_skipped(self, result):
        super(MyCallback, self).v2_runner_on_skipped(result)
        self._store(result, 'SKIPPED')

    def v2_runner_on_unreachable(self, result):
        super(MyCallback, self).v2_runner_on_unreachable(result)
        self._store(result, 'UNREACHABLE')


Options = namedtuple('Options',
                     ['connection', 'password', 'module_path', 'forks',
                      'remote_user',
                      'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                      'sftp_extra_args', 'scp_extra_args', 'become',
                      'become_method', 'become_user', 'verbosity', 'check'])


class AnsibleRunner(object):
    def __init__(self, remote_user='root', password=None, forks=100,
                 ssh_common_args=None):
        super(AnsibleRunner, self).__init__()

        module_path = utils.resolve_relative_path(
            'os_failures/ansible/modules')
        self.options = Options(
            connection='smart', password=password, module_path=module_path,
            forks=forks, remote_user=remote_user, private_key_file=None,
            ssh_common_args=ssh_common_args, ssh_extra_args=None, sftp_extra_args=None,
            scp_extra_args=None, become=None, become_method='sudo',
            become_user='root', verbosity=100, check=False)

    def _run_play(self, play_source):
        LOG.debug('Running play: %s', play_source)

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

        _log_result(storage)

        return storage

    def run(self, playbook):
        result = []

        for play_source in playbook:
            play_source['gather_facts'] = 'no'

            result += self._run_play(play_source)

        return result

    def execute(self, hosts, task):
        task_play = {'hosts': hosts, 'tasks': [task]}
        return self.run([task_play])
