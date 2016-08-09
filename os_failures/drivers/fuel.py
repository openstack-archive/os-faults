import json
import random

from os_failures.ansible import runner
from os_failures.api import cloud_manager
from os_failures.api import node_collection
from os_failures.api import service


ROLE_MAPPING = {
    'keystone-api': 'controller',
}


class FuelNodeCollection(node_collection.NodeCollection):
    def __init__(self, cloud_management=None, power_management=None,
                 hosts=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self.hosts = hosts

    def reboot(self):
        task = {
            'command': 'ps aux'
        }
        ips = [n['ip'] for n in self.hosts]
        self.cloud_management.execute_on_cloud(ips, task)

    def oom(self):
        print('OOM!')

    def pick(self):
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=[random.choice(self.hosts)])

    def poweroff(self):
        self.power_management.poweroff([n['mac'] for n in self.hosts])


class FuelService(service.Service):

    def __init__(self, cloud_management=None, power_management=None,
                 name=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self.name = name

    def _get_hosts(self):
        cloud_hosts = self.cloud_management.get_cloud_hosts()
        return [n for n in cloud_hosts if 'controller' in n['roles']]

    def get_nodes(self):
        if self.name == 'keystone-api':
            hosts = self._get_hosts()
            return FuelNodeCollection(cloud_management=self.cloud_management,
                                      power_management=self.power_management,
                                      hosts=hosts)

    def stop(self):
        if self.name == 'keystone-api':
            task = {
                'command': 'service apache2 restart'
            }
            ips = [n['ip'] for n in self._get_hosts()]
            print(self.cloud_management.execute_on_cloud(ips, task))


class FuelManagement(cloud_manager.CloudManagement):
    def __init__(self, params):
        super(FuelManagement, self).__init__()

        self.master_node_address = params['master_node_host']
        self.username = params['username']
        self.password = params['password']

        self.master_node_executor = runner.AnsibleRunner(
            remote_user=self.username)

        hosts = self.get_cloud_hosts()
        print(hosts)

        self.cloud_executor = runner.AnsibleRunner(
            remote_user=self.username,
            ssh_common_args='-o ProxyCommand="ssh -W %%h:%%p %s@%s"' %
                            (self.username, self.master_node_address))
        task = {'command': 'hostname'}
        host_addrs = [n['ip'] for n in hosts]
        print(self.execute_on_cloud(host_addrs, task))

    def get_cloud_hosts(self):
        task = {'command': 'fuel2 node list -f json'}
        r = self.execute_on_master_node(task)
        return json.loads(r[0]['payload']['stdout'])

    def execute_on_master_node(self, task):
        return self.master_node_executor.execute([self.master_node_address], task)

    def execute_on_cloud(self, hosts, task):
        return self.cloud_executor.execute(hosts, task)

    def get_nodes(self):
        hosts = self.get_cloud_hosts()
        return FuelNodeCollection(cloud_management=self,
                                  power_management=self.power_management,
                                  hosts=hosts)

    def get_service(self, name):
        return FuelService(cloud_management=self,
                           power_management=self.power_management,
                           name=name)
