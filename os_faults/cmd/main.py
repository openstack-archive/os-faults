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
from os_faults import registry


READABLE_FILE = click.Path(dir_okay=False, readable=True, exists=True,
                           resolve_path=True)
WRITABLE_FILE = click.Path(dir_okay=False, writable=True, resolve_path=True)

config_option = click.option('-c', '--config', type=READABLE_FILE,
                             help='path to os-faults cloud connection config')


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Version: %s' % os_faults.get_release())
    ctx.exit()


@click.group()
@click.option('--debug', '-d', is_flag=True, help='Enable debug logs')
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help='Show version and exit.')
def main(debug):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)


@main.command()
@config_option
def verify(config):
    """Verify connection to the cloud"""
    config = config or os_faults.get_default_config_file()
    cloud_management = os_faults.connect(config_filename=config)
    cloud_management.verify()


@main.command()
@click.argument('output', type=WRITABLE_FILE)
@config_option
def discover(config, output):
    """Discover services/nodes and save them to output config file"""
    config = config or os_faults.get_default_config_file()
    with open(config) as f:
        cloud_config = yaml.safe_load(f.read())
    discovered_config = os_faults.discover(cloud_config)
    with open(output, 'w') as f:
        f.write(yaml.safe_dump(discovered_config, default_flow_style=False))
    click.echo('Saved {}'.format(output))


@main.command()
@config_option
def nodes(config):
    """List cloud nodes"""
    config = config or os_faults.get_default_config_file()
    cloud_management = os_faults.connect(config_filename=config)
    hosts = [{'ip': host.ip, 'mac': host.mac, 'fqdn': host.fqdn}
             for host in cloud_management.get_nodes().hosts]
    click.echo(yaml.safe_dump(hosts, default_flow_style=False), nl=False)


@main.command()
def drivers():
    """List os-faults drivers"""
    drivers = sorted(registry.get_drivers().keys())
    click.echo(yaml.safe_dump(drivers, default_flow_style=False), nl=False)


if __name__ == '__main__':
    main()
