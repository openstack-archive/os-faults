=====
Usage
=====

Configuration
-------------

The cloud deployment configuration schema is an extension to the cloud config
used by the `os-client-config <https://github.com/openstack/os-client-config>`_
library:

.. code-block:: python

    cloud_config = {
        'cloud_management': {
            'driver': 'devstack',
            'args': {
                'address': 'devstack.local',
                'username': 'root',
            }
        },
        'power_managements': [
            {
                'driver': 'libvirt',
                'args': {
                    'connection_uri': 'qemu+unix:///system',
                }
            }
        ]
    }

Establish a connection to the cloud and verify it:

.. code-block:: python

    destructor = os_faults.connect(cloud_config)
    destructor.verify()

The library can also read configuration from a file and the file can be in the
following three formats: os-faults.{json,yaml,yml}. The configuration file can
be specified in the `OS_FAULTS_CONFIG` environment variable or can be read from
one of the default locations:

    * current directory
    * ~/.config/os-faults
    * /etc/openstack

Make some destructive actions:

.. code-block:: python

    destructor.get_service(name='keystone').restart()


The library operates with 2 types of objects:

    * `service` - is a software that runs in the cloud, e.g. `nova-api`
    * `nodes` - nodes that host the cloud, e.g. a hardware server with a hostname


Simplified API
--------------

Simplified API is used to inject faults in a human-friendly form.

**Service-oriented** command performs specified `action` against `service` on
all, on one random node or on the node specified by FQDN::

    <action> <service> service [on (random|one|single|<fqdn> node[s])]

Examples:
    * `Restart Keystone service` - restarts Keystone service on all nodes.
    * `kill nova-api service on one node` - restarts Nova API on one
      randomly-picked node.

**Node-oriented** command performs specified `action` on node specified by FQDN
or set of service's nodes::

    <action> [random|one|single|<fqdn>] node[s] [with <service> service]

Examples:
    * `Reboot one node with mysql` - reboots one random node with MySQL.
    * `Reset node-2.domain.tld node` - reset node `node-2.domain.tld`.

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

    destructor = os_faults.connect(cloud_config)
    service = destructor.get_service(name='glance-api')
    service.restart()

Available actions:
 * `start` - start Service
 * `terminate` - terminate Service gracefully
 * `restart` - restart Service
 * `kill` - terminate Service abruptly
 * `unplug` - unplug Service out of network
 * `plug` - plug Service into network

2. Node actions
~~~~~~~~~~~~~~~

Get all nodes in the cloud and reboot them:

.. code-block:: python

    nodes = destructor.get_nodes()
    nodes.reboot()

Available actions:
 * `reboot` - reboot all nodes gracefully
 * `poweroff` - power off all nodes abruptly
 * `reset` - reset (cold restart) all nodes
 * `oom` - fill all node's RAM
 * `disconnect` - disable network with the specified name on all nodes
 * `connect` - enable network with the specified name on all nodes

3. Operate with nodes
~~~~~~~~~~~~~~~~~~~~~

Get all nodes where a service runs, pick one of them and reset:

.. code-block:: python

    nodes = service.get_nodes()
    one = nodes.pick()
    one.reset()

Get nodes where l3-agent runs and disable the management network on them:

.. code-block:: python

    fqdns = neutron.l3_agent_list_hosting_router(router_id)
    nodes = destructor.get_nodes(fqdns=fqdns)
    nodes.disconnect(network_name='management')

4. Operate with services
~~~~~~~~~~~~~~~~~~~~~~~~

Restart a service on a single node:

.. code-block:: python

    service = destructor.get_service(name='keystone')
    nodes = service.get_nodes().pick()
    service.restart(nodes)
