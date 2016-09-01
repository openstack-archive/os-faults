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

import os_faults


def main():
    usage = 'os-faults [-d] [-c CONFIG] command'
    parser = argparse.ArgumentParser(prog='os-faults', usage=usage)
    parser.add_argument('-d', '--debug', dest='debug', action='store_true')
    parser.add_argument('-c', '--config', dest='config',
                        help='os-faults cloud connection config')
    parser.add_argument('command', nargs='*',
                        help='fault injection command, e.g. "restart keystone '
                             'service"')
    args = parser.parse_args()

    debug = args.debug
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)

    if not args.command:
        parser.print_usage()
        exit(0)

    config = args.config
    command = ' '.join(args.command)

    destructor = os_faults.connect(config_filename=config)
    os_faults.human_api(destructor, command)


if __name__ == '__main__':
    main()
