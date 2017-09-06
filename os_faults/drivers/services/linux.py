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


class LinuxService(process.ServiceAsProcess):
    """Linux service

    Service that is defined in init.d and can be controlled by `service`
    CLI tool.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: linux_service
            args:
              linux_service: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **linux_service** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)

    """
    NAME = 'linux_service'
    DESCRIPTION = 'Service in init.d'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'linux_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': process.PORT_SCHEMA,
        },
        'required': ['grep', 'linux_service'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(LinuxService, self).__init__(*args, **kwargs)
        self.linux_service = self.config['linux_service']

        self.restart_cmd = 'service {} restart'.format(self.linux_service)
        self.terminate_cmd = 'service {} stop'.format(self.linux_service)
        self.start_cmd = 'service {} start'.format(self.linux_service)
