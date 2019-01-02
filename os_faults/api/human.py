# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import inspect
import logging
import re

from os_faults.api import container as container_pkg
from os_faults.api import error
from os_faults.api import node_collection as node_collection_pkg
from os_faults.api import service as service_pkg
from os_faults.api import utils

LOG = logging.getLogger(__name__)

"""
Human API understands commands like these (examples):
 * restart <service> service [on (random|one|single|<fqdn> node[s])]
 * terminate <service> service [on (random|one|single|<fqdn> node[s])]
 * start <service> service [on (random|one|single|<fqdn> node[s])]
 * kill <service> service [on (random|one|single|<fqdn> node[s])]
 * plug <service> service [on (random|one|single|<fqdn> node[s])]
 * unplug <service> service [on (random|one|single|<fqdn> node[s])]
 * freeze <service> service [on (random|one|single|<fqdn> node[s])]
   [for <T> seconds]
 * unfreeze <service> service [on (random|one|single|<fqdn> node[s])]
 * reboot [random|one|single|<fqdn>] node[s] [with <service> service]
 * reset [random|one|single|<fqdn>] node[s] [with <service> service]
 * stress [cpu|memory|disk|kernel for <T> seconds] on
   [random|one|single|<fqdn>] node[s] [with <service> service]
 * disconnect <name> network on [random|one|single|<fqdn>] node[s]
   [with <service> service]
 * connect <name> network on [random|one|single|<fqdn>] node[s]
   [with <service> service]
"""


def list_actions(klazz):
    return set(m[0].replace('_', ' ') for m in inspect.getmembers(
        klazz,
        predicate=utils.is_public))

RANDOMNESS = {'one', 'random', 'some', 'single'}
ANYTHING = {'all'}
NODE_ALIASES_PATTERN = '|'.join(RANDOMNESS | ANYTHING)
SERVICE_ACTIONS = list_actions(service_pkg.Service)
SERVICE_ACTIONS_PATTERN = '|'.join(SERVICE_ACTIONS)
CONTAINER_ACTIONS = list_actions(container_pkg.Container)
CONTAINER_ACTIONS_PATTERN = '|'.join(CONTAINER_ACTIONS)
NODE_ACTIONS = list_actions(node_collection_pkg.NodeCollection)
NODE_ACTIONS_PATTERN = '|'.join(NODE_ACTIONS)

PATTERNS = [
    re.compile(r'(?P<action>%s)'
               r'\s+(?P<service>\S+)\s+service'
               r'(\s+on(\s+(?P<node>\S+))?\s+nodes?)?'
               r'(\s+for\s+(?P<duration>\d+)\s+seconds)?' %
               SERVICE_ACTIONS_PATTERN),
    re.compile(r'(?P<action>%s)'
               r'\s+(?P<container>\S+)\s+container'
               r'(\s+on(\s+(?P<node>\S+))?\s+nodes?)?'
               r'(\s+for\s+(?P<duration>\d+)\s+seconds)?' %
               CONTAINER_ACTIONS_PATTERN),
    re.compile(r'(?P<action>%s)'
               r'(\s+(?P<network>\w+)\s+network\s+on)?'
               r'(\s+(?P<target>\w+)'
               r'(\s+for\s+(?P<duration>\d+)\s+seconds)(\s+on)?)?'
               r'(\s+(?P<node>%s|\S+))?'
               r'\s+nodes?'
               r'(\s+with\s+(?P<service>\S+)\s+service)?' %
               (NODE_ACTIONS_PATTERN, NODE_ALIASES_PATTERN)),
]


def execute(destructor, command):
    command = command.lower()
    rec = None
    for pattern in PATTERNS:
        rec = re.search(pattern, command)
        if rec:
            break

    if not rec:
        raise error.OSFException('Could not parse command: %s' % command)

    groups = rec.groupdict()

    action = groups.get('action').replace(' ', '_')
    service_name = groups.get('service')
    container_name = groups.get('container')
    node_name = groups.get('node')
    network_name = groups.get('network')
    target = groups.get('target')
    duration = groups.get('duration')

    if service_name:
        service = destructor.get_service(name=service_name)

        if action in SERVICE_ACTIONS:

            kwargs = {}
            if node_name in RANDOMNESS:
                kwargs['nodes'] = service.get_nodes().pick()
            elif node_name and node_name not in ANYTHING:
                kwargs['nodes'] = destructor.get_nodes(fqdns=[node_name])

            if duration:
                kwargs['sec'] = int(duration)

            fn = getattr(service, action)
            fn(**kwargs)

        else:  # node actions
            nodes = service.get_nodes()

            if node_name in RANDOMNESS:
                nodes = nodes.pick()

            kwargs = {}
            if network_name:
                kwargs['network_name'] = network_name
            if target:
                kwargs['target'] = target
                kwargs['duration'] = int(duration)

            fn = getattr(nodes, action)
            fn(**kwargs)
    elif container_name:
        container = destructor.get_container(name=container_name)

        if action in CONTAINER_ACTIONS:

            kwargs = {}
            if node_name in RANDOMNESS:
                kwargs['nodes'] = container.get_nodes().pick()
            elif node_name and node_name not in ANYTHING:
                kwargs['nodes'] = destructor.get_nodes(fqdns=[node_name])

            if duration:
                kwargs['sec'] = int(duration)

            fn = getattr(container, action)
            fn(**kwargs)

        else:  # node actions
            nodes = container.get_nodes()

            if node_name in RANDOMNESS:
                nodes = nodes.pick()

            kwargs = {}
            if network_name:
                kwargs['network_name'] = network_name
            if target:
                kwargs['target'] = target
                kwargs['duration'] = int(duration)

            fn = getattr(nodes, action)
            fn(**kwargs)
    else:  # nodes operation
        if node_name and node_name not in ANYTHING:
            nodes = destructor.get_nodes(fqdns=[node_name])
        else:
            nodes = destructor.get_nodes()

        kwargs = {}
        if network_name:
            kwargs['network_name'] = network_name
        if target:
            kwargs['target'] = target
            kwargs['duration'] = int(duration)

        fn = getattr(nodes, action)
        fn(**kwargs)

    LOG.info('Command `%s` is executed successfully', command)
