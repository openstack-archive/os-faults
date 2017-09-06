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


class SystemdService(process.ServiceAsProcess):
    """Systemd service.

    Service as Systemd unit and can be controlled by `systemctl` CLI tool.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: systemd_service
            args:
              systemd_service: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **systemd_service** - name of a service in systemd
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)

    """
    NAME = 'systemd_service'
    DESCRIPTION = 'Service in Systemd'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'systemd_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': process.PORT_SCHEMA,
            'start_cmd': {'type': 'string'},
            'terminate_cmd': {'type': 'string'},
            'restart_cmd': {'type': 'string'},
        },
        'required': ['grep', 'systemd_service'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(SystemdService, self).__init__(*args, **kwargs)
        self.systemd_service = self.config['systemd_service']

        self.restart_cmd = 'sudo systemctl restart {}'.format(
            self.systemd_service)
        self.terminate_cmd = 'sudo systemctl stop {}'.format(
            self.systemd_service)
        self.start_cmd = 'sudo systemctl start {}'.format(
            self.systemd_service)
