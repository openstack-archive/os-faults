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

from os_faults.api import node_collection
from os_faults.drivers.power import libvirt
from os_faults import error
from os_faults.tests.unit import test


DRIVER_PATH = 'os_faults.drivers.power.libvirt'


@ddt.ddt
class LibvirtDriverTestCase(test.TestCase):

    def setUp(self):
        super(LibvirtDriverTestCase, self).setUp()

        self.params = {'connection_uri': 'fake_connection_uri'}
        self.driver = libvirt.LibvirtDriver(self.params)
        self.host = node_collection.Host(
            ip='10.0.0.2', mac='00:00:00:00:00:00', fqdn='node1.com')

    @mock.patch('oslo_utils.importutils.try_import')
    def test__get_connection_no_cached_connection(self, mock_import):
        mock_libvirt = mock_import.return_value = mock.Mock()
        mock_libvirt_open = mock_libvirt.open = mock.Mock()
        self.driver._get_connection()
        self.assertNotEqual(self.driver._cached_conn, None)

        mock_libvirt_open.assert_called_once_with(
            self.params['connection_uri'])

    def test__get_connection_cached_connection(self):
        self.driver._cached_conn = 'some cached connection'

        conn = self.driver._get_connection()
        self.assertEqual(conn, 'some cached connection')

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._get_connection')
    def test__find_domain_by_host_mac(self, mock__get_connection):
        host = node_collection.Host(ip='10.0.0.2', mac=':54:00:f9:b8:f9')
        domain1 = mock.MagicMock()
        domain1.XMLDesc.return_value = '52:54:00:ab:64:42'
        domain2 = mock.MagicMock()
        domain2.XMLDesc.return_value = '52:54:00:f9:b8:f9'
        self.driver.conn.listAllDomains.return_value = [domain1, domain2]

        domain = self.driver._find_domain_by_host(host)
        self.assertEqual(domain, domain2)

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._get_connection')
    def test__find_domain_by_host_name(self, mock__get_connection):
        host = node_collection.Host(ip='10.0.0.2', libvirt_name='foo')
        domain1 = mock.MagicMock()
        domain1.XMLDesc.return_value = '52:54:00:ab:64:42'
        domain1.name.return_value = 'bar'
        domain2 = mock.MagicMock()
        domain2.XMLDesc.return_value = '52:54:00:f9:b8:f9'
        domain2.name.return_value = 'foo'
        self.driver.conn.listAllDomains.return_value = [domain1, domain2]

        domain = self.driver._find_domain_by_host(host)
        self.assertEqual(domain, domain2)

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._get_connection')
    def test__find_domain_by_host_domain_not_found(
            self, mock__get_connection):
        host = node_collection.Host(ip='10.0.0.2')
        domain1 = mock.MagicMock()
        domain1.XMLDesc.return_value = '52:54:00:ab:64:42'
        domain2 = mock.MagicMock()
        domain2.XMLDesc.return_value = '52:54:00:f9:b8:f9'
        self.driver.conn.listAllDomains.return_value = [domain1, domain2]

        self.assertRaises(error.PowerManagementError,
                          self.driver._find_domain_by_host, host)

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._get_connection')
    def test_supports(self, mock__get_connection):
        domain1 = mock.MagicMock()
        domain1.XMLDesc.return_value = '52:54:00:ab:64:42'
        domain2 = mock.MagicMock()
        domain2.XMLDesc.return_value = '00:00:00:00:00:00'
        self.driver.conn.listAllDomains.return_value = [domain1, domain2]

        self.assertTrue(self.driver.supports(self.host))

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._get_connection')
    def test_supports_false(self, mock__get_connection):
        self.driver.conn.listAllDomains.return_value = []

        self.assertFalse(self.driver.supports(self.host))

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_host')
    @ddt.data(('poweroff', 'destroy'), ('poweron', 'create'),
              ('reset', 'reset'), ('shutdown', 'shutdown'))
    def test_driver_actions(self, actions, mock__find_domain_by_host):
        getattr(self.driver, actions[0])(self.host)
        domain = mock__find_domain_by_host.return_value
        getattr(domain, actions[1]).assert_called_once_with()

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_host')
    def test_snapshot(self, mock__find_domain_by_host):
        self.driver.snapshot(self.host, 'foo', suspend=False)
        domain = mock__find_domain_by_host.return_value
        domain.snapshotCreateXML.assert_called_once_with(
            '<domainsnapshot><name>foo</name></domainsnapshot>')

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_host')
    def test_snapshot_suspend(self, mock__find_domain_by_host):
        self.driver.snapshot(self.host, 'foo', suspend=True)
        domain = mock__find_domain_by_host.return_value
        domain.assert_has_calls((
            mock.call.suspend(),
            mock.call.snapshotCreateXML(
                '<domainsnapshot><name>foo</name></domainsnapshot>'),
            mock.call.resume(),
        ))

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_host')
    def test_revert(self, mock__find_domain_by_host):
        self.driver.revert(self.host, 'foo', resume=False)
        domain = mock__find_domain_by_host.return_value
        snapshot = domain.snapshotLookupByName.return_value
        domain.snapshotLookupByName.assert_called_once_with('foo')
        domain.revertToSnapshot.assert_called_once_with(snapshot)
        self.assertFalse(domain.resume.called)

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_host')
    def test_revert_resume(self, mock__find_domain_by_host):
        self.driver.revert(self.host, 'foo', resume=True)
        domain = mock__find_domain_by_host.return_value
        snapshot = domain.snapshotLookupByName.return_value
        domain.snapshotLookupByName.assert_called_once_with('foo')
        domain.revertToSnapshot.assert_called_once_with(snapshot)
        domain.resume.assert_called_once_with()

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_host')
    def test_revert_destroy(self, mock__find_domain_by_host):
        domain = mock__find_domain_by_host.return_value
        domain.isActive.return_value = True
        self.driver.revert(self.host, 'foo', resume=True)
        domain.destroy.assert_called_once_with()

    @mock.patch(DRIVER_PATH + '.LibvirtDriver._find_domain_by_host')
    def test_revert_destroy_nonactive(self, mock__find_domain_by_host):
        domain = mock__find_domain_by_host.return_value
        domain.isActive.return_value = False
        self.driver.revert(self.host, 'foo', resume=True)
        self.assertFalse(domain.destroy.called)
