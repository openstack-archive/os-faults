===========
os-failures
===========

**An OpenStack failures library**

The library does destructive actions against OpenStack cloud. It provides
an abstraction layer over different type of cloud deployment. The actions
are implemented as drivers (e.g. DevStack driver, Fuel driver, KVM driver etc.).

* Free software: Apache license
* Documentation: http://os_failures.readthedocs.io
* Source: https://github.com/shakhat/os-failures
* Bugs: http://bugs.launchpad.net/os_failures

Usage
-----

Cloud deployment configuration schema is an extension to cloud config used by
`os-client-config <https://github.com/openstack/os-client-config>`_ library:

.. code-block:: python

    cloud_config = {
        'auth': {
            'username': 'admin',
            'password': 'admin',
            'project_name': 'admin',
        },
        'region_name': 'RegionOne',
        'cloud_management': {
            'driver': 'devstack',
            'address': 'devstack.local',
            'username': 'root',
        },
        'power_management': {
            'driver': 'kvm',
            'address': 'kvm.local',
            'username': 'root',
        }
    }

Build the connection to the cloud deployment and verify it:

.. code-block:: python

    distractor = os_failures.connect(cloud_config)
    distractor.verify()

Make some distraction:

.. code-block:: python

    distractor.get_service(name='keystone-api').restart()


The library operates with 2 types of objects:
 * `service` - is software that runs in the cloud, e.g. `keystone-api`
 * `nodes` - nodes that host the cloud, e.g. hardware server with hostname


Simplified API
--------------

Simplified API is used to specify particular failures in a text form.
The query format is following:
``<action> [one] <subject> node|service``

Actions:
 * restart
 * terminate
 * kill
 * start
 * unplug
 * plug
 * reset
 * power off
 * power on
Subject is the name of the service or name of the node.

Examples:

 * `Restart Keystone service` - restarts Keystone service in the whole cloud
 * `Reboot one MySQL node` - reboots random node with MySQL
 * `Reboot node-2.domain.tld` - reboot node with specified name


Extended API
------------

1. Service actions
~~~~~~~~~~~~~~~~~~

Get a service and restart it:

.. code-block:: python

    distractor = os_failures.connect(cloud_config)
    service = distractor.get_service(name='keystone-api')
    service.restart()

Available actions:
 * `start` - start Service
 * `terminate` - terminate Service gracefully
 * `restart` - restart Service
 * `kill` - terminate Service abruptly
 * `unplug` - unplug Service out of network
 * `plug` - plug Service into network

2. Nodes operations
~~~~~~~~~~~~~~~~~~~

Get all nodes in the cloud and reboot them:

.. code-block:: python

    nodes = distractor.get_nodes()
    nodes.reboot()

Available actions:
 * `reboot` - reboot all nodes gracefully
 * `poweroff` - power off all nodes abruptly
 * `reset` - reset (cold restart) all nodes
 * `oom` - fill all node's RAM
 * `disable_network` - disable network with specified name on each of the nodes
 * `enable_network` - enable network with specified name on each of the nodes

3. Operate with service's nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get all nodes where the service runs, pick one of them and reset:

.. code-block:: python

    nodes = service.get_nodes()
    one = nodes.pick()
    one.reset()

4. Operate with nodes by their FQDNs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get nodes where l3-agent runs and disable management network on that nodes:

.. code-block:: python

    fqdns = neutron.l3_agent_list_hosting_router(router_id)
    nodes = distractor.get_nodes(fqdns=fqdns)
    nodes.disable_network(network_name='management')

5. Operate with service on particular node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Restart service on a single node:

.. code-block:: python

    service = distractor.get_service(name='keystone-api')
    nodes = service.get_nodes().pick()
    service.restart(nodes)

