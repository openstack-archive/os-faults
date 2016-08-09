import json

from os_failures.ansible import runner
from os_failures.api import client
from os_failures.api import node
from os_failures.api import service_collection


ROLE_MAPPING = {
    'keystone-api': 'controller',
}


class FuelNodes(node.NodeCollection):
    def __init__(self, client=None, collection=None):
        self.client = client

    def reboot(self):
        print('Reboot!')

    def oom(self):
        print('OOM!')

    def kill_process(self):
        print('PS')


class FuelService(service_collection.ServiceCollection):

    def __init__(self, client=None, name=None):
        self.client = client
        self.name = name

    def get_nodes(self):
        if self.name == 'keystone-api':
            nodes = self.client.get_fuel_nodes()
            controllers = [n for n in nodes if 'controller' in n['roles']]
            return FuelNodes(client=self.client, collection=controllers)
        pass

    def stop(self):
        super(FuelService, self).stop()


class FuelClient(client.Client):
    def __init__(self, params):
        self.ip = params['ip']
        self.username = params['username']
        self.password = params['password']

        self.ansible_executor = runner.AnsibleRunner(
            remote_user=self.username)

        task = {'command': 'fuel2 node list -f json'}
        nodes_s = self.ansible_executor.execute([self.ip], task)
        nodes = json.loads(nodes_s[0]['payload']['stdout'])
        print(nodes)

        self.ansible_executor = runner.AnsibleRunner(
            remote_user=self.username,
            ssh_common_args='-o ProxyCommand="ssh -W %h:%p root@172.18.171.149"')
        task = {'command': 'hostname'}
        print(self.ansible_executor.execute(['10.20.0.3', '10.20.0.4'], task))

    def get_fuel_nodes(self):
        task = {'command': 'fuel2 node list -f json'}
        nodes_s = self.ansible_executor.execute([self.ip], task)
        nodes = json.loads(nodes_s[0]['payload']['stdout'])
        return nodes

    def get_nodes(self):
        pass

    def get_services(self, name):
        return FuelService(client=self, name=name)
