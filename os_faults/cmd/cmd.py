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
import logging

import sys

import os_faults


# todo (ishakhat): list available actions and services
USAGE = """os-inject-fault [-h] [-c CONFIG] [-d] [-v] [command]

Service-based command performs specified action against service on
all, on one random node or on the node specified by FQDN:

  <action> <service> service [on (random|one|single|<fqdn> node[s])]

Node-based command performs specified action on all or selected service's
node:

  <action> [random|one|single] <service> node[s]

Network-management command is a subset of node-based query::

  disable|enable network <network name> on <service> node[s]

Examples:

 * Restart Keystone service - restarts Keystone service on all nodes
 * kill nova-api service on one node - restarts Nova API on one of nodes
 * Reboot one node with mysql - reboots one random node with MySQL
 * Reboot node-2.domain.tld node - reboot node with specified name
"""


def main():
    parser = argparse.ArgumentParser(prog='os-inject-fault', usage=USAGE)
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
