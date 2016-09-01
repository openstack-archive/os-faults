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

import re

from os_faults.api import error

COMMAND_PATTERN = re.compile('(?P<action>\w+)'
                             '(\s+(?P<specifier>(random)))?'
                             '(\s+(?P<subject>\S+))'
                             '(\s+(?P<subject_type>\w+))?')


def execute(distractor, command):
    rec = re.search(COMMAND_PATTERN, command)

    if not rec:
        raise error.OSFException('Could not parse command: %s' % command)

    action = rec.group('action').lower()
    specifier = (rec.group('specifier') or '').lower()
    subject = rec.group('subject').lower()
    subject_type = (rec.group('subject_type') or '').lower()

    service = distractor.get_service(name=subject)

    if service:
        # e.g. restart keystone service
        if subject_type == 'service':
            fn = getattr(service, action)
            fn()
        elif subject_type == 'node':
            nodes = service.get_nodes()
            if specifier == 'random':
                nodes = nodes.pick()

            fn = getattr(nodes, action)
            fn()

    else:
        # e.g. restart node-2.domain.tld
        nodes = distractor.get_nodes(fqdns=[subject])
        fn = getattr(nodes, action)
        fn()
