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

import os
import uuid

from ansible.module_utils.basic import *  # noqa


SCRIPT_TEMPLATE = """#!/bin/bash
cids=`docker ps -q`
cid=`docker inspect --format \
     '{{.Id}} {{.Path}} {{ range $arg := .Args }}{{$arg}} {{end}}' | \
     grep %s | awk '{ print $1 }'`
pids=`docker top $cid | grep %s | awk '{ print $2 }'`
kill -19 $pids
sleep %s
kill -18 $pids
rm %s
"""


def main():
    module = AnsibleModule(
        argument_spec=dict(
            grep_container=dict(required=True, type='str'),
            grep_process=dict(required=True, type='str'),
            sec=dict(required=True, type='int')
        ))

    grep_container = module.params['grep_container']
    grep_process = module.params['grep_process']
    sec = module.params['sec']

    fname = '/tmp/script.%s' % str(uuid.uuid4())
    script = SCRIPT_TEMPLATE % (grep_container, grep_process, sec, fname)

    # save tmp script
    with open(fname, 'w') as f:
        f.write(script)

    # set executable flag
    os.chmod(fname, 0o770)

    cmd = ('bash -c "nohup %s &"') % fname
    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    module.exit_json(cmd=cmd, rc=rc, stderr=stderr, stdout=stdout)


if __name__ == '__main__':
    main()
