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

from os_failures.ansible import executor
from os_failures.api import power_management


class KVM(power_management.PowerManagement):
    def __init__(self, params):
        self.host = params['address']
        self.username = params.get('username')
        self.password = params.get('password')

        self.executor = executor.AnsibleRunner(remote_user=self.username)

    def poweroff(self, hosts):
        print('Power off hosts %s' % hosts)
