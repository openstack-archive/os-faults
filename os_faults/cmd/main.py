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

import click
import yaml

import os_faults


READABLE_FILE = click.Path(dir_okay=False, readable=True, exists=True,
                           resolve_path=True)
WRITABLE_FILE = click.Path(dir_okay=False, writable=True, resolve_path=True)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Version %s' % os_faults.get_release())
    ctx.exit()


class CommonOptions(object):
    def __init__(self, config_filename=None, debug=False):
        self.config_filename = (
            config_filename or os_faults.get_default_config_file())
        self.debug = debug


@click.group()
@click.option('--debug', '-d', is_flag=True, help='Enable debug logs')
@click.option('-c', '--config', type=READABLE_FILE,
              help='path to os-faults cloud connection config')
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help='Show version and exit.')
@click.pass_context
def main(ctx, config, debug):
    ctx.obj = CommonOptions(config, debug)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)


@main.command()
@click.pass_obj
def verify(opts):
    """Verify connection to the cloud"""
    destructor = os_faults.connect(config_filename=opts.config_filename)
    destructor.verify()
    click.echo('Connected to cloud successfully')


@main.command()
@click.option('--dst-path', default=None, type=WRITABLE_FILE,
              help='Alternate location for discovered config')
@click.pass_obj
def discover(opts, dst_path):
    """Discover services/nodes and save them to config file"""
    dst_path = dst_path or opts.config_filename
    with open(opts.config_filename) as f:
        cloud_config = yaml.safe_load(f.read())
    discovered_config = os_faults.discover(cloud_config)
    with open(dst_path, 'w') as f:
        f.write(yaml.safe_dump(discovered_config, default_flow_style=False))
    click.echo('Saved {}'.format(dst_path))


if __name__ == '__main__':
    main()
