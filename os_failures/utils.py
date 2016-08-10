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
import itertools
import logging as std_logging
import os
import random
import uuid

from oslo_config import cfg
from oslo_log import log as logging
import re
import six
import yaml


LOG = logging.getLogger(__name__)


def env(*_vars, **kwargs):
    """Returns the first environment variable set.

    If none are non-empty, defaults to '' or keyword arg default.
    """
    for v in _vars:
        value = os.environ.get(v)
        if value:
            return value
    return kwargs.get('default', None)


def validate_required_opts(conf, opts):
    # all config parameters default to ENV values, that's why standard
    # check of required options doesn't work and needs to be done manually
    for opt in opts:
        if opt.required and not conf[opt.dest]:
            raise cfg.RequiredOptError(opt.name)


def init_config_and_logging(opts):
    conf = cfg.CONF
    conf.register_cli_opts(opts)
    conf.register_opts(opts)
    logging.register_options(conf)
    logging.set_defaults()

    try:
        conf(project='performa')
        validate_required_opts(conf, opts)
    except cfg.RequiredOptError as e:
        print('Error: %s' % e)
        conf.print_usage()
        exit(1)

    logging.setup(conf, 'performa')
    LOG.info('Logging enabled')
    conf.log_opt_values(LOG, std_logging.DEBUG)


def resolve_relative_path(file_name):
    path = os.path.normpath(os.path.join(
        os.path.dirname(__import__('os_failures').__file__), '../', file_name))
    if os.path.exists(path):
        return path


def get_absolute_file_path(file_name, base_dir='', alias_mapper=None):
    full_path = os.path.normpath(os.path.join(base_dir, file_name))

    if alias_mapper:  # interpret file_name as alias
        alias_path = resolve_relative_path(alias_mapper(file_name))
        if alias_path:
            full_path = alias_path
            LOG.info('Alias "%s" is resolved into file "%s"', file_name,
                     full_path)

    if not os.path.exists(full_path):
        # treat file_name as relative to act's package root
        full_path = os.path.normpath(
            os.path.join(os.path.dirname(__import__('performa').__file__),
                         '../', file_name))
        if not os.path.exists(full_path):
            msg = ('File %s not found by absolute nor by relative path' %
                   file_name)
            raise IOError(msg)

    return full_path


def read_file(file_name, base_dir='', alias_mapper=None):
    full_path = get_absolute_file_path(file_name, base_dir, alias_mapper)

    fd = None
    try:
        fd = open(full_path)
        return fd.read()
    except IOError as e:
        LOG.error('Error reading file: %s', e)
        raise
    finally:
        if fd:
            fd.close()


def write_file(data, file_name, base_dir=''):
    full_path = os.path.normpath(os.path.join(base_dir, file_name))
    fd = None
    try:
        fd = open(full_path, 'w')
        return fd.write(data)
    except IOError as e:
        LOG.error('Error writing file: %s', e)
        raise
    finally:
        if fd:
            fd.close()


def read_yaml_file(file_name, base_dir='', alias_mapper=None):
    raw = read_file(file_name, base_dir, alias_mapper)
    try:
        parsed = yaml.safe_load(raw)
        return parsed
    except Exception as e:
        LOG.error('Failed to parse file %(file)s in YAML format: %(err)s',
                  dict(file=file_name, err=e))


def read_uri(uri):
    try:
        req = six.moves.urllib.request.Request(url=uri)
        fd = six.moves.urllib.request.urlopen(req)
        raw = fd.read()
        fd.close()
        return raw
    except Exception as e:
        LOG.warn('Error "%(error)s" while reading uri %(uri)s',
                 {'error': e, 'uri': uri})


def random_string(length=6):
    return ''.join(random.sample('adefikmoprstuz', length))


def make_id():
    return str(uuid.uuid4())


def make_help_options(message, base, type_filter=None):
    path = resolve_relative_path(base)
    files = itertools.chain.from_iterable(
        [map(functools.partial(os.path.join, root), files)
         for root, dirs, files in os.walk(path)])  # list of files in a tree
    if type_filter:
        files = (f for f in files if type_filter(f))  # filtered list
    rel_files = map(functools.partial(os.path.relpath, start=path), files)
    return message % ', '.join('"%s"' % f.partition('.')[0]
                               for f in sorted(rel_files))


def algebraic_product(**kwargs):
    position_to_key = {}
    values = []
    total = 1

    for key, item in six.iteritems(kwargs):
        position_to_key[len(values)] = key
        if type(item) != list:
            item = [item]  # enclose single item into the list

        values.append(item)
        total *= len(item)

    LOG.debug('Total number of permutations is: %s', total)

    for chain in itertools.product(*values):
        result = {}
        for position, key in six.iteritems(position_to_key):
            result[key] = chain[position]
        yield result


def strict(s):
    return re.sub(r'[^\w\d]+', '_', re.sub(r'\(.+\)', '', s)).lower()


def parse_url(url):
    arr = url.split(':')
    result = {}

    if len(arr) > 0:
        result['host'] = arr[0]

        if len(arr) > 1:
            if arr[1].isdigit():
                result['port'] = int(arr[1])
            else:
                raise ValueError('URL should be in form of host[:port], '
                                 'but got: %s', url)
    else:
        ValueError('URL should not be empty')

    return result
