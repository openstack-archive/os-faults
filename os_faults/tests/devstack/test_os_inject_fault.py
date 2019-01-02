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

import logging
import os
import re
import shlex

from oslo_concurrency import processutils

from os_faults.tests.unit import test


LOG = logging.getLogger(__name__)


class TestOSInjectFaultUniversalDriver(test.TestCase):
    CONFIG_FILE = os.path.join(os.path.dirname(__file__),
                               'os-faults-universal.yaml')

    def test_connect(self):
        cmd = 'os-inject-fault -dc %s -v' % self.CONFIG_FILE

        command_stdout, command_stderr = processutils.execute(
            *shlex.split(cmd))

        success = re.search('Connected to cloud successfully', command_stderr)
        self.assertTrue(success)

    def test_restart_etcd(self):
        cmd = 'os-inject-fault -dc %s restart etcd service' % self.CONFIG_FILE

        command_stdout, command_stderr = processutils.execute(
            *shlex.split(cmd))

        print('stdout', command_stdout)
        print('stderr', command_stderr)
        success = re.search('successfully', command_stderr)
        self.assertTrue(success)


class TestOSInjectFaultDevstackDriver(TestOSInjectFaultUniversalDriver):
    CONFIG_FILE = os.path.join(os.path.dirname(__file__),
                               'os-faults-devstack.yaml')
