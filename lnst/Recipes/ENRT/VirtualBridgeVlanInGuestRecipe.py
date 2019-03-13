"""
Implements scenario similar to regression_tests/phase1/
(virtual_bridge_vlan_in_guest.xml + virtual_bridge_vlan_in_guest.py)
"""
from lnst.Common.Parameters import Param
from lnst.Common.IpAddress import ipaddress
from lnst.Controller import HostReq, DeviceReq
from lnst.Recipes.ENRT.BaseEnrtRecipe import BaseEnrtRecipe, EnrtConfiguration
from lnst.Devices import VlanDevice
from lnst.Devices import BridgeDevice
from lnst.Common.LnstError import LnstError

class VirtualBridgeVlanInGuestRecipe(BaseEnrtRecipe):
    host1 = HostReq()
    host1.eth0 = DeviceReq(label="to_switch")
    host1.tap0 = DeviceReq(label="to_guest")

    host2 = HostReq()
    host2.eth0 = DeviceReq(label="to_switch")

    guest1 = HostReq()
    guest1.eth0 = DeviceReq(label="to_guest")

    offload_combinations = Param(default=(
        dict(gro="on", gso="on", tso="on", tx="on", rx="on"),
        dict(gro="off", gso="on", tso="on", tx="on", rx="on"),
        dict(gro="on", gso="off", tso="off", tx="on", rx="on"),
        dict(gro="on", gso="on", tso="off", tx="off", rx="on"),
        dict(gro="on", gso="on", tso="on", tx="on", rx="off")))

    def test_wide_configuration(self):
        host1, host2, guest1 = self.matched.host1, self.matched.host2, self.matched.guest1

        host1.eth0.down()
        host1.tap0.down()
        host1.br0 = BridgeDevice()
        host1.br0.slave_add(host1.eth0)
        host1.br0.slave_add(host1.tap0)

        host2.eth0.down()
        host2.vlan1 = VlanDevice(realdev=host2.eth0, vlan_id=10)

        guest1.eth0.down()
        guest1.vlan1 = VlanDevice(realdev=guest1.eth0, vlan_id=10)

        #Due to limitations in the current EnrtConfiguration
        #class, a single vlan test pair is chosen
        configuration = EnrtConfiguration()
        configuration.endpoint1 = guest1.vlan1
        configuration.endpoint2 = host2.vlan1

        if "mtu" in self.params:
            host1.eth0.mtu = self.params.mtu
            host1.tap0.mtu = self.params.mtu
            host1.br0.mtu = self.params.mtu
            guest1.eth0.mtu = self.params.mtu
            guest1.vlan1.mtu = self.params.mtu
            host2.eth0.mtu = self.params.mtu

        net_addr_1 = "192.168.10"
        net_addr6_1 = "fc00:0:0:1"

        host1.br0.ip_add(ipaddress(net_addr_1 + ".1/24"))
        host2.vlan1.ip_add(ipaddress(net_addr_1 + ".2/24"))
        host2.vlan1.ip_add(ipaddress(net_addr6_1 + "::2/64"))
        guest1.vlan1.ip_add(ipaddress(net_addr_1 + ".3/24"))
        guest1.vlan1.ip_add(ipaddress(net_addr6_1 + "::3/64"))

        host1.eth0.up()
        host1.tap0.up()
        host1.br0.up()
        host2.eth0.up()
        host2.vlan1.up()
        guest1.eth0.up()
        guest1.vlan1.up()

        #TODO better service handling through HostAPI
        if "dev_intr_cpu" in self.params:
            raise LnstError("'dev_intr_cpu' (%d) should not be set for this test" % self.params.dev_intr_cpu)

        if "perf_tool_cpu" in self.params:
            for m in [host1, host2]:
                m.run("service irqbalance stop")
                self._pin_dev_interrupts(m.eth0, 0)

        return configuration

    def test_wide_deconfiguration(self, config):
        host1, host2, guest1 = self.matched.host1, self.matched.host2, self.matched.guest1

        #TODO better service handling through HostAPI
        if "perf_tool_cpu" in self.params:
            for m in [host1, hpst2]:
                m.run("service irqbalance start")