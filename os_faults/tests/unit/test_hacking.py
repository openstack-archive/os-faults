#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from os_faults.tests.hacking import checks
from os_faults.tests.unit import test


class HackingTestCase(test.TestCase):

    def _assert_bad_samples(self, checker, samples, module_file="f"):
        for s in samples:
            self.assertEqual(1, len(list(checker(s, s, module_file))), s)

    def _assert_good_samples(self, checker, samples, module_file="f"):
        for s in samples:
            self.assertEqual([], list(checker(s, s, module_file)), s)

    def test_check_quotas(self):
        bad_lines = [
            "a = '1'",
            "a = \"a\" + 'a'",
            "'",
            "\"\"\"\"\"\" + ''''''"
        ]
        self._assert_bad_samples(checks.check_quotes, bad_lines)

        good_lines = [
            "\"'a'\" + \"\"\"a'''fdfd'''\"\"\"",
            "\"fdfdfd\" + \"''''''\"",
            "a = ''   # noqa "
        ]
        self._assert_good_samples(checks.check_quotes, good_lines)
