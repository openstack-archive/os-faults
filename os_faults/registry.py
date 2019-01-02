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

import inspect
import os
import sys

from oslo_utils import importutils

import os_faults
from os_faults.api import base_driver
from os_faults.api import error

DRIVERS = {}


def _import_modules_from_package():
    folder = os.path.dirname(os_faults.__file__)
    library_root = os.path.normpath(os.path.join(folder, os.pardir))
    drivers_folder = os.path.join(folder, 'drivers')

    for root, dirs, files in os.walk(drivers_folder):
        for filename in files:
            if (filename.startswith('__') or
                    filename.startswith('test') or
                    not filename.endswith('.py')):
                continue

            relative_path = os.path.relpath(os.path.join(root, filename),
                                            library_root)
            name = os.path.splitext(relative_path)[0]  # remove extension
            module_name = '.'.join(name.split(os.sep))  # convert / to .

            if module_name not in sys.modules:
                module = importutils.import_module(module_name)
                sys.modules[module_name] = module
            else:
                module = sys.modules[module_name]

            yield module


def _list_drivers():
    modules = _import_modules_from_package()

    for module in modules:
        class_info_list = inspect.getmembers(module, inspect.isclass)

        for class_info in class_info_list:
            klazz = class_info[1]
            if not issubclass(klazz, base_driver.BaseDriver):
                continue
            if 'NAME' not in vars(klazz):  # driver must have a name
                continue
            if klazz.NAME == 'base':  # skip base class
                continue

            yield klazz


def get_drivers():
    global DRIVERS

    if not DRIVERS:
        DRIVERS = {}
        for k in _list_drivers():
            driver_name = k.get_driver_name()
            if driver_name in DRIVERS:
                orig_k = DRIVERS[driver_name]
                orig_path = orig_k.__module__ + '.' + orig_k.__name__
                dup_path = k.__module__ + '.' + k.__name__

                raise error.OSFDriverWithSuchNameExists(
                    'Driver "%s" already defined in %s. '
                    'Found a duplicate in %s ' % (
                        driver_name, orig_path, dup_path))
            DRIVERS[driver_name] = k

    return DRIVERS


def get_driver(name):
    all_drivers = get_drivers()

    if name not in all_drivers:
        raise error.OSFDriverNotFound('Driver %s is not found' % name)

    return all_drivers[name]
