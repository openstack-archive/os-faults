===========
os_failures
===========

OpenStack failures library

This is a library. It does different destructive actions against OpenStack
cloud. It is an abstraction layer, actions are implemented as drivers
(e.g. Fuel driver, KVM driver, IPMI driver).

* Free software: Apache license
* Documentation: http://os_failures.readthedocs.io
* Source: https://github.com/shakhat/os-failures
* Bugs: http://bugs.launchpad.net/os_failures

Sample usage
------------

.. code-block:: python

  failures_client = os_failures.build_client(cloud_params)
  failures_client.kill_rabbitmq()
