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

from ansible.module_utils.basic import AnsibleModule  # noqa


def main():
    module = AnsibleModule(
        argument_spec=dict(
            service=dict(required=True, type='str'),
            action=dict(required=True, choices=['block', 'unblock']),
            port=dict(required=True, type='int'),
            protocol=dict(required=True, choices=['tcp', 'udp']),
        ))

    service = module.params['service']
    action = module.params['action']
    port = module.params['port']
    protocol = module.params['protocol']
    comment = '{}_temporary_DROP'.format(service)

    if action == 'block':
        cmd = ('bash -c "iptables -I INPUT 1 -p {protocol} --dport {port} '
               '-j DROP -m comment --comment "{comment}""'.format(
                   comment=comment, port=port, protocol=protocol))
    else:
        cmd = ('bash -c "rule=`iptables -L INPUT -n --line-numbers | '
               'grep "{comment}" | cut -d \' \' -f1`; for arg in $rule;'
               ' do iptables -D INPUT -p {protocol} --dport {port} '
               '-j DROP -m comment --comment "{comment}"; done"'.format(
                   comment=comment, port=port, protocol=protocol))
    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    module.exit_json(cmd=cmd, rc=rc, stderr=stderr, stdout=stdout)


if __name__ == '__main__':
    main()
