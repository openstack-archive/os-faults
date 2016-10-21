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

import yaml

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.common import service

LOG = logging.getLogger(__name__)


class TCPCloudNodeCollection(node_collection.NodeCollection):

    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


SALT_RESTART = ('salt-call --local --retcode-passthrough '
                'service.restart {service}')


class KeystoneService(service.ServiceAsProcess):
    SERVICE_NAME = 'keystone'
    GREP = '[k]eystone-all'
    RESTART_CMD = SALT_RESTART.format(service='keystone')


class MemcachedService(service.ServiceAsProcess):
    SERVICE_NAME = 'memcached'
    GREP = '[m]emcached'
    RESTART_CMD = SALT_RESTART.format(service='memcached')


class MySQLService(service.ServiceAsProcess):
    SERVICE_NAME = 'mysql'
    GREP = '[m]ysqld'
    RESTART_CMD = SALT_RESTART.format(service='mysql')
    PORT = ('tcp', 3307)


class RabbitMQService(service.ServiceAsProcess):
    SERVICE_NAME = 'rabbitmq'
    GREP = 'beam\.smp .*rabbitmq_server'
    RESTART_CMD = SALT_RESTART.format(service='rabbitmq-server')


class NovaAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-api'
    GREP = '[n]ova-api'
    RESTART_CMD = SALT_RESTART.format(service='nova-api')


class GlanceAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'glance-api'
    GREP = '[g]lance-api'
    RESTART_CMD = SALT_RESTART.format(service='glance-api')


class NovaComputeService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-compute'
    GREP = '[n]ova-compute'
    RESTART_CMD = SALT_RESTART.format(service='nova-compute')


class NovaSchedulerService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-scheduler'
    GREP = '[n]ova-scheduler'
    RESTART_CMD = SALT_RESTART.format(service='nova-scheduler')


class HeatAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'heat-api'
    GREP = '[h]eat-api '
    RESTART_CMD = SALT_RESTART.format(service='heat-api')


class HeatEngineService(service.ServiceAsProcess):
    SERVICE_NAME = 'heat-engine'
    GREP = '[h]eat-engine'
    RESTART_CMD = SALT_RESTART.format(service='heat-engine')


class TCPCloudManagement(cloud_management.CloudManagement):
    NAME = 'tcpcloud'
    DESCRIPTION = 'TCPCloud management driver'
    NODE_CLS = TCPCloudNodeCollection
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'memcached': MemcachedService,
        'mysql': MySQLService,
        'rabbitmq': RabbitMQService,
        'nova-api': NovaAPIService,
        'glance-api': GlanceAPIService,
        'nova-compute': NovaComputeService,
        'nova-scheduler': NovaSchedulerService,
        'heat-api': HeatAPIService,
        'heat-engine': HeatEngineService,
    }
    SUPPORTED_SERVICES = list(SERVICE_NAME_TO_CLASS.keys())
    SUPPORTED_NETWORKS = []
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
        super(TCPCloudManagement, self).__init__()

        self.master_node_address = cloud_management_params['address']
        self.username = cloud_management_params['username']
        self.private_key_file = cloud_management_params.get('private_key_file')

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file)

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            jump_host=self.master_node_address)

        self.cached_cloud_hosts = list()
        self.fqdn_to_hosts = dict()

    def verify(self):
        """Verify connection to the cloud."""
        hosts = self._get_cloud_hosts()
        LOG.debug('Cloud nodes: %s', hosts)

        task = {'command': 'hostname'}
        host_addrs = [host.ip for host in hosts]
        task_result = self.execute_on_cloud(host_addrs, task)
        LOG.debug('Hostnames of cloud nodes: %s',
                  [r.payload['stdout'] for r in task_result])

        LOG.info('Connected to cloud successfully!')

    def _get_cloud_hosts(self):
        if not self.cached_cloud_hosts:
            cmd = "salt -E '(ctl*|cmp*)' network.interfaces --out=yaml"
            result = self.execute_on_master_node({'command': cmd})
            stdout = result[0].payload['stdout']
            for fqdn, net_data in yaml.load(stdout).items():
                host = node_collection.Host(
                    ip=net_data['eth0']['inet'][0]['address'],
                    mac=net_data['eth0']['hwaddr'],
                    fqdn=fqdn)
                self.cached_cloud_hosts.append(host)
                self.fqdn_to_hosts[host.fqdn] = host
            self.cached_cloud_hosts = sorted(self.cached_cloud_hosts)

        return self.cached_cloud_hosts

    def execute_on_master_node(self, task):
        """Execute task on salt master node.

        :param task: Ansible task
        :return: Ansible execution result (list of records)
        """
        return self.master_node_executor.execute(
            [self.master_node_address], task)

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
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that were specified by FQDNs.
        :param fqdns: list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """
        hosts = self._get_cloud_hosts()

        if fqdns:
            LOG.debug('Trying to find nodes with FQDNs: %s', fqdns)
            hosts = []
            for fqdn in fqdns:
                if fqdn in self.fqdn_to_hosts:
                    hosts.append(self.fqdn_to_hosts[fqdn])
                else:
                    raise error.NodeCollectionError(
                        'Node with FQDN \'%s\' not found!' % fqdn)
            LOG.debug('The following nodes were found: %s', hosts)

        return self.NODE_CLS(cloud_management=self,
                             power_management=self.power_management,
                             hosts=hosts)
