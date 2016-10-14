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

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import node_collection
from os_faults.api import service
from os_faults import utils

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

    def __len__(self):
        return 1

    def pick(self):
        return self

    def run_task(self, task, raise_on_error=True):
        # TODO(astudenov): refactor DevStackManagement.execute
        # to be consistent with api
        self.cloud_management.execute(self.host.ip, task)

    def reboot(self):
        task = {'command': 'reboot'}
        self.cloud_management.execute(self.host.ip, task)

    def oom(self):
        raise NotImplementedError

    def poweroff(self):
        self.power_management.poweroff([self.host.mac])

    def poweron(self):
        self.power_management.poweron([self.host.mac])

    def reset(self):
        logging.info('Reset nodes: %s', self)
        self.power_management.reset([self.host.mac])

    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


@six.add_metaclass(abc.ABCMeta)
class DevStackService(service.Service):

    def __init__(self, cloud_management=None, power_management=None):
        self.cloud_management = cloud_management
        self.power_management = power_management

    def __repr__(self):
        return str(type(self))

    def get_nodes(self):
        return self.cloud_management.get_nodes()

    @utils.require_variables('RESTART_CMD', 'SERVICE_NAME')
    def restart(self, nodes=None):
        task = {'command': self.RESTART_CMD}
        exec_res = self.cloud_management.execute(task)
        logging.info('Restart %s result: %s', self.SERVICE_NAME, exec_res)


class KeystoneService(DevStackService):
    SERVICE_NAME = 'keystone'
    RESTART_CMD = 'service apache2 restart'


SERVICE_NAME_TO_CLASS = {
    'keystone': KeystoneService,
}


class DevStackManagement(cloud_management.CloudManagement):
    NAME = 'devstack'
    DESCRIPTION = 'Single node DevStack management driver'
    SUPPORTED_SERVICES = list(SERVICE_NAME_TO_CLASS.keys())
    SUPPORTED_NETWORKS = ['all-in-one']
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'username': {'type': 'string'},
            'private_key_file': {'type': 'string'},

        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(DevStackManagement, self).__init__()

        self.address = cloud_management_params['address']
        self.username = cloud_management_params['username']
        self.private_key_file = cloud_management_params.get('private_key_file')

        self.executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            become=True)
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
