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

from os_faults.ansible import executor
from os_faults.api import container
from os_faults.api import error

LOG = logging.getLogger(__name__)


class DockerContainers(container.Container):
    """Docker container

    This is docker container driver for any docker containers supported by
    Ansible. Please refer to Ansible documentation
    https://docs.ansible.com/ansible/latest/modules/docker_container_module.html
    for the whole list.

    **Example configuration:**

    .. code-block:: yaml

        containers:
          app:
            driver: docker_container
            args:
              container_name: app

    parameters:

    - **container_name** - name of the container
    """
    NAME = 'docker_container'
    DESCRIPTION = 'Docker container'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'container_name': {'type': 'string'},
        },
        'required': ['container_name'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(DockerContainers, self).__init__(*args, **kwargs)
        self.container_name = self.config['container_name']

    def _run_task(self, nodes, task, message):
        nodes = nodes if nodes is not None else self.get_nodes()
        if len(nodes) == 0:
            raise error.ContainerError(
                'Container %s is not found on any nodes' % self.container_name)

        LOG.info('%s container %s on nodes: %s',
                 message, self.container_name, nodes.get_ips())

        return self.cloud_management.execute_on_cloud(nodes.hosts, task)

    def discover_nodes(self):
        nodes = self.cloud_management.get_nodes()
        cmd = 'bash -c "docker ps | grep \'{}\'"'.format(self.container_name)
        results = self.cloud_management.execute_on_cloud(
            nodes.hosts, {'command': cmd}, False)
        success_ips = [r.host for r in results
                       if r.status == executor.STATUS_OK]
        hosts = [h for h in nodes.hosts if h.ip in success_ips]
        LOG.debug('Container %s is discovered on nodes %s',
                  self.container_name, hosts)
        return self.node_cls(cloud_management=self.cloud_management,
                             hosts=hosts)

    def start(self, nodes=None):
        task = {
            'docker_container': {
                'name': self.container_name, 'state': 'started'
            },
        }
        self._run_task(nodes, task, 'Start')

    def terminate(self, nodes=None):
        task = {
            'docker_container': {
                'name': self.container_name, 'state': 'stopped',
            },
        }
        self._run_task(nodes, task, 'Terminate')

    def restart(self, nodes=None):
        task = {
            'docker_container': {
                'name': self.container_name, 'state': 'started',
                'restart': 'yes'
            },
        }
        self._run_task(nodes, task, 'Restart')
