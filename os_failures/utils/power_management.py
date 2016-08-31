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

import logging
import threading
import traceback

from os_failures.api import error


def run(target, mac_addresses_list):
    tw = ThreadsWrapper(target)
    for mac_address in mac_addresses_list:
        tw.start_thread(mac_address=mac_address)
    tw.join_threads()

    if tw.errors:
        raise error.PowerManagmentError(
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
            logging.error(traceback.format_exc())
            self.errors.append(exc)

    def start_thread(self, **kwargs):
        thread = threading.Thread(target=self._target, kwargs=kwargs)
        thread.start()
        self.threads.append(thread)

    def join_threads(self):
        for thread in self.threads:
            thread.join()
