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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            grep_container=dict(required=True, type='str'),
            grep_process=dict(required=True, type='str'),
            sig=dict(required=True, type='int')
        ))

    grep_container = module.params['grep_container']
    grep_process = module.params['grep_process']
    sig = module.params['sig']

    cmd = ('bash -c "docker ps -q | '
           'xargs docker inspect --format '
           '\'{{.Id}} {{.Path}} {{ range $arg := .Args }}{{$arg}} {{end}}\' | '
           'grep %s | '
           'awk \'{ print $1 }\' | '
           'xargs docker top | '
           'grep %s | '
           'awk \'{ print $2 }\' | '
           'xargs kill -%s"') % (grep_container, grep_process, sig)
    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    module.exit_json(cmd=cmd, rc=rc, stderr=stderr, stdout=stdout)


if __name__ == '__main__':
    main()
