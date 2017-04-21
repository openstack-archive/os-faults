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

LOG = logging.getLogger(__name__)

MACADDR_REGEXP = '^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
FQDN_REGEXP = '.*'


class ThreadsWrapper(object):
    def __init__(self):
        self.threads = []
        self.errors = []

    def _target(self, fn, **kwargs):
        try:
            fn(**kwargs)
        except Exception as exc:
            LOG.error('%s raised exception: %s', fn, exc)
            self.errors.append(exc)

    def start_thread(self, fn, **kwargs):
        thread = threading.Thread(target=self._target,
                                  args=(fn, ), kwargs=kwargs)
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
                if not getattr(self, var, None):
                    missing_vars.append(var)
            if missing_vars:
                missing_vars = ', '.join(missing_vars)
                msg = '{} required for {}.{}'.format(
                    missing_vars, self.__class__.__name__, fn.__name__)
                raise NotImplementedError(msg)
            return fn(self, *args, **kawrgs)
        return wrapper
    return decorator


class ComparableMixin(object):

    ATTRS = ()

    def _cmp_attrs(self):
        return tuple(getattr(self, attr) for attr in self.ATTRS)

    def __lt__(self, other):
        return self._cmp_attrs() < other._cmp_attrs()

    def __le__(self, other):
        return self._cmp_attrs() <= other._cmp_attrs()

    def __eq__(self, other):
        return self._cmp_attrs() == other._cmp_attrs()

    def __ge__(self, other):
        return self._cmp_attrs() >= other._cmp_attrs()

    def __gt__(self, other):
        return self._cmp_attrs() > other._cmp_attrs()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._cmp_attrs())


class ReprMixin(object):

    ATTRS = ()
    REPR_ATTRS = ()

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={}'.format(attr, repr(getattr(self, attr)))
                      for attr in self.REPR_ATTRS or self.ATTRS))
