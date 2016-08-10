from os_failures.ansible import executor
from os_failures.api import power_management


class KVM(power_management.PowerManagement):
    def __init__(self, params):
        self.host = params['address']
        self.username = params.get('username')
        self.password = params.get('password')

        self.executor = executor.AnsibleRunner(remote_user=self.username)

    def poweroff(self, hosts):
        print('Power off hosts %s', hosts)
