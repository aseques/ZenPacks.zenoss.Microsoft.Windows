##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from mock import Mock, sentinel

from Products.ZenTestCase.BaseTestCase import BaseTestCase
from ZenPacks.zenoss.Microsoft.Windows.tests.utils import StringAttributeObject, load_pickle

from ZenPacks.zenoss.Microsoft.Windows.modeler.plugins.zenoss.winrm.Interfaces import (
    Interfaces,
    filter_maps,
)


class TestInterfaces(BaseTestCase):
    def setUp(self):
        self.results = load_pickle(self, 'results')
        self.device = load_pickle(self, 'device')
        self.plugin = Interfaces()

    def test_process(self):
        data = self.plugin.process(self.device, self.results, Mock())
        self.assertEquals(len(data.maps), 13)

        eth0 = data.maps[12]
        self.assertEquals(eth0.adminStatus, 1)
        self.assertEquals(eth0.description, "Local Area Connection 2")
        self.assertEquals(eth0.duplex, 0)
        self.assertEquals(eth0.id, "12-Intel_R_ PRO_1000 MT Network Connection")
        self.assertEquals(eth0.ifindex, '14')
        self.assertEquals(eth0.interfaceName, "Intel(R) PRO/1000 MT Network Connection")
        self.assertEquals(eth0.macaddress, "00:50:56:8D:45:FC")
        self.assertEquals(eth0.perfmonInstance, "\\Network Interface(Intel[R] PRO_1000 MT Network Connection)")
        self.assertEquals(eth0.setIpAddresses, ['192.168.240.37/23', 'fe80::a930:96ad:f65e:b3ba/64'])
        self.assertEquals(eth0.speed, 1000000000)
        self.assertEquals(eth0.title, "Intel(R) PRO/1000 MT Network Connection")
        self.assertEquals(eth0.type, "Ethernet 802.3")

    def test_sanitize_counters(self):
        counters = Mock()
        counters.stdout = "a:None|a:a|"
        self.assertIsNone(self.plugin.sanitize_counters(None))
        self.assertEquals(self.plugin.sanitize_counters(counters), {'a': 'a'})


class TestHelpers(BaseTestCase):
    def test_filter_maps(self):
        om0 = StringAttributeObject()
        om1 = StringAttributeObject()
        om2 = StringAttributeObject()

        device = StringAttributeObject()
        for objectmap, attribute, prop in zip(
                (om0, om1, om2),
                ('description', 'interfaceName', 'type'),
                ('zInterfaceMapIgnoreDescriptions', 'zInterfaceMapIgnoreNames', 'zInterfaceMapIgnoreTypes')
        ):
            setattr(objectmap, attribute, 'ignore')
            setattr(device, prop, 'ignore')

        self.assertFalse(list(filter_maps([om0, om1, om2], device, Mock())))
