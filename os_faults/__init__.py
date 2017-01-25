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

import appdirs
import jsonschema
import logging
import pbr.version
import yaml

from os_faults.ansible import executor
from os_faults.api import error
from os_faults.api import human
from os_faults import registry

LOG = logging.getLogger(__name__)

# Set default logging handler to avoid "No handler found" warnings.
LOG.addHandler(logging.NullHandler())


def get_version():
    return pbr.version.VersionInfo('os_faults').version_string()


def get_release():
    return pbr.version.VersionInfo('os_faults').release_string()


APPDIRS = appdirs.AppDirs(appname='openstack', appauthor='OpenStack')
UNIX_SITE_CONFIG_HOME = '/etc/openstack'
CONFIG_SEARCH_PATH = [
    os.getcwd(),
    APPDIRS.user_config_dir,
    UNIX_SITE_CONFIG_HOME,
]
CONFIG_FILES = [
    os.path.join(d, 'os-faults' + s)
    for d in CONFIG_SEARCH_PATH
    for s in ['.json', '.yaml', '.yml']
]

CONFIG_SCHEMA = {
    'type': 'object',
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'properties': {
        'node_discover': {
            'type': 'object',
            'properties': {
                'driver': {'type': 'string'},
                'args': {},
            },
            'required': ['driver', 'args'],
            'additionalProperties': False,
        },
        'cloud_management': {
            'type': 'object',
            'properties': {
                'driver': {'type': 'string'},
                'args': {'type': 'object'},
            },
            'required': ['driver', 'args'],
            'additionalProperties': False,
        },
        'power_management': {
            'type': 'object',
            'properties': {
                'driver': {'type': 'string'},
                'args': {'type': 'object'},
            },
            'required': ['driver', 'args'],
            'additionalProperties': False,
        },
        'power_managements': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'driver': {'type': 'string'},
                    'args': {'type': 'object'},
                },
                'required': ['driver', 'args'],
                'additionalProperties': False,
            },
            'minItems': 1,
        },
    },
    'required': ['cloud_management'],
}


def _read_config(config_filename):
    os_faults_config = config_filename or os.environ.get('OS_FAULTS_CONFIG')
    if os_faults_config:
        CONFIG_FILES.insert(0, os_faults_config)

    for config_file in CONFIG_FILES:
        if os.path.exists(config_file):
            with open(config_file) as fd:
                return yaml.safe_load(fd.read())

    msg = 'Config file is not found on any of paths: {}'.format(CONFIG_FILES)
    raise error.OSFError(msg)


def _init_driver(params):
    driver_cls = registry.get_driver(params['driver'])
    jsonschema.validate(params['args'], driver_cls.CONFIG_SCHEMA)
    return driver_cls(params['args'])


def connect(cloud_config=None, config_filename=None):
    """Connect to the cloud

    :param cloud_config: dict with cloud and power management params
    :param config_filename: name of the file where to read config from
    :return: CloudManagement object
    """
    if cloud_config is None:
        cloud_config = _read_config(config_filename)

    jsonschema.validate(cloud_config, CONFIG_SCHEMA)

    cloud_management_conf = cloud_config['cloud_management']
    cloud_management = _init_driver(cloud_management_conf)

    node_discover_conf = cloud_config.get('node_discover')
    if node_discover_conf:
        node_discover = _init_driver(node_discover_conf)
        cloud_management.set_node_discover(node_discover)

    power_managements_conf = cloud_config.get('power_managements')
    if power_managements_conf:
        for pm_conf in power_managements_conf:
            pm = _init_driver(pm_conf)
            cloud_management.add_power_management(pm)

    power_management_conf = cloud_config.get('power_management')
    if power_management_conf:
        if power_managements_conf:
            raise error.OSFError('Please use only power_managements')
        else:
            LOG.warning('power_management is deprecated, use '
                        'power_managements instead.')

        power_management = _init_driver(power_management_conf)
        cloud_management.add_power_management(power_management)

    return cloud_management


def human_api(distractor, command):
    """Execute high-level text command with specified destructor

    :param destructor: library instance as returned by :connect: function
    :param command: text command
    """
    human.execute(distractor, command)


def register_ansible_modules(paths):
    """Registers ansible modules by provided paths

    Allows to use custom ansible modules in NodeCollection.run_task method

    :param path: list of paths to folders with ansible modules
    """
    executor.add_module_paths(paths)
