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

from os_faults.drivers.services import process
from os_faults.drivers import shared_schemas


class SystemService(process.ServiceAsProcess):
    """System service

    This is universal driver for any system services supported by Ansible
    (e.g. systemd, upstart). Please refer to Ansible documentation
    http://docs.ansible.com/ansible/latest/service_module.html for the
    whole list.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: system_service
            args:
              service_name: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **service_name** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)
    """
    NAME = 'system_service'
    DESCRIPTION = 'System Service (systemd, upstart, SysV, etc.)'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'service_name': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': shared_schemas.PORT_SCHEMA,
        },
        'required': ['grep', 'service_name'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(SystemService, self).__init__(*args, **kwargs)
        self.service_name = self.config['service_name']

    def start(self, nodes=None):
        task = {
            'service': {
                'name': self.service_name, 'state': 'started'
            },
            'become': 'yes',
        }
        self._run_task(nodes, task, 'Start')

    def terminate(self, nodes=None):
        task = {
            'service': {
                'name': self.service_name, 'state': 'stopped',
                'pattern': self.grep,
            },
            'become': 'yes',
        }
        self._run_task(nodes, task, 'Terminate')

    def restart(self, nodes=None):
        task = {
            'service': {
                'name': self.service_name, 'state': 'restarted'
            },
            'become': 'yes',
        }
        self._run_task(nodes, task, 'Restart')
