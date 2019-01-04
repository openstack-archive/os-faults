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

STRESSORS_MAP = {
    'cpu': '--cpu 0',
    'disk': '--hdd 0',
    'memory': '--brk 0',
    'kernel': '--kill 0',
    'all': '--all 0',
}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            target=dict(required=True, type='str'),
            duration=dict(required=True, type='int')
        ))

    target = module.params['target']
    stressor = STRESSORS_MAP.get(target) or STRESSORS_MAP['all']
    duration = module.params['duration']

    cmd = 'bash -c "stress-ng %s --timeout %ss"' % (stressor, duration)
    rc, stdout, stderr = module.run_command(cmd, check_rc=True)

    module.exit_json(cmd=cmd, rc=rc, stderr=stderr, stdout=stdout)


if __name__ == '__main__':
    main()
