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

import logging

from os_faults.drivers.services import process

LOG = logging.getLogger(__name__)


class PcsService(process.ServiceAsProcess):
    """Service as a resource in Pacemaker

    Service that can be controlled by `pcs resource` CLI tool.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: pcs_service
            args:
              pcs_service: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **pcs_service** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)
    """

    NAME = 'pcs_service'
    DESCRIPTION = 'Service in pacemaker'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'pcs_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': process.PORT_SCHEMA,
        },
        'required': ['grep', 'pcs_service'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(PcsService, self).__init__(*args, **kwargs)
        self.pcs_service = self.config['pcs_service']

        self.restart_cmd = 'pcs resource restart {} $(hostname)'.format(
            self.pcs_service)
        self.terminate_cmd = 'pcs resource ban {} $(hostname)'.format(
            self.pcs_service)
        self.start_cmd = 'pcs resource clear {} $(hostname)'.format(
            self.pcs_service)


class PcsOrLinuxService(process.ServiceAsProcess):
    """Service as a resource in Pacemaker or Linux service

    Service that can be controlled by `pcs resource` CLI tool or
    linux `service` tool. This is a hybrid driver that tries to find
    service in Pacemaker and uses linux `service` if it is not found
    there.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: pcs_or_linux_service
            args:
              pcs_service: p_app
              linux_service: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **pcs_service** - name of a service in Pacemaker
    - **linux_service** - name of a service in init.d
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)
    """

    NAME = 'pcs_or_linux_service'
    DESCRIPTION = 'Service in pacemaker or init.d'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'pcs_service': {'type': 'string'},
            'linux_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': process.PORT_SCHEMA,
        },
        'required': ['grep', 'pcs_service', 'linux_service'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(PcsOrLinuxService, self).__init__(*args, **kwargs)
        self.pcs_service = self.config.get('pcs_service')
        self.linux_service = self.config.get('linux_service')

        self.restart_cmd = (
            'if pcs resource show {pcs_service}; '
            'then pcs resource restart {pcs_service} $(hostname); '
            'else service {linux_service} restart; fi').format(
                linux_service=self.linux_service,
                pcs_service=self.pcs_service)
        self.terminate_cmd = (
            'if pcs resource show {pcs_service}; '
            'then pcs resource ban {pcs_service} $(hostname); '
            'else service {linux_service} stop; fi').format(
                linux_service=self.linux_service,
                pcs_service=self.pcs_service)
        self.start_cmd = (
            'if pcs resource show {pcs_service}; '
            'then pcs resource clear {pcs_service} $(hostname); '
            'else service {linux_service} start; fi').format(
                linux_service=self.linux_service,
                pcs_service=self.pcs_service)
