======
Basics
======


Configuration file
------------------

The cloud deployment configuration schema is an extension to the cloud config
used by the `os-client-config <https://github.com/openstack/os-client-config>`_
library:

.. code-block:: yaml

    cloud_management:
      driver: devstack
      args:
        address: 192.168.1.240
        username: ubuntu
        iface: enp0s3

    power_managements:
    - driver: libvirt
      args:
        connection_uri: qemu+ssh://ubuntu@10.0.1.50/system


By default, the library reads configuration from a file and the file can be in
the following three formats: ``os-faults.{json,yaml,yml}``. The configuration
file will be searched in the default locations:

    * current directory
    * ~/.config/os-faults
    * /etc/openstack

Also, the configuration file can be specified in the ``OS_FAULTS_CONFIG``
environment variable::

    $ export OS_FAULTS_CONFIG=/home/alex/my-os-faults-config.yaml


Running
-------

Establish a connection to the cloud and verify it:

.. code-block:: python

    import os_faults
    destructor = os_faults.connect(config_filename='os-faults.yaml')
    destructor.verify()


or via CLI::

    $ os-faults verify -c os-faults.yaml


Make some destructive actions:

.. code-block:: python

    destructor.get_service(name='keystone').restart()


or via CLI::

    $ os-inject-fault -c os-faults.yaml restart keystone service
