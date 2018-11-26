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

import argparse
import inspect
import logging
import sys
import textwrap

import os_faults
from os_faults.api import cloud_management
from os_faults.api import node_collection as node_collection_pkg
from os_faults.api import service as service_pkg
from os_faults import registry


def describe_actions(klazz):
    methods = (m for m in inspect.getmembers(
        klazz,
        predicate=lambda o: ((inspect.isfunction(o) or inspect.ismethod(o)) and
                             hasattr(o, '__public__'))))
    return ['%s - %s' % (m[0], m[1].__doc__.split('\n')[0])
            for m in sorted(methods)]

SERVICE_ACTIONS = describe_actions(service_pkg.Service)
NODE_ACTIONS = describe_actions(node_collection_pkg.NodeCollection)

USAGE = 'os-inject-fault [-h] [-c CONFIG] [-d] [-v] [command]'
HELP_TEMPLATE = """
Built-in drivers:
%(drivers)s

*Service-oriented* commands perform specified action against service on
all, on one random node or on the node specified by FQDN:

  <action> <service> service [on (random|one|single|<fqdn> node[s])]

  where:
    action is one of:
      %(service_action)s
    service is one of supported by driver:
%(services)s

Examples:
    * "Restart Keystone service" - restarts Keystone service on all nodes.
    * "kill nova-api service on one node" - restarts Nova API on one
      randomly-picked node.

*Node-oriented* commands perform specified action on node specified by FQDN
or set of service's nodes:

  <action> [random|one|single|<fqdn>] node[s] [with <service> service]

  where:
    action is one of:
      %(node_action)s
    service is one of supported by driver:
%(services)s

Examples:
    * "Reboot one node with mysql" - reboots one random node with MySQL.
    * "Reset node-2.domain.tld node" - reset node node-2.domain.tld.

*Network-oriented* commands are subset of node-oriented and perform network
management operation on selected nodes:

  [connect|disconnect] <network> network on [random|one|single|<fqdn>] node[s]
    [with <service> service]

  where:
    network is one of supported by driver:
%(networks)s
    service is one of supported by driver:
%(services)s

Examples:
    * "Disconnect management network on nodes with rabbitmq service" - shuts
      down management network interface on all nodes where rabbitmq runs.
    * "Connect storage network on node-1.domain.tld node" - enables storage
      network interface on node-1.domain.tld.

For more details please refer to docs: http://os-faults.readthedocs.io/
"""


def _list_items(group, items):
    s = '\n'.join(
        textwrap.wrap(', '.join(sorted(items)),
                      subsequent_indent=' ' * (len(group) + 8),
                      break_on_hyphens=False))
    if not s:
        s = '/no built-in support/'
    return '      %s: %s' % (group, s)


def _make_epilog():
    drivers = registry.get_drivers()
    services_strings = []
    networks_strings = []
    driver_descriptions = []

    for driver_name, driver in sorted(drivers.items(), key=lambda x: x[0]):
        driver_descriptions.append(
            '  %s - %s' % (driver_name, driver.get_driver_description()))

        if issubclass(driver, cloud_management.CloudManagement):
            services_strings.append(
                _list_items(driver_name, driver.list_supported_services()))
            networks_strings.append(
                _list_items(driver_name, driver.list_supported_networks()))

    return HELP_TEMPLATE % dict(
        drivers='\n'.join(driver_descriptions),
        service_action='\n      '.join(SERVICE_ACTIONS),
        services='\n'.join(services_strings),
        node_action='\n      '.join(sorted(NODE_ACTIONS)),
        networks='\n'.join(networks_strings),
    )


def main():
    parser = argparse.ArgumentParser(
        prog='os-inject-fault',
        usage=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_make_epilog())
    parser.add_argument('-c', '--config', dest='config',
                        help='path to os-faults cloud connection config')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true')
    parser.add_argument('-v', '--verify', action='store_true',
                        help='verify connection to the cloud')
    parser.add_argument('command', nargs='*',
                        help='fault injection command, e.g. "restart keystone '
                             'service"')
    args = parser.parse_args()

    debug = args.debug
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)

    config = args.config
    command = args.command

    if not command and not args.verify:
        parser.print_help()
        sys.exit(0)

    destructor = os_faults.connect(config_filename=config)

    if args.verify:
        destructor.verify()

    if command:
        command = ' '.join(command)
        os_faults.human_api(destructor, command)

if __name__ == '__main__':
    main()
