from os_failures.ansible import runner
from os_failures.api import client
from os_failures.api import cloud


ROLE_MAPPING = {
    'keystone-api': 'controller',
}


class FuelCloud(cloud.Cloud):

    def __init__(self, client):
        self.client = client

    def get_nodes(self, role):
        fuel_role = ROLE_MAPPING[role]


class FuelClient(client.Client):
    def __init__(self, params):
        self.ip = params['ip']
        self.username = params['username']
        self.password = params['password']

        self.ansible_executor = runner.AnsibleRunner(
            remote_user=self.username)

        task = {'command': 'fuel2 node list -f json'}
        nodes = self.ansible_executor.execute([self.ip], task)
        print(nodes)

        self.ansible_executor = runner.AnsibleRunner(
            remote_user=self.username,
            ssh_common_args='-o ProxyCommand="ssh -W %h:%p root@172.18.171.149"')
        task = {'command': 'hostname'}
        print(self.ansible_executor.execute(['10.20.0.3', '10.20.0.4'], task))

    def get_cloud(self):
        return FuelCloud(self)
