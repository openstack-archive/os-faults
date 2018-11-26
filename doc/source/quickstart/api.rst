===
API
===

The library operates with different types of objects:

    * `service` - is a software that runs in the cloud, e.g. `nova-api`
    * `containers` - is a container that runs in the cloud, e.g. `neutron-api`
    * `nodes` - nodes that host the cloud, e.g. a hardware server with a hostname


Human API
---------

Human API is used to specify faults as normal English sentences.

.. code-block:: python

    import os_faults
    cloud_management = os_faults.connect(config_filename='os-faults.yaml')
    os_faults.human_api(cloud_management, 'restart keystone service')


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
 * `oom` - fill all node's RAM
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
