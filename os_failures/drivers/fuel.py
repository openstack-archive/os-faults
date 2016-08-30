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
import json
import logging
import random
import six

from os_failures.ansible import executor
from os_failures.api import cloud_management
from os_failures.api import node_collection
from os_failures.api import service


SERVICE_CMD = {
    'mysql': 'bash -c "netstat -tap | grep \'.*LISTEN.*mysqld\'"',
    'rabbitmq': 'bash -c "rabbitmqctl status | grep \'pid,\'"',
    'nova-api': 'bash -c "ps ax | grep \'nova-api\'"',
    'glance-api': 'bash -c "ps ax | grep \'glance-api\'"',
    'keystone': 'bash -c "ps ax | grep \'keystone-main\'"'
}

class FuelNodeCollection(node_collection.NodeCollection):
    def __init__(self, cloud_management=None, power_management=None,
                 hosts=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self.hosts = hosts

    def __repr__(self):
        return ('FuelNodeCollection(%s)' %
                [dict(ip=h['ip'], mac=h['mac']) for h in self.hosts])

    def iterate_hosts(self):
        for host in self.hosts:
            try:
                yield host
            except GeneratorExit:
                break

    def filter(self, role):
        hosts = [h for h in self.hosts if role in h['roles']]
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=hosts)

    def filter_by_service(self, service_name):
        cmd = SERVICE_CMD[service_name]
        ips = [n['ip'] for n in self.hosts]
        results = self.cloud_management.execute_on_cloud(ips, {'command': cmd}, False)
        success_ips = [r.host for r in results if r.status == executor.STATUS_OK]
        hosts = [h for h in self.hosts if h['ip'] in success_ips]
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=hosts)

    def pick(self):
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=[random.choice(self.hosts)])

    def reboot(self):
        raise NotImplementedError
        task = {
            'command': 'ps aux'
        }
        ips = [n['ip'] for n in self.hosts]
        self.cloud_management.execute_on_cloud(ips, task)

    def oom(self):
        raise NotImplementedError
        logging.info('Enforce nodes to run out of memory: %s', self)

    def poweroff(self):
        self.power_management.poweroff([n['mac'] for n in self.hosts])

    def poweron(self):
        self.power_management.poweron([n['mac'] for n in self.hosts])

    def reset(self):
        logging.info('Reset nodes: %s', self)
        self.power_management.reset([n['mac'] for n in self.hosts])

    def enable_network(self, network_name):
        logging.info('Enable network: %s on nodes: %s', network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'up',
        }}
        ips = [n['ip'] for n in self.hosts]
        self.cloud_management.execute_on_cloud(ips, task)

    def disable_network(self, network_name):
        logging.info('Disable network: %s on nodes: %s', network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'down',
        }}
        ips = [n['ip'] for n in self.hosts]
        self.cloud_management.execute_on_cloud(ips, task)


@six.add_metaclass(abc.ABCMeta)
class FuelService(service.Service):

    def __init__(self, cloud_management=None, power_management=None):
        self.cloud_management = cloud_management
        self.power_management = power_management

    def __repr__(self):
        return str(type(self))

    def _get_nodes(self, role):
        nodes = self.cloud_management.get_nodes()
        return nodes.filter(role=role)

    @staticmethod
    def get_nodes_ips(nodes):
        return [host['ip'] for host in nodes.iterate_hosts()]


class KeystoneService(FuelService):
    def get_nodes(self):
        return self._get_nodes(role='controller')

    def restart(self, nodes=None):
        nodes = nodes or self._get_nodes(role='controller')
        ips = self.get_nodes_ips(nodes)

        task = {
            'command': 'service apache2 restart'
        }
        exec_res = self.cloud_management.execute_on_cloud(ips, task)
        logging.info('Restart the service, result: %s', exec_res)


SERVICE_NAME_TO_CLASS = {
    'keystone-api': KeystoneService,
}


class FuelManagement(cloud_management.CloudManagement):
    def __init__(self, cloud_management_params):
        super(FuelManagement, self).__init__()

        self.master_node_address = cloud_management_params['address']
        self.username = cloud_management_params['username']

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username)

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username,
            ssh_common_args='-o ProxyCommand="ssh -W %%h:%%p %s@%s"' %
                            (self.username, self.master_node_address))

        self.cached_cloud_hosts = None
        self.fqdn_to_hosts = dict()

    def verify(self):
        """Verify connection to the cloud."""
        hosts = self._get_cloud_hosts()
        logging.debug('Cloud hosts: %s', hosts)

        task = {'command': 'hostname'}
        host_addrs = [n['ip'] for n in hosts]
        logging.debug('Cloud nodes hostnames: %s',
                      self.execute_on_cloud(host_addrs, task))

        logging.info('Connected to cloud successfully')

    def _get_cloud_hosts(self):
        if not self.cached_cloud_hosts:
            task = {'command': 'fuel2 node list -f json'}
            r = self.execute_on_master_node(task)
            self.cached_cloud_hosts = json.loads(r[0].payload['stdout'])
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
        :return: Ansible execution result (list of records)
        """
        if raise_on_error:
            return self.cloud_executor.execute(hosts, task)
        else:
            return self.cloud_executor.execute(hosts, task, [])

    def _retrieve_hosts_fqdn(self):
        for host in self._get_cloud_hosts():
            task = {'command': 'fuel2 node show %s -f json' % host['id']}
            r = self.execute_on_master_node(task)
            host_ext = json.loads(r[0].payload['stdout'])
            self.fqdn_to_hosts[host_ext['fqdn']] = host_ext

    def get_nodes(self, fqdns=None):
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that has specified FQDNs.
        :param fqdns: list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """
        if not fqdns:
            # return all hosts
            hosts = self._get_cloud_hosts()
            return FuelNodeCollection(cloud_management=self,
                                      power_management=self.power_management,
                                      hosts=hosts)
        # return only specified
        if not self.fqdn_to_hosts:
            self._retrieve_hosts_fqdn()

        hosts = [self.fqdn_to_hosts[k] for k in fqdns]
        return FuelNodeCollection(cloud_management=self,
                                  power_management=self.power_management,
                                  hosts=hosts)

    def get_service(self, name):
        """Get service with specified name

        :param name: name of the serives
        :return: Service
        """
        if name in SERVICE_NAME_TO_CLASS:
            klazz = SERVICE_NAME_TO_CLASS[name]
            return klazz(cloud_management=self,
                         power_management=self.power_management)
