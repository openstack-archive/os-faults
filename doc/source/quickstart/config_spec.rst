===========================
Configuration specification
===========================

Configuration file contains the following parameters:

    * cloud_management
    * power_managements
    * node_discover
    * services
    * containers

Each parameter specifies a driver or a list of drivers.

Example configuration:

.. code-block:: yaml

    cloud_management:
      driver: devstack
      args:
        address: 192.168.1.240
        auth:
          username: ubuntu
          iface: enp0s3

    power_managements:
    - driver: libvirt
      args:
        connection_uri: qemu+ssh://ubuntu@10.0.1.50/system

    - driver: ipmi
      args:
        fqdn_to_bmc:
          node-1.domain.tld:
            address: 120.10.30.65
            username: alex
            password: super-secret

    node_discover:
      driver: node_list
      args:
      - fqdn: node-1.domain.tld
        ip: 192.168.1.240
        mac: 1e:24:c3:75:dd:2c

    services:
      glance-api:
        driver: screen
        args:
          grep: glance-api
          window_name: g-api
        hosts:
        - 192.168.1.240

    containers:
      neutron_api:
        driver: docker_container
        args:
          container_name: neutron_api


cloud_management
----------------

This parameter specifies cloud management driver and its arguments.
``cloud_management`` is responsible for configuring connection to nodes
and contains arguments such as SSH username/password/key/proxy.

.. code-block:: yaml

    cloud_management:
      driver: devstack  # name of the driver
      args:             # arguments for the driver
        address: 192.168.1.240
        auth:
          username: ubuntu
          iface: enp0s3


Drivers can support discovering of cloud nodes. For example,
``saltcloud`` drives allow discovering information about nodes
through master/config node of the cloud.

List of supported drivers for cloud_management: :ref:`Cloud management`


power_managements
-----------------

This parameter specifies list of power management drivers. Such drivers
allow controlling power state of cloud nodes.

.. code-block:: yaml

    power_managements:
    - driver: libvirt   # name of the driver
      args:             # arguments for the driver
        connection_uri: qemu+ssh://ubuntu@10.0.1.50/system

    - driver: ipmi      # name of the driver
      args:             # arguments for the driver
        fqdn_to_bmc:
          node-1.domain.tld:
            address: 120.10.30.65
            username: alex
            password: super-secret


List of supported drivers for power_managements: :ref:`Power management`


node_discover
-------------

This parameter specifies node discover driver. ``node_discover`` is responsible
for fetching list of hosts for the cloud. If ``node_discover`` is specified in
configuration then ``cloud_management`` will only control connection options to
the nodes.

.. code-block:: yaml

    node_discover:
      driver: node_list
      args:
      - fqdn: node-1.domain.tld
        ip: 192.168.1.240
        mac: 1e:24:c3:75:dd:2c

List of supported drivers for node_discover: :ref:`Node discover`


services
--------

This parameter specifies list of services and their types. This parameter
allows updating/adding services which are embedded in ``cloud_management``
driver.

.. code-block:: yaml

    services:
      glance-api:            # name of the service
        driver: screen       # name of the service driver
        args:                # arguments for the driver
          grep: glance-api
          window_name: g-api
        hosts:               # list of hosts where this service running
        - 192.168.1.240
      mysql:                 # name of the service
        driver: process      # name of the service driver
        args:                # arguments for the driver
          grep: mysqld
          port:
          - tcp
          - 3307
          restart_cmd: sudo service mysql restart
          start_cmd: sudo service mysql start
          terminate_cmd: sudo service mysql stop


Service driver contains optional ``hosts`` parameter which controls discovering
of hosts where the service is running. If ``hosts`` specified, then service
discovering is disabled for this service and hosts specified in ``hosts`` will
be used, otherwise, service will be searched across all nodes.

List of supported drivers for services: :ref:`Service drivers`


containers
----------

This parameter specifies list of containers and their types. This parameter
allows updating/adding containers which are embedded in ``cloud_management``
driver.

.. code-block:: yaml

    containers:
      neutron_api:                     # name of the container
        driver: docker_container       # name of the container driver
        args:                          # arguments for the driver
          container_name: neutron_api
        hosts:                         # list of hosts where this container running
        - 192.168.1.240


Container driver contains optional ``hosts`` parameter which controls discovering
of hosts where the container is running. If ``hosts`` specified, then container
discovering is disabled for this container and hosts specified in ``hosts`` will
be used, otherwise, container will be searched across all nodes.

List of supported drivers for containers: :ref:`Container drivers`
