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

import abc
from collections import namedtuple
import logging

import six

from os_failures.ansible import executor
from os_failures.api import cloud_management
from os_failures.api import node_collection
from os_failures.api import service


HostClass = namedtuple('HostClass', ['ip', 'mac'])


class DevStackNode(node_collection.NodeCollection):
    def __init__(self, cloud_management=None, power_management=None,
                 host=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self.host = host

    def __repr__(self):
        return ('DevStackNode(%s)' %
                dict(ip=self.host.ip, mac=self.host.mac))

    def pick(self):
        return self

    def reboot(self):
        task = {
            'command': 'reboot'
        }
        self.cloud_management.execute_on_cloud(self.host.ip, task)

    def oom(self):
        logging.info('Enforce nodes to run out of memory: %s', self)

    def poweroff(self):
        self.power_management.poweroff(self.host.mac)

    def reset(self):
        logging.info('Reset nodes: %s', self)

    def enable_network(self, network_name):
        logging.info('Enable network: %s on nodes: %s', network_name, self)

    def disable_network(self, network_name):
        logging.info('Disable network: %s on nodes: %s', network_name, self)


@six.add_metaclass(abc.ABCMeta)
class DevStackService(service.Service):

    def __init__(self, cloud_management=None, power_management=None):
        self.cloud_management = cloud_management
        self.power_management = power_management

    def __repr__(self):
        return str(type(self))

    def _get_nodes(self):
        return self.cloud_management.get_nodes()


class KeystoneService(DevStackService):
    def get_nodes(self):
        return self._get_nodes()

    def restart(self, nodes=None):
        task = {
            'command': 'service apache2 restart'
        }
        exec_res = self.cloud_management.execute(task)
        logging.info('Restart the service, result: %s', exec_res)


SERVICE_NAME_TO_CLASS = {
    'keystone-api': KeystoneService,
}


class DevStackManagement(cloud_management.CloudManagement):
    def __init__(self, cloud_management_params):
        super(DevStackManagement, self).__init__()

        self.address = cloud_management_params['address']
        self.username = cloud_management_params['username']

        self.executor = executor.AnsibleRunner(remote_user=self.username)
        self.host = None

    def verify(self):
        """Verify connection to the cloud."""
        task = {'command': 'hostname'}
        hostname = self.execute(task)[0].payload['stdout']
        logging.debug('DevStack hostname: %s', hostname)
        logging.info('Connected to cloud successfully')

    def execute(self, task):
        return self.executor.execute([self.address], task)

    def get_nodes(self, fqdns=None):
        if not self.host:
            task = {'command': 'cat /sys/class/net/eth0/address'}
            mac = self.execute(task)[0].payload['stdout']
            self.host = HostClass(ip=self.address, mac=mac)

        return DevStackNode(cloud_management=self,
                            power_management=self.power_management,
                            host=self.host)

    def get_service(self, name):
        if name in SERVICE_NAME_TO_CLASS:
            klazz = SERVICE_NAME_TO_CLASS[name]
            return klazz(cloud_management=self,
                         power_management=self.power_management)
