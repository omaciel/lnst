from lnst.Common.LnstError import LnstError
from lnst.Common.Parameters import IntParam, Param, StrParam, BoolParam
from lnst.Common.IpAddress import ipaddress, AF_INET, AF_INET6

from lnst.Controller import HostReq, DeviceReq, RecipeParam

from lnst.Recipes.ENRT.BaseEnrtRecipe import BaseEnrtRecipe

from lnst.Recipes.ENRT.ConfigMixins.OffloadSubConfigMixin import (
    OffloadSubConfigMixin,
)
from lnst.Recipes.ENRT.ConfigMixins.CommonHWConfigMixin import (
    CommonHWConfigMixin,
)


class SimplePerfRecipe(
    OffloadSubConfigMixin, CommonHWConfigMixin, BaseEnrtRecipe
):
    host1 = HostReq()
    host1.eth0 = DeviceReq(label="net1", driver=RecipeParam("driver"))

    host2 = HostReq()
    host2.eth0 = DeviceReq(label="net1", driver=RecipeParam("driver"))

    offload_combinations = Param(default=(
        dict(gro="on", gso="on", tso="on", tx="on", rx="on"),
        dict(gro="off", gso="on", tso="on", tx="on", rx="on"),
        dict(gro="on", gso="off", tso="off", tx="on", rx="on"),
        dict(gro="on", gso="on", tso="off", tx="off", rx="on"),
        dict(gro="on", gso="on", tso="on", tx="on", rx="off")))

    def test_wide_configuration(self):
        host1, host2 = self.matched.host1, self.matched.host2
        configuration = super().test_wide_configuration()
        configuration.test_wide_devices = []

        host1.eth0.ip_add(ipaddress("192.168.101.1/24"))
        host1.eth0.ip_add(ipaddress("fc00::1/64"))
        host1.eth0.up()
        configuration.test_wide_devices.append(host1.eth0)

        host2.eth0.ip_add(ipaddress("192.168.101.2/24"))
        host2.eth0.ip_add(ipaddress("fc00::2/64"))
        host2.eth0.up()
        configuration.test_wide_devices.append(host2.eth0)


        return configuration

    def generate_test_wide_description(self, config):
        desc = super().generate_test_wide_description(config)
        desc += [
            "Configured {}.{}.ips = {}".format(
                dev.host.hostid, dev.name, dev.ips
            )
            for dev in config.test_wide_devices
        ]
        return desc

    def test_wide_deconfiguration(self, config):
        del config.test_wide_devices

        super().test_wide_deconfiguration(config)

    def generate_ping_endpoints(self, config):
        return [(self.matched.host1.eth0, self.matched.host2.eth0)]

    def generate_perf_endpoints(self, config):
        return [(self.matched.host1.eth0, self.matched.host2.eth0)]

    @property
    def offload_nics(self):
        return [self.matched.host1.eth0, self.matched.host2.eth0]

    @property
    def hw_config_dev_list(self):
        return [self.matched.host1.eth0, self.matched.host2.eth0]
