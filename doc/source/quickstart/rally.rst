=================
OS-Faults + Rally
=================

Combination of OS-Faults and `Rally`_ gives a powerful tool to test OpenStack high availability
and fail-over under the load.

Fault injection is implemented with help of Rally `Fault Injection Hook`_. Following
is an example of Rally scenario performing Keystone authentication with restart of one of
Memcached services:

.. code-block:: yaml

    ---
      Authenticate.keystone:
        -
          runner:
            type: "constant_for_duration"
            duration: 30
            concurrency: 5
          context:
            users:
              tenants: 1
              users_per_tenant: 1
          hooks:
            -
              name: fault_injection
              args:
                action: restart memcached service on one node
              trigger:
                name: event
                args:
                  unit: iteration
                  at: [100]

The moment of fault injection can be specified as iteration number or in time relative
to the beginning of the test:

.. code-block:: yaml

              trigger:
                name: event
                args:
                  unit: time
                  at: [10]

Parameter `action` contains fault specification in human-friendly format, see
:ref:`Human API` for details.

More on reliability testing of OpenStack:

 * `Reliability Test Plan`_ in OpenStack performance documentation
 * `Keystone authentication with restart memcached report`_ collected in OpenStack deployed by Fuel
 * `Introduction into reliability metrics`_ video cast


.. references:
.. _Rally: http://rally.readthedocs.io
.. _Fault Injection Hook: http://docs.xrally.xyz/projects/openstack/en/0.10.0/plugins/plugin_reference.html?highlight=fault_injection#fault-injection-hook-action
.. _Reliability Test Plan: https://docs.openstack.org/performance-docs/latest/test_plans/reliability/version_2/plan.html
.. _Keystone authentication with restart memcached report: https://docs.openstack.org/performance-docs/latest/test_results/reliability/version_2/reports/keystone/authenticate_with_restart_memcached_service_on_one_node/index.html
.. _Introduction into reliability metrics: https://youtu.be/MIj4clkKtfY
