#!/usr/bin/python

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

from ansible.module_utils.basic import *  # noqa

NETWORK_NAME_TO_INTERFACE = {
    'management': 'br-mgmt',
    'public': 'br-ex',
    'private': 'br-prv',
    'storage': 'br-storage',
}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            operation=dict(choices=['up', 'down']),
            network_name=dict(default='management',
                              choices=list(NETWORK_NAME_TO_INTERFACE.keys())),
        ))

    operation = module.params['operation']
    network_name = module.params['network_name']

    interface = NETWORK_NAME_TO_INTERFACE[network_name]
    cmd = 'ip link set %s %s' % (interface, operation)

    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    module.exit_json(cmd=cmd, rc=rc, stderr=stderr, stdout=stdout)


if __name__ == '__main__':
    main()
