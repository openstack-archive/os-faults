============
Installation
============

At the command line::

    $ pip install os-faults

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv os-faults
    $ pip install os-faults

The library contains optional libvirt driver, if you plan to use it,
please use the following command to install os-faults with extra dependencies::

    pip install os-faults[libvirt]


The library relies on Ansible which needs to be installed separately.
Please refer to [https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html]
for installation instructions.
