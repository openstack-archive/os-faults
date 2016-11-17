# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ddt
import mock

from os_faults.drivers import libvirt_driver
from os_faults import error
from os_faults.tests.unit import test


DRIVER_PATH = 'os_faults.drivers.libvirt_driver'


@ddt.ddt
class LibvirtDriverTestCase(test.TestCase):

    def setUp(self):
        super(LibvirtDriverTestCase, self).setUp()

        self.params = {'connection_uri': 'fake_connection_uri'}
        self.driver = libvirt_driver.LibvirtDriver(self.params)

    @mock.patch('libvirt.open')
    def test__get_connection_no_cached_connection(self, mock_libvirt_open):
        self.driver._get_connection()
        self.assertNotEqual(self.driver._cached_conn, None)

        mock_libvirt_open.assert_called_once_with(
            self.params['connection_uri'])

    def test__get_connection_cached_connection(self):
        self.driver._cached_conn = 'some cached connection'

        conn = self.driver._get_connection()
        self.assertEqual(conn, 'some cached connection')

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._get_connection')
    def test__find_domain_by_mac_address(self, mock__get_connection):
        domain1 = mock.MagicMock()
        domain1.XMLDesc.return_value = '52:54:00:ab:64:42'
        domain2 = mock.MagicMock()
        domain2.XMLDesc.return_value = '52:54:00:f9:b8:f9'
        self.driver.conn.listAllDomains.return_value = [domain1, domain2]

        domain = self.driver._find_domain_by_mac_address('52:54:00:f9:b8:f9')
        self.assertEqual(domain, domain2)

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._get_connection')
    def test__find_domain_by_mac_address_domain_not_found(
            self, mock__get_connection):
        domain1 = mock.MagicMock()
        domain1.XMLDesc.return_value = '52:54:00:ab:64:42'
        domain2 = mock.MagicMock()
        domain2.XMLDesc.return_value = '52:54:00:f9:b8:f9'
        self.driver.conn.listAllDomains.return_value = [domain1, domain2]

        self.assertRaises(error.PowerManagementError,
                          self.driver._find_domain_by_mac_address,
                          '00:00:00:00:00:01')

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_mac_address')
    @ddt.data(('_poweroff', 'destroy'), ('_poweron', 'create'),
              ('_reset', 'reset'))
    def test__driver_actions(self, actions, mock__find_domain_by_mac_address):
        getattr(self.driver, actions[0])('52:54:00:f9:b8:f9')
        domain = mock__find_domain_by_mac_address.return_value
        getattr(domain, actions[1]).assert_called_once_with()

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_mac_address')
    def test__snapshot(self, mock__find_domain_by_mac_address):
        self.driver._snapshot('52:54:00:f9:b8:f9', 'foo')
        domain = mock__find_domain_by_mac_address.return_value
        domain.snapshotCreateXML.assert_called_once_with(
            '<domainsnapshot><name>foo</name></domainsnapshot>')

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_mac_address')
    def test__revert(self, mock__find_domain_by_mac_address):
        self.driver._revert('52:54:00:f9:b8:f9', 'foo', resume=False)
        domain = mock__find_domain_by_mac_address.return_value
        snapshot = domain.snapshotLookupByName.return_value
        domain.snapshotLookupByName.assert_called_once_with('foo')
        domain.revertToSnapshot.assert_called_once_with(snapshot)
        self.assertFalse(domain.resume.called)

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_mac_address')
    def test__revert_resume(self, mock__find_domain_by_mac_address):
        self.driver._revert('52:54:00:f9:b8:f9', 'foo', resume=True)
        domain = mock__find_domain_by_mac_address.return_value
        snapshot = domain.snapshotLookupByName.return_value
        domain.snapshotLookupByName.assert_called_once_with('foo')
        domain.revertToSnapshot.assert_called_once_with(snapshot)
        domain.resume.assert_called_once_with()

    @mock.patch('os_faults.utils.run')
    @ddt.data('poweroff', 'poweron', 'reset')
    def test_driver_actions(self, action, mock_run):
        macs_list = ['52:54:00:f9:b8:f9', '52:54:00:ab:64:42']
        getattr(self.driver, action)(macs_list)
        mock_run.assert_called_once_with(
            getattr(self.driver, '_%s' % action),
            [{'mac_address': '52:54:00:f9:b8:f9'},
             {'mac_address': '52:54:00:ab:64:42'}])

    @mock.patch('os_faults.utils.run')
    def test_driver_snapshot(self, mock_run):
        macs_list = ['52:54:00:f9:b8:f9', '52:54:00:ab:64:42']
        self.driver.snapshot(macs_list, 'foo_snap')
        mock_run.assert_called_once_with(
            self.driver._snapshot,
            [{'mac_address': '52:54:00:f9:b8:f9',
              'snapshot_name': 'foo_snap'},
             {'mac_address': '52:54:00:ab:64:42',
              'snapshot_name': 'foo_snap'}])

    @mock.patch('os_faults.utils.run')
    def test_driver_revert(self, mock_run):
        macs_list = ['52:54:00:f9:b8:f9', '52:54:00:ab:64:42']
        self.driver.revert(macs_list, 'foo_snap', resume=False)
        mock_run.assert_called_once_with(
            self.driver._revert,
            [{'mac_address': '52:54:00:f9:b8:f9',
              'snapshot_name': 'foo_snap',
              'resume': False},
             {'mac_address': '52:54:00:ab:64:42',
              'snapshot_name': 'foo_snap',
              'resume': False}])
