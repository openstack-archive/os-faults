# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import logging
import threading

from os_faults.api import error

LOG = logging.getLogger(__name__)


def run(target, mac_addresses_list):
    tw = ThreadsWrapper(target)
    for mac_address in mac_addresses_list:
        tw.start_thread(mac_address=mac_address)
    tw.join_threads()

    if tw.errors:
        raise error.PowerManagementError(
            'There are some errors when working the driver. '
            'Please, check logs for more details.')


class ThreadsWrapper(object):
    def __init__(self, target):
        self.target = target
        self.threads = []
        self.errors = []

    def _target(self, **kwargs):
        try:
            self.target(**kwargs)
        except Exception as exc:
            LOG.error('Target raised exception: %s', exc)
            self.errors.append(exc)

    def start_thread(self, **kwargs):
        thread = threading.Thread(target=self._target, kwargs=kwargs)
        thread.start()
        self.threads.append(thread)

    def join_threads(self):
        for thread in self.threads:
            thread.join()


def require_variables(*variables):
    """Class method decorator to check that required variables are present"""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kawrgs):
            missing_vars = []
            for var in variables:
                if not hasattr(self, var):
                    missing_vars.append(var)
            if missing_vars:
                missing_vars = ', '.join(missing_vars)
                msg = '{} required for {}.{}'.format(
                    missing_vars, self.__class__.__name__, fn.__name__)
                raise NotImplementedError(msg)
            return fn(self, *args, **kawrgs)
        return wrapper
    return decorator
