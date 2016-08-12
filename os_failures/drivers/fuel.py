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


class FuelNodeCollection(node_collection.NodeCollection):
    def __init__(self, cloud_management=None, power_management=None,
                 hosts=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self.hosts = hosts

    def __repr__(self):
        return '%s(%s)' % (type(self),
                           [(h['ip'], h['mac']) for h in self.hosts])

    def pick(self):
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=[random.choice(self.hosts)])

    def reboot(self):
        task = {
            'command': 'ps aux'
        }
        ips = [n['ip'] for n in self.hosts]
        self.cloud_management.execute_on_cloud(ips, task)

    def oom(self):
        logging.info('Enforce nodes to run out of memory: %s', self)

    def poweroff(self):
        self.power_management.poweroff([n['mac'] for n in self.hosts])

    def reset(self):
        logging.info('Reset nodes: %s', self)

    def enable_network(self, network_name):
        logging.info('Enable network: %s on nodes: %s', network_name, self)

    def disable_network(self, network_name):
        logging.info('Disable network: %s on nodes: %s', network_name, self)


@six.add_metaclass(abc.ABCMeta)
class FuelService(service.Service):

    def __init__(self, cloud_management=None, power_management=None):
        self.cloud_management = cloud_management
        self.power_management = power_management

    def _get_cloud_nodes(self, role):
        cloud_hosts = self.cloud_management.get_cloud_hosts()
        return [n for n in cloud_hosts if role in n['roles']]

    def get_cloud_nodes_ips(self, role):
        return [n['ip'] for n in self._get_cloud_nodes(role=role)]

    def get_fuel_nodes(self, role):
        hosts = self._get_cloud_nodes(role=role)
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=hosts)


class KeystoneService(FuelService):
    def get_nodes(self):
        return self.get_fuel_nodes(role='controller')

    def restart(self):
        task = {
            'command': 'service apache2 restart'
        }
        ips = self.get_cloud_nodes_ips(role='controller')
        exec_res = self.cloud_management.execute_on_cloud(ips, task)
        logging.info('Restart the service, result: %s', exec_res)


SERVICE_NAME_TO_CLASS = {
    'keystone-api': KeystoneService,
}


class FuelManagement(cloud_management.CloudManagement):
    def __init__(self, params):
        super(FuelManagement, self).__init__()

        self.master_node_address = params['address']
        self.username = params['username']

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username)

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username,
            ssh_common_args='-o ProxyCommand="ssh -W %%h:%%p %s@%s"' %
                            (self.username, self.master_node_address))

        self.cached_cloud_hosts = None
        self.fqdn_to_hosts = dict()

    def verify(self):
        hosts = self.get_cloud_hosts()
        logging.debug('Cloud hosts: %s', hosts)

        task = {'command': 'hostname'}
        host_addrs = [n['ip'] for n in hosts]
        logging.debug('Cloud nodes hostnames: %s', self.execute_on_cloud(host_addrs, task))

        logging.info('Connected to cloud successfully')

    def get_cloud_hosts(self):
        if not self.cached_cloud_hosts:
            task = {'command': 'fuel2 node list -f json'}
            r = self.execute_on_master_node(task)
            self.cached_cloud_hosts = json.loads(r[0].payload['stdout'])
        return self.cached_cloud_hosts

    def execute_on_master_node(self, task):
        return self.master_node_executor.execute(
            [self.master_node_address], task)

    def execute_on_cloud(self, hosts, task):
        return self.cloud_executor.execute(hosts, task)

    def _retrieve_hosts_fqdn(self):
        for host in self.get_cloud_hosts():
            task = {'command': 'fuel2 node show %s -f json' % host['id']}
            r = self.execute_on_master_node(task)
            host_ext = json.loads(r[0].payload['stdout'])
            self.fqdn_to_hosts[host_ext['fqdn']] = host_ext

    def get_nodes(self, fqdns=None):
        if not fqdns:
            # return all hosts
            hosts = self.get_cloud_hosts()
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
        if name in SERVICE_NAME_TO_CLASS:
            klazz = SERVICE_NAME_TO_CLASS[name]
            return klazz(cloud_management=self,
                         power_management=self.power_management)
