import json
import random

from os_failures.ansible import runner
from os_failures.api import client as client_pkg
from os_failures.api import node_collection
from os_failures.api import service


ROLE_MAPPING = {
    'keystone-api': 'controller',
}


class FuelNodes(node_collection.NodeCollection):
    def __init__(self, client=None, hosts=None):
        self.client = client
        self.hosts = hosts

    def reboot(self):
        task = {
            'command': 'ps aux'
        }
        self.client.execute_on_cloud(self.hosts, task)

    def oom(self):
        print('OOM!')

    def pick(self):
        return FuelNodes(self.client, random.choice(self.hosts))

    def poweroff(self):
        super(FuelNodes, self).poweroff()


class FuelService(service.Service):

    def __init__(self, client=None, name=None):
        self.client = client
        self.name = name

    def _get_hosts(self):
        cloud_hosts = self.client.get_cloud_hosts()
        return [n['ip'] for n in cloud_hosts if 'controller' in n['roles']]

    def get_nodes(self):
        if self.name == 'keystone-api':
            hosts = self._get_hosts()
            return FuelNodes(client=self.client, hosts=hosts)

    def stop(self):
        if self.name == 'keystone-api':
            task = {
                'command': 'service apache2 restart'
            }
            print(self.client.execute_on_cloud(self._get_hosts(), task))


class FuelClient(client_pkg.Client):
    def __init__(self, params):
        self.master_node_address = params['master_node_host']
        self.username = params['username']
        self.password = params['password']

        self.master_node_executor = runner.AnsibleRunner(
            remote_user=self.username)

        print(self.get_cloud_hosts())

        self.cloud_executor = runner.AnsibleRunner(
            remote_user=self.username,
            ssh_common_args='-o ProxyCommand="ssh -W %%h:%%p %s@%s"' %
                            (self.username, self.master_node_address))
        task = {'command': 'hostname'}
        print(self.execute_on_cloud(['10.20.0.3', '10.20.0.4'], task))

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
        return FuelNodes(client=self, hosts=hosts)

    def get_service(self, name):
        return FuelService(client=self, name=name)
