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

"""
Guidelines for writing new hacking checks

 - Use only for OS-Faults specific tests. OpenStack general tests
   should be submitted to the common 'hacking' module.
 - Pick numbers in the range N3xx. Find the current test with
   the highest allocated number and then pick the next value.
 - Keep the test method code in the source file ordered based
   on the N3xx value.
 - List the new rule in the top level HACKING.rst file
 - Add test cases for each new rule to tests/unit/hacking/test_hacking.py

"""

import functools


def skip_ignored_lines(func):
    @functools.wraps(func)
    def wrapper(logical_line, physical_line, filename):
        line = physical_line.strip()
        if not line or line.startswith("#") or line.endswith("# noqa"):
            return
        yield next(func(logical_line, physical_line, filename))

    return wrapper


@skip_ignored_lines
def check_quotes(logical_line, physical_line, filename):
    """Check that single quotation marks are not used

    N350
    """

    in_string = False
    in_multiline_string = False
    single_quotas_are_used = False

    check_tripple = (
        lambda line, i, char: (
            i + 2 < len(line) and
            (char == line[i] == line[i + 1] == line[i + 2])
        )
    )

    i = 0
    while i < len(logical_line):
        char = logical_line[i]

        if in_string:
            if char == "\"":
                in_string = False
            if char == "\\":
                i += 1  # ignore next char

        elif in_multiline_string:
            if check_tripple(logical_line, i, "\""):
                i += 2  # skip next 2 chars
                in_multiline_string = False

        elif char == "#":
            break

        elif char == "'":
            single_quotas_are_used = True
            break

        elif char == "\"":
            if check_tripple(logical_line, i, "\""):
                in_multiline_string = True
                i += 3
                continue
            in_string = True

        i += 1

    if single_quotas_are_used:
        yield (i, "N350 Remove Single quotes")


def factory(register):
    register(check_quotes)
