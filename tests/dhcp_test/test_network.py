from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo

def disable_ipv6(node):
    node.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    node.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    node.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")


def ping(host, dst, count=1, timeout=1):
    return host.cmd('ping -c %s -W %s %s' % (count, timeout, dst))

def send_arp(node, count=1):
    node.cmd('arping -c %s -A -I %s-eth0 %s' % (count, node.name, node.IP()))

def send_dhcp(node):
    print('Sending DHCP request dhclient -v %s-eth0 '% (node.name))
    node.cmd('dhclient -v %s-eth0' % (node.name))


def do_arp_all(net):
    for h in net.hosts:
        send_arp(h)


class TestTopo(Topo):

    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        # h1 = self.addHost('h1', ip='no ip defined/8')
        s1 = self.addSwitch('s1')
        # self.addLink(h1, s1)
        self.datapath = s1

    def add_n_host(self,m):
        for i in range(1,m+1):
            h = self.addHost(f'h{i}',ip='no ip defined/8')
            self.addLink(h,self.datapath)


def test_case(host_num):
    topo = TestTopo()
    topo.add_n_host(host_num)
    net = Mininet(topo=topo, autoSetMacs=True, controller=RemoteController)
    for h in net.hosts:
        disable_ipv6(h)
    for h in net.switches:
        disable_ipv6(h)
    
    net.start()
    for h in net.hosts:
        send_dhcp(h)
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    test_case(15)
