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

import logging
import signal

from os_faults.ansible import executor
from os_faults.api import error
from os_faults.api import service
from os_faults import utils

LOG = logging.getLogger(__name__)

PORT_SCHEMA = {
    'type': 'array',
    'items': [
        {'enum': ['tcp', 'udp']},
        {'type': 'integer', 'minimum': 0, 'maximum': 65535},
    ],
    'minItems': 2,
    'maxItems': 2,
}


class ServiceAsProcess(service.Service):
    """Service as process

    "process" is a basic service driver that uses `ps` and `kill` in
    actions like kill / freeze / unfreeze. Commands for start / restart
    / terminate should be specified in configuration, otherwise
    the commands will fail at runtime.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: process
            args:
              grep: my_app
              restart_cmd: /bin/my_app --restart
              terminate_cmd: /bin/stop_my_app
              start_cmd: /bin/my_app
              port: ['tcp', 4242]

    parameters:

    - **grep** - regexp for grep to find process PID
    - **restart_cmd** - command to restart service (optional)
    - **terminate_cmd** - command to terminate service (optional)
    - **start_cmd** - command to start service (optional)
    - **port** - tuple with two values - potocol, port number (optional)

    """

    NAME = 'process'
    DESCRIPTION = 'Service as process'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'grep': {'type': 'string'},
            'start_cmd': {'type': 'string'},
            'terminate_cmd': {'type': 'string'},
            'restart_cmd': {'type': 'string'},
            'port': PORT_SCHEMA,
        },
        'required': ['grep'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(ServiceAsProcess, self).__init__(*args, **kwargs)
        self.grep = self.config['grep']
        self.start_cmd = self.config.get('start_cmd')
        self.terminate_cmd = self.config.get('terminate_cmd')
        self.restart_cmd = self.config.get('restart_cmd')
        self.port = self.config.get('port')

    def _run_task(self, task, nodes):
        ips = nodes.get_ips()
        if not ips:
            raise error.ServiceError('Node collection is empty')

        results = self.cloud_management.execute_on_cloud(ips, task)
        err = False
        for result in results:
            if result.status != executor.STATUS_OK:
                LOG.error(
                    'Task {} failed on node {}'.format(task, result.host))
                err = True
        if err:
            raise error.ServiceError('Task failed on some nodes')
        return results

    def get_nodes(self):
        nodes = self.cloud_management.get_nodes()
        ips = nodes.get_ips()
        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(self.grep)
        results = self.cloud_management.execute_on_cloud(
            ips, {'command': cmd}, False)
        success_ips = [r.host for r in results
                       if r.status == executor.STATUS_OK]
        hosts = [h for h in nodes.hosts if h.ip in success_ips]
        return self.node_cls(cloud_management=self.cloud_management,
                             hosts=hosts)

    @utils.require_variables('restart_cmd')
    def restart(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Restart '%s' service on nodes: %s", self.service_name,
                 nodes.get_ips())
        self._run_task({'shell': self.restart_cmd}, nodes)

    @utils.require_variables('terminate_cmd')
    def terminate(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Terminate '%s' service on nodes: %s", self.service_name,
                 nodes.get_ips())
        self._run_task({'shell': self.terminate_cmd}, nodes)

    @utils.require_variables('start_cmd')
    def start(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Start '%s' service on nodes: %s", self.service_name,
                 nodes.get_ips())
        self._run_task({'shell': self.start_cmd}, nodes)

    def kill(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Kill '%s' service on nodes: %s", self.service_name,
                 nodes.get_ips())
        cmd = {'kill': {'grep': self.grep, 'sig': signal.SIGKILL}}
        self._run_task(cmd, nodes)

    def freeze(self, nodes=None, sec=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        if sec:
            cmd = {'freeze': {'grep': self.grep, 'sec': sec}}
        else:
            cmd = {'kill': {'grep': self.grep, 'sig': signal.SIGSTOP}}
        LOG.info("Freeze '%s' service %son nodes: %s", self.service_name,
                 ('for %s sec ' % sec) if sec else '', nodes.get_ips())
        self._run_task(cmd, nodes)

    def unfreeze(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Unfreeze '%s' service on nodes: %s", self.service_name,
                 nodes.get_ips())
        cmd = {'kill': {'grep': self.grep, 'sig': signal.SIGCONT}}
        self._run_task(cmd, nodes)

    @utils.require_variables('port')
    def plug(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Open port %d for '%s' service on nodes: %s",
                 self.port[1], self.service_name, nodes.get_ips())
        self._run_task({'iptables': {'protocol': self.port[0],
                                     'port': self.port[1],
                                     'action': 'unblock',
                                     'service': self.service_name}}, nodes)

    @utils.require_variables('port')
    def unplug(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Close port %d for '%s' service on nodes: %s",
                 self.port[1], self.service_name, nodes.get_ips())
        self._run_task({'iptables': {'protocol': self.port[0],
                                     'port': self.port[1],
                                     'action': 'block',
                                     'service': self.service_name}}, nodes)


class LinuxService(ServiceAsProcess):
    """Linux service

    Service that is defined in init.d and can be controled by `service`
    CLI tool.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: linux_service
            args:
              linux_service: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **linux_service** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - potocol, port number (optional)

    """
    NAME = 'linux_service'
    DESCRIPTION = 'Service in init.d'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'linux_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': PORT_SCHEMA,
        },
        'required': ['grep', 'linux_service'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(LinuxService, self).__init__(*args, **kwargs)
        self.linux_service = self.config['linux_service']

        self.restart_cmd = 'service {} restart'.format(self.linux_service)
        self.terminate_cmd = 'service {} stop'.format(self.linux_service)
        self.start_cmd = 'service {} start'.format(self.linux_service)
