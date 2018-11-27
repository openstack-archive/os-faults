=========
OS-Faults
=========

**OpenStack fault-injection library**

The library does destructive actions inside an OpenStack cloud. It provides
an abstraction layer over different types of cloud deployments. The actions
are implemented as drivers (e.g. DevStack driver, Fuel driver, Libvirt driver,
IPMI driver, Universal driver).

* Free software: Apache license
* Documentation: http://os-faults.readthedocs.io
* Source: https://github.com/openstack/os-faults
* Bugs: http://bugs.launchpad.net/os-faults


Installation
------------

Requirements
~~~~~~~~~~~~

Ansible is required and should be installed manually system-wide or in virtual
environment. Please refer to [https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html]
for installation instructions.

Regular installation::

    pip install os-faults

The library contains optional libvirt driver, if you plan to use it,
please use the following command to install os-faults with extra dependencies::

    pip install os-faults[libvirt]


Configuration
-------------

The cloud deployment configuration is specified in JSON/YAML format or Python dictionary.

The library operates with 2 types of objects:
 * `service` - is a software that runs in the cloud, e.g. `nova-api`
 * `container` - is a software that runs in the cloud, e.g. `neutron_api`
 * `nodes` - nodes that host the cloud, e.g. a server with a hostname


Example 1. DevStack
~~~~~~~~~~~~~~~~~~~

Connection to DevStack can be specified using the following YAML file:

.. code-block:: yaml

    cloud_management:
      driver: devstack
      args:
        address: devstack.local
        auth:
          username: stack
          private_key_file: cloud_key
        iface: enp0s8

OS-Faults library will connect to DevStack by address `devstack.local` with user `stack`
and SSH key located in file `cloud_key`. Default networking interface is specified with
parameter `iface`. Note that user should have sudo permissions (by default DevStack user has them).

DevStack driver is responsible for service discovery. For more details please refer
to driver documentation: http://os-faults.readthedocs.io/en/latest/drivers.html#devstack-systemd-devstackmanagement

Example 2. An OpenStack with services, containers and power management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An arbitrary OpenStack can be handled too with help of `universal` driver.
In this example os-faults is used as Python library.

.. code-block:: python

    cloud_config = {
        'cloud_management': {
            'driver': 'universal',
        },
        'node_discover': {
            'driver': 'node_list',
            'args': [
                {
                    'ip': '192.168.5.127',
                    'auth': {
                        'username': 'root',
                        'private_key_file': 'openstack_key',
                    }
                },
                {
                    'ip': '192.168.5.128',
                    'auth': {
                        'username': 'root',
                        'private_key_file': 'openstack_key',
                    }
                }
            ]
        },
        'services': {
            'memcached': {
                'driver': 'system_service',
                'args': {
                    'service_name': 'memcached',
                    'grep': 'memcached',
                }
            }
        },
        'containers': {
            'neutron_api': {
                'driver': 'docker_container',
                'args': {
                    'container_name': 'neutron_api',
                }
            }
        },
        'power_managements': [
            {
                'driver': 'libvirt',
                'args': {
                    'connection_uri': 'qemu+unix:///system',
                }
            },
        ]
    }

The config contains all OpenStack nodes with credentials and all
services/containers. OS-Faults will automatically figure out the mapping
between services/containers and nodes. Power management configuration is
flexible and supports mixed bare-metal / virtualized deployments.

First let's establish a connection to the cloud and verify it:

.. code-block:: python

    cloud_management = os_faults.connect(cloud_config)
    cloud_management.verify()

The library can also read configuration from a file in YAML or JSON format.
The configuration file can be specified in the `OS_FAULTS_CONFIG` environment
variable. By default the library searches for file `os-faults.{json,yaml,yml}`
in one of locations:

  * current directory
  * ~/.config/os-faults
  * /etc/openstack

Now let's make some destructive action:

.. code-block:: python

    cloud_management.get_service(name='memcached').kill()
    cloud_management.get_container(name='neutron_api').restart()


Human API
---------

Human API is simplified and self-descriptive. It includes multiple commands
that are written like normal English sentences.

**Service-oriented** command performs specified `action` against `service` on
all, on one random node or on the node specified by FQDN::

    <action> <service> service [on (random|one|single|<fqdn> node[s])]

Examples:
    * `Restart Keystone service` - restarts Keystone service on all nodes.
    * `kill nova-api service on one node` - kills Nova API on one
      randomly-picked node.

**Container-oriented** command performs specified `action` against `container`
on all, on one random node or on the node specified by FQDN::

    <action> <container> container [on (random|one|single|<fqdn> node[s])]

Examples:
    * `Restart neutron_ovs_agent container` - restarts neutron_ovs_agent
      container on all nodes.
    * `Terminate neutron_api container on one node` - stops Neutron API
      container on one randomly-picked node.

**Node-oriented** command performs specified `action` on node specified by FQDN
or set of service's nodes::

    <action> [random|one|single|<fqdn>] node[s] [with <service> service]

Examples:
    * `Reboot one node with mysql` - reboots one random node with MySQL.
    * `Reset node-2.domain.tld node` - resets node `node-2.domain.tld`.

**Network-oriented** command is a subset of node-oriented and performs network
management operation on selected nodes::

    <action> <network> network on [random|one|single|<fqdn>] node[s]
        [with <service> service]

Examples:
    * `Disconnect management network on nodes with rabbitmq service` - shuts
      down management network interface on all nodes where rabbitmq runs.
    * `Connect storage network on node-1.domain.tld node` - enables storage
      network interface on node-1.domain.tld.


Extended API
------------

1. Service actions
~~~~~~~~~~~~~~~~~~

Get a service and restart it:

.. code-block:: python

    cloud_management = os_faults.connect(cloud_config)
    service = cloud_management.get_service(name='glance-api')
    service.restart()

Available actions:
 * `start` - start Service
 * `terminate` - terminate Service gracefully
 * `restart` - restart Service
 * `kill` - terminate Service abruptly
 * `unplug` - unplug Service out of network
 * `plug` - plug Service into network

2. Container actions
~~~~~~~~~~~~~~~~~~~~

Get a container and restart it:

.. code-block:: python

    cloud_management = os_faults.connect(cloud_config)
    container = cloud_management.get_container(name='neutron_api')
    container.restart()

Available actions:
 * `start` - start Container
 * `terminate` - terminate Container gracefully
 * `restart` - restart Container

3. Node actions
~~~~~~~~~~~~~~~

Get all nodes in the cloud and reboot them:

.. code-block:: python

    nodes = cloud_management.get_nodes()
    nodes.reboot()

Available actions:
 * `reboot` - reboot all nodes gracefully
 * `poweroff` - power off all nodes abruptly
 * `reset` - reset (cold restart) all nodes
 * `disconnect` - disable network with the specified name on all nodes
 * `connect` - enable network with the specified name on all nodes

4. Operate with nodes
~~~~~~~~~~~~~~~~~~~~~

Get all nodes where a service runs, pick one of them and reset:

.. code-block:: python

    nodes = service.get_nodes()
    one = nodes.pick()
    one.reset()

Get nodes where l3-agent runs and disable the management network on them:

.. code-block:: python

    fqdns = neutron.l3_agent_list_hosting_router(router_id)
    nodes = cloud_management.get_nodes(fqdns=fqdns)
    nodes.disconnect(network_name='management')

5. Operate with services
~~~~~~~~~~~~~~~~~~~~~~~~

Restart a service on a single node:

.. code-block:: python

    service = cloud_management.get_service(name='keystone')
    nodes = service.get_nodes().pick()
    service.restart(nodes)

6. Operate with containers
~~~~~~~~~~~~~~~~~~~~~~~~~~

Terminate a container on a random node:

.. code-block:: python

    container = cloud_management.get_container(name='neutron_ovs_agent')
    nodes = container.get_nodes().pick()
    container.restart(nodes)


License notes
-------------

Ansible is distributed under GPL-3.0 license and thus all programs
that link with its code are subject to GPL restrictions [1].
However these restrictions are not applied to os-faults library
since it invokes Ansible as process [2][3].

Ansible modules are provided with Apache license (compatible to GPL) [4].
Those modules import part of Ansible runtime (modules API) and executed
on remote hosts. os-faults library does not import these module
neither static nor dynamic.

 [1] https://www.gnu.org/licenses/gpl-faq.html#GPLModuleLicense
 [2] https://www.gnu.org/licenses/gpl-faq.html#GPLPlugins
 [3] https://www.gnu.org/licenses/gpl-faq.html#MereAggregation
 [4] https://www.apache.org/licenses/GPL-compatibility.html
