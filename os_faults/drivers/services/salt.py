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

SALT_CALL = 'salt-call --local --retcode-passthrough '
SALT_RESTART = SALT_CALL + 'service.restart {service}'
SALT_TERMINATE = SALT_CALL + 'service.stop {service}'
SALT_START = SALT_CALL + 'service.start {service}'


class SaltService(process.ServiceAsProcess):
    """Salt service

    Service that can be controlled by `salt service.*` commands.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: salt_service
            args:
              salt_service: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **salt_service** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)

    """

    NAME = 'salt_service'
    DESCRIPTION = 'Service in salt'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'salt_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': process.PORT_SCHEMA,
        },
        'required': ['grep', 'salt_service'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(SaltService, self).__init__(*args, **kwargs)
        self.salt_service = self.config['salt_service']

        self.restart_cmd = SALT_RESTART.format(service=self.salt_service)
        self.terminate_cmd = SALT_TERMINATE.format(service=self.salt_service)
        self.start_cmd = SALT_START.format(service=self.salt_service)
