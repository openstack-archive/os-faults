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


class ServiceAsProcess(service.Service):

    def __init__(self, node_cls, cloud_management=None):
        self.node_cls = node_cls
        self.cloud_management = cloud_management

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
        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(self.GREP)
        results = self.cloud_management.execute_on_cloud(
            ips, {'command': cmd}, False)
        success_ips = [r.host for r in results
                       if r.status == executor.STATUS_OK]
        hosts = [h for h in nodes.hosts if h.ip in success_ips]
        return self.node_cls(cloud_management=self.cloud_management,
                             hosts=hosts)

    @utils.require_variables('RESTART_CMD', 'SERVICE_NAME')
    def restart(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Restart '%s' service on nodes: %s", self.SERVICE_NAME,
                 nodes.get_ips())
        self._run_task({'shell': self.RESTART_CMD}, nodes)

    @utils.require_variables('TERMINATE_CMD', 'SERVICE_NAME')
    def terminate(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Terminate '%s' service on nodes: %s", self.SERVICE_NAME,
                 nodes.get_ips())
        self._run_task({'shell': self.TERMINATE_CMD}, nodes)

    @utils.require_variables('START_CMD', 'SERVICE_NAME')
    def start(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Start '%s' service on nodes: %s", self.SERVICE_NAME,
                 nodes.get_ips())
        self._run_task({'shell': self.START_CMD}, nodes)

    @utils.require_variables('GREP', 'SERVICE_NAME')
    def kill(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Kill '%s' service on nodes: %s", self.SERVICE_NAME,
                 nodes.get_ips())
        cmd = {'kill': {'grep': self.GREP, 'sig': signal.SIGKILL}}
        self._run_task(cmd, nodes)

    @utils.require_variables('GREP', 'SERVICE_NAME')
    def freeze(self, nodes=None, sec=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        if sec:
            cmd = {'freeze': {'grep': self.GREP, 'sec': sec}}
        else:
            cmd = {'kill': {'grep': self.GREP, 'sig': signal.SIGSTOP}}
        LOG.info("Freeze '%s' service %son nodes: %s", self.SERVICE_NAME,
                 ('for %s sec ' % sec) if sec else '', nodes.get_ips())
        self._run_task(cmd, nodes)

    @utils.require_variables('GREP', 'SERVICE_NAME')
    def unfreeze(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Unfreeze '%s' service on nodes: %s", self.SERVICE_NAME,
                 nodes.get_ips())
        cmd = {'kill': {'grep': self.GREP, 'sig': signal.SIGCONT}}
        self._run_task(cmd, nodes)

    @utils.require_variables('PORT', 'SERVICE_NAME')
    def plug(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Open port %d for '%s' service on nodes: %s",
                 self.PORT[1], self.SERVICE_NAME, nodes.get_ips())
        self._run_task({'iptables': {'protocol': self.PORT[0],
                                     'port': self.PORT[1],
                                     'action': 'unblock',
                                     'service': self.SERVICE_NAME}}, nodes)

    @utils.require_variables('PORT', 'SERVICE_NAME')
    def unplug(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        LOG.info("Close port %d for '%s' service on nodes: %s",
                 self.PORT[1], self.SERVICE_NAME, nodes.get_ips())
        self._run_task({'iptables': {'protocol': self.PORT[0],
                                     'port': self.PORT[1],
                                     'action': 'block',
                                     'service': self.SERVICE_NAME}}, nodes)


class LinuxService(ServiceAsProcess):

    @utils.require_variables('LINUX_SERVICE')
    def __init__(self, *args, **kwargs):
        super(LinuxService, self).__init__(*args, **kwargs)

        self.RESTART_CMD = 'service {} restart'.format(self.LINUX_SERVICE)
        self.TERMINATE_CMD = 'service {} stop'.format(self.LINUX_SERVICE)
        self.START_CMD = 'service {} start'.format(self.LINUX_SERVICE)
