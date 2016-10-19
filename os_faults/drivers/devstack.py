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
from os_faults.api import cloud_management
from os_faults.api import node_collection
from os_faults.common import service

LOG = logging.getLogger(__name__)


class DevStackNode(node_collection.NodeCollection):

    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


class KeystoneService(service.ServiceAsProcess):
    SERVICE_NAME = 'keystone'
    GREP = '[k]eystone-'
    RESTART_CMD = 'service apache2 restart'


class MySQLService(service.ServiceAsProcess):
    SERVICE_NAME = 'mysql'
    GREP = '[m]ysqld'
    RESTART_CMD = 'service mysql restart'
    PORT = ('tcp', 3307)


class RabbitMQService(service.ServiceAsProcess):
    SERVICE_NAME = 'rabbitmq'
    GREP = '[r]abbitmq-server'
    RESTART_CMD = 'service rabbitmq-server restart'


class NovaAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-api'
    GREP = '[n]ova-api'
    RESTART_CMD = ("screen -S stack -p n-api -X "
                   "stuff $'\\003'$'\\033[A'$(printf \\\\r)")


class GlanceAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'glance-api'
    GREP = '[g]lance-api'
    RESTART_CMD = ("screen -S stack -p g-api -X "
                   "stuff $'\\003'$'\\033[A'$(printf \\\\r)")


class NovaComputeService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-compute'
    GREP = '[n]ova-compute'
    RESTART_CMD = ("screen -S stack -p n-cpu -X "
                   "stuff $'\\003'$'\\033[A'$(printf \\\\r)")


class NovaSchedulerService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-scheduler'
    GREP = '[n]ova-scheduler'
    RESTART_CMD = ("screen -S stack -p n-sch -X "
                   "stuff $'\\003'$'\\033[A'$(printf \\\\r)")


class DevStackManagement(cloud_management.CloudManagement):
    NAME = 'devstack'
    DESCRIPTION = 'Single node DevStack management driver'
    NODE_CLS = DevStackNode
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'mysql': MySQLService,
        'rabbitmq': RabbitMQService,
        'nova-api': NovaAPIService,
        'glance-api': GlanceAPIService,
        'nova-compute': NovaComputeService,
        'nova-scheduler': NovaSchedulerService,
    }
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

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            become=True)
        self.host = None

    def verify(self):
        """Verify connection to the cloud."""
        task = {'shell': 'screen -ls | grep stack'}
        hostname = self.execute_on_cloud(
            [self.address], task)[0].payload['stdout']
        LOG.debug('DevStack hostname: %s', hostname)
        LOG.info('Connected to cloud successfully')

    def execute_on_cloud(self, hosts, task, raise_on_error=True):
        """Execute task on specified hosts within the cloud.

        :param hosts: List of host FQDNs
        :param task: Ansible task
        :param raise_on_error: throw exception in case of error
        :return: Ansible execution result (list of records)
        """
        if raise_on_error:
            return self.cloud_executor.execute(hosts, task)
        else:
            return self.cloud_executor.execute(hosts, task, [])

    def get_nodes(self, fqdns=None):
        if self.host is None:
            task = {'command': 'cat /sys/class/net/eth0/address'}
            mac = self.execute_on_cloud(
                [self.address], task)[0].payload['stdout']
            # TODO(astudenov): support fqdn
            self.host = node_collection.Host(ip=self.address, mac=mac,
                                             fqdn='')

        return self.NODE_CLS(cloud_management=self,
                             power_management=self.power_management,
                             hosts=[self.host])
