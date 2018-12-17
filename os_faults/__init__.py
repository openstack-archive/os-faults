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

import copy
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
        'services': {
            'type': 'object',
            'patternProperties': {
                '.*': {
                    'type': 'object',
                    'properties': {
                        'driver': {'type': 'string'},
                        'args': {'type': 'object'},
                        'hosts': {
                            'type': 'array',
                            'minItems': 1,
                            'items': {'type': 'string'},
                        },
                    },
                    'required': ['driver', 'args'],
                    'additionalProperties': False,
                }
            },
            'additionalProperties': False,
        },
        'cloud_management': {
            'type': 'object',
            'properties': {
                'driver': {'type': 'string'},
                'args': {'type': 'object'},
            },
            'required': ['driver'],
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


def get_default_config_file():
    if 'OS_FAULTS_CONFIG' in os.environ:
        return os.environ['OS_FAULTS_CONFIG']

    for config_file in CONFIG_FILES:
        if os.path.exists(config_file):
            return config_file

    msg = 'Config file is not found on any of paths: {}'.format(CONFIG_FILES)
    raise error.OSFError(msg)


def _init_driver(params):
    driver_cls = registry.get_driver(params['driver'])

    args = params.get('args') or {}  # driver may have no arguments
    if args:
        jsonschema.validate(args, driver_cls.CONFIG_SCHEMA)
    return driver_cls(args)


def connect(cloud_config=None, config_filename=None):
    """Connects to the cloud

    :param cloud_config: dict with cloud and power management params
    :param config_filename: name of the file where to read config from
    :returns: CloudManagement object
    """
    if cloud_config is None:
        config_filename = config_filename or get_default_config_file()
        with open(config_filename) as fd:
            cloud_config = yaml.safe_load(fd.read())

    jsonschema.validate(cloud_config, CONFIG_SCHEMA)

    cloud_management_conf = cloud_config['cloud_management']
    cloud_management = _init_driver(cloud_management_conf)

    services = cloud_config.get('services')
    if services:
        cloud_management.update_services(services)
    cloud_management.validate_services()

    containers = cloud_config.get('containers')
    if containers:
        cloud_management.update_containers(containers)
    cloud_management.validate_containers()

    node_discover_conf = cloud_config.get('node_discover')
    if node_discover_conf:
        node_discover = _init_driver(node_discover_conf)
        cloud_management.set_node_discover(node_discover)

    power_managements_conf = cloud_config.get('power_managements')
    if power_managements_conf:
        for pm_conf in power_managements_conf:
            pm = _init_driver(pm_conf)
            cloud_management.add_power_management(pm)

    return cloud_management


def discover(cloud_config):
    """Connect to the cloud and discover nodes and services

    :param cloud_config: dict with cloud and power management params
    :returns: config dict with discovered nodes/services
    """

    cloud_config = copy.deepcopy(cloud_config)
    cloud_management = connect(cloud_config)

    # discover nodes
    hosts = []
    for host in cloud_management.get_nodes().hosts:
        hosts.append({'ip': host.ip, 'mac': host.mac, 'fqdn': host.fqdn})
        LOG.info('Found node: %s' % str(host))
    cloud_config['node_discover'] = {'driver': 'node_list', 'args': hosts}

    # discover services
    cloud_config['services'] = {}
    for service_name in cloud_management.list_supported_services():
        service = cloud_management.get_service(service_name)
        ips = service.get_nodes().get_ips()
        cloud_config['services'][service_name] = {
            'driver': service.NAME,
            'args': service.config
        }
        if ips:
            cloud_config['services'][service_name]['hosts'] = ips
            LOG.info('Found service "%s" on hosts: %s' % (
                service_name, str(ips)))
        else:
            LOG.warning('Service "%s" is not found' % service_name)

    return cloud_config


def human_api(cloud_management, command):
    """Executes a command written as English sentence

    :param cloud_management: library instance as returned by :connect:
           function
    :param command: text command
    """
    human.execute(cloud_management, command)


def register_ansible_modules(paths):
    """Registers ansible modules by provided paths

    Allows to use custom ansible modules in NodeCollection.run_task method

    :param paths: list of paths to folders with ansible modules
    """
    executor.add_module_paths(paths)
