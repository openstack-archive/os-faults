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

import json
import logging

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.common import service

LOG = logging.getLogger(__name__)


class FuelNodeCollection(node_collection.NodeCollection):

    def connect(self, network_name):
        LOG.info("Connect network '%s' on nodes: %s", network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'up',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)

    def disconnect(self, network_name):
        LOG.info("Disconnect network '%s' on nodes: %s",
                 network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'down',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)


class KeystoneService(service.ServiceAsProcess):
    SERVICE_NAME = 'keystone'
    GREP = '[k]eystone'
    RESTART_CMD = 'service apache2 restart'


class MemcachedService(service.ServiceAsProcess):
    SERVICE_NAME = 'memcached'
    GREP = '[m]emcached'
    RESTART_CMD = 'service memcached restart'


class MySQLService(service.ServiceAsProcess):
    SERVICE_NAME = 'mysql'
    GREP = '[m]ysqld'
    PORT = ('tcp', 3307)


class RabbitMQService(service.ServiceAsProcess):
    SERVICE_NAME = 'rabbitmq'
    GREP = '[r]abbit tcp_listeners'
    RESTART_CMD = 'service rabbitmq-server restart'


class NovaAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-api'
    GREP = '[n]ova-api'
    RESTART_CMD = 'service nova-api restart'


class GlanceAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'glance-api'
    GREP = '[g]lance-api'
    RESTART_CMD = 'service glance-api restart'


class NovaComputeService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-compute'
    GREP = '[n]ova-compute'
    RESTART_CMD = 'service nova-compute restart'


class NovaSchedulerService(service.ServiceAsProcess):
    SERVICE_NAME = 'nova-scheduler'
    GREP = '[n]ova-scheduler'
    RESTART_CMD = 'service nova-scheduler restart'


class NeutronOpenvswitchAgentService(service.ServiceAsProcess):
    SERVICE_NAME = 'neutron-openvswitch-agent'
    GREP = '[n]eutron-openvswitch-agent'
    RESTART_CMD = ('bash -c "if pcs resource show neutron-openvswitch-agent; '
                   'then pcs resource restart neutron-openvswitch-agent; '
                   'else service neutron-openvswitch-agent restart; fi"')


class NeutronL3AgentService(service.ServiceAsProcess):
    SERVICE_NAME = 'neutron-l3-agent'
    GREP = '[n]eutron-l3-agent'
    RESTART_CMD = ('bash -c "if pcs resource show neutron-l3-agent; '
                   'then pcs resource restart neutron-l3-agent; '
                   'else service neutron-l3-agent restart; fi"')


class HeatAPIService(service.ServiceAsProcess):
    SERVICE_NAME = 'heat-api'
    GREP = '[h]eat-api'
    RESTART_CMD = 'service heat-api restart'


class HeatEngineService(service.ServiceAsProcess):
    SERVICE_NAME = 'heat-engine'
    GREP = '[h]eat-engine'
    RESTART_CMD = 'pcs resource restart p_heat-engine'


class FuelManagement(cloud_management.CloudManagement):
    NAME = 'fuel'
    DESCRIPTION = 'Fuel 9.x cloud management driver'
    NODE_CLS = FuelNodeCollection
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'memcached': MemcachedService,
        'mysql': MySQLService,
        'rabbitmq': RabbitMQService,
        'nova-api': NovaAPIService,
        'glance-api': GlanceAPIService,
        'nova-compute': NovaComputeService,
        'nova-scheduler': NovaSchedulerService,
        'neutron-openvswitch-agent': NeutronOpenvswitchAgentService,
        'neutron-l3-agent': NeutronL3AgentService,
        'heat-api': HeatAPIService,
        'heat-engine': HeatEngineService,
    }
    SUPPORTED_SERVICES = list(SERVICE_NAME_TO_CLASS.keys())
    SUPPORTED_NETWORKS = ['management', 'private', 'public', 'storage']
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
        super(FuelManagement, self).__init__()

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
            task = {'command': 'fuel node --json'}
            result = self.execute_on_master_node(task)
            for r in json.loads(result[0].payload['stdout']):
                host = node_collection.Host(ip=r['ip'], mac=r['mac'],
                                            fqdn=r['fqdn'])
                self.cached_cloud_hosts.append(host)
                self.fqdn_to_hosts[host.fqdn] = host

        return self.cached_cloud_hosts

    def execute_on_master_node(self, task):
        """Execute task on Fuel master node.

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
            hosts = list()
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
