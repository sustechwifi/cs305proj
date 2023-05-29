from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event
from ryu.ofproto import ofproto_v1_0
from ryu.lib.packet import ether_types, arp
from ryu.lib.packet import dhcp
from ryu.lib.packet import ethernet
from ryu.lib.packet import packet
from dhcp import DHCPServer

from ofctl_utilis import OfCtl, VLANID_NONE

# conda activate cs305
# sudo mn -c
# ryu-manager --observe-links controller.py

# cd ./tests/switching_test/
# sudo env "PATH=$PATH" python test_network.py # share the PATN env with sudo user

class ControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ControllerApp, self).__init__(*args, **kwargs)
        self.switchNum = 0
        self.s_s = []  # 两个switch之间的距,邻接矩阵
        self.numInfo = []
        self.switch_num_real = {}  # switch id->switchNum
        self.switch_real_num = {}  # switchNum-> switch id
        self.port = []
        self.Hip_Hmac = {}  # host ip->host mac
        self.Hmac_Smac = {}  # host mac->switch mac
        self.Smac_Sport = {}  # switch mac->switch port
        self.mac_mac = {}  # hardware address
        self.Smac_Sid = {}  # switch mac->switch id
        self.Hip_Hid = {}  # host ip->host id
        self.Sid_Sswitch = {}  # switch id->switch
        self.s_s.append([])
        self.numInfo.append([])
        self.leaveSwitchList = []
        self.DelPortList = []

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev):
        switch = ev.switch
        dp = switch.dp
        self.Sid_Sswitch[dp.id] = dp
        self.switchNum += 1
        self.s_s.append([])
        self.numInfo.append([])
        for port in switch.ports:
            self.Smac_Sport[port.hw_addr] = port.port_no
            self.numInfo[self.switchNum].append(port.hw_addr)
            self.s_s[self.switchNum].append(0)
            self.Smac_Sid[port.hw_addr] = self.switchNum
        self.switch_real_num[switch.dp.id] = self.switchNum
        self.switch_num_real[self.switchNum] = switch.dp.id
        self.update()

    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev):
        switch = ev.switch
        temp_num = self.switch_real_num[switch.dp.id]
        self.leaveSwitchList.append(temp_num)
        for mac in self.numInfo[temp_num]:
            if mac in self.mac_mac:
                del self.mac_mac[self.mac_mac[mac]]
                del self.mac_mac[mac]
        self.update()

    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev):
        host = ev.host
        self.Hip_Hmac[host.ipv4[0]] = host.mac
        self.Hmac_Smac[host.mac] = host.port.hw_addr
        self.Hip_Hid[host.ipv4[0]] = host.port.dpid
        self.update()

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        link = ev.link
        src_port = link.src
        dst_port = link.dst
        self.mac_mac[src_port.hw_addr] = dst_port.hw_addr
        self.mac_mac[dst_port.hw_addr] = src_port.hw_addr
        self.update()

    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        link = ev.link
        src_port = link.src
        dst_port = link.dst
        if src_port.hw_addr in self.mac_mac:
            del self.mac_mac[src_port.hw_addr]
        if dst_port.hw_addr in self.mac_mac:
            del self.mac_mac[dst_port.hw_addr]
        self.update()

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        port = ev.port
        a = self.Smac_Sid[port.hw_addr]
        if port.hw_addr in self.mac_mac:
            b = self.Smac_Sid[self.mac_mac[port.hw_addr]]
            if port.hw_addr in self.DelPortList:
                self.DelPortList.remove(port.hw_addr)
                self.s_s[a][b] = 1
                self.s_s[b][a] = 1
            else:
                self.DelPortList.append(port.hw_addr)
                if port.hw_addr in self.mac_mac:
                    self.s_s[a][b] = 10000000
                    self.s_s[b][a] = 10000000
        self.update()

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        try:
            msg = ev.msg
            dp = msg.datapath
            ofctl = OfCtl.factory(dp, self.logger)
            in_port = msg.in_port
            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            pkt_dhcp = pkt.get_protocols(dhcp.dhcp)
            if not pkt_dhcp:
                if eth.ethertype == ether_types.ETH_TYPE_ARP:
                    arp_msg = pkt.get_protocols(arp.arp)[0]
                    if arp_msg.opcode == arp.ARP_REQUEST:
                        path = self.get_path(arp_msg.src_ip, arp_msg.dst_ip)
                        src_mac = self.Hip_Hmac[arp_msg.src_ip]
                        dst_mac = self.Hip_Hmac[arp_msg.dst_ip]
                        print("The distance from host_" + str(src_mac) + " to host_" + str(dst_mac) + " : " + str(
                            len(path) + 1))
                        s = "Path : host_"
                        s += str(src_mac)
                        for p in path:
                            s += " -> switch_"
                            s += str(p[0])
                        s += " -> host_"
                        s += str(dst_mac)
                        print(s)
                        ofctl.send_arp(
                            vlan_id=VLANID_NONE,
                            src_port=ofctl.dp.ofproto.OFPP_CONTROLLER,
                            dst_mac=arp_msg.src_mac,
                            sender_ip=arp_msg.dst_ip,
                            sender_mac=self.Hip_Hmac[arp_msg.dst_ip],
                            target_ip=arp_msg.src_ip,
                            target_mac=arp_msg.src_mac,
                            output_port=self.Smac_Sport[self.Hmac_Smac[arp_msg.src_mac]],
                            arp_opcode=2
                        )
                pass
            else:
                DHCPServer.handle_dhcp(dp, in_port, pkt)
            return
        except Exception as e:
            self.logger.error(e)

    def update(self):
        self.s_s = [[1000000 for _ in range(self.switchNum + 1)] for _ in range(self.switchNum + 1)]
        for i in range(1, self.switchNum + 1):
            self.s_s[i][i] = 0
        for key in self.mac_mac:
            macA = key
            macB = self.mac_mac[key]
            a = self.Smac_Sid[macA]
            b = self.Smac_Sid[macB]
            self.s_s[a][b] = 1
        for k in range(1, self.switchNum + 1):
            for i in range(1, self.switchNum + 1):
                for j in range(1, self.switchNum + 1):
                    if self.s_s[i][k] + self.s_s[k][j] < self.s_s[i][j]:
                        self.s_s[i][j] = self.s_s[i][k] + self.s_s[k][j]
        self.set_flowtable()
        self.print_path()

    def add_forwarding_rule(self, dp, dl_dst, port):
        ofctl = OfCtl.factory(dp, self.logger)
        actions = [dp.ofproto_parser.OFPActionOutput(port)]
        ofctl.set_flow(cookie=0,
                       priority=0,
                       dl_type=ether_types.ETH_TYPE_IP,
                       dl_vlan=VLANID_NONE,
                       dl_dst=dl_dst,
                       actions=actions)

    def delete_forwarding_rule(self, dp, dl_dst):
        ofctl = OfCtl.factory(dp, self.logger)
        match = dp.ofproto_parser.OFPMatch(dl_dst=dl_dst)
        ofctl.delete_flow(cookie=0,
                          priority=0,
                          match=match)

    def print_path(self):
        host_table = self.get_hostTable()
        ad_table = self.get_linkTable()
        for index in range(len(ad_table)):
            if index != 0:
                string = 'Switch' + str(index) + ':'
                for tuple in ad_table[index]:
                    string += 'port' + str(tuple[1]) + '->Switch' + str(tuple[0]) + ' | '
                for host in host_table:
                    if host[1] == index:
                        string += 'port' + str(host[2]) + '->Host-' + str(host[0]) + ' | '
                self.logger.info(string)

    def get_path(self, src_ip, dst_ip):
        startMac = self.Hmac_Smac[self.Hip_Hmac[src_ip]]
        endMac = self.Hmac_Smac[self.Hip_Hmac[dst_ip]]
        startNum = self.Smac_Sid[startMac]
        endNum = self.Smac_Sid[endMac]
        temp_Num = startNum
        ans_list = []

        while temp_Num != endNum:
            minDistance = self.s_s[temp_Num][endNum]
            nextNum = temp_Num
            outputNum = self.switch_num_real[temp_Num]
            outputPort = -1
            for mac in self.numInfo[temp_Num]:
                if mac in self.mac_mac:
                    tempNum = self.Smac_Sid[self.mac_mac[mac]]
                    if self.s_s[tempNum][endNum] < minDistance:
                        nextNum = tempNum
                        minDistance = self.s_s[tempNum][endNum]
                        outputPort = self.Smac_Sport[mac]
            ans_list.append((outputNum, outputPort))
            testNum = temp_Num
            temp_Num = nextNum
            if testNum == temp_Num:
                return []
        lastNum = self.switch_num_real[endNum]
        lastPort = self.Smac_Sport[endMac]
        ans_list.append((lastNum, lastPort))
        return ans_list

    def set_flowtable(self):
        ipList = []  # 所有ip
        for key in self.Hip_Hmac:
            ipList.append(key)
        # 任意两个ip之间都添加对应的流表
        for ip1 in ipList:
            for ip2 in ipList:
                if ip1 != ip2:
                    path_list = self.get_path(ip1, ip2)
                    for path in path_list:
                        # 先删除旧流表再添加流表
                        self.delete_forwarding_rule(self.Sid_Sswitch[path[0]], self.Hip_Hmac[ip2])
                        self.add_forwarding_rule(self.Sid_Sswitch[path[0]], self.Hip_Hmac[ip2], path[1])

    def get_linkTable(self):
        table = []
        for i in range(self.switchNum + 1):
            table.append([])
        for link in self.numInfo:
            for mac in link:
                if mac in self.mac_mac:
                    start = self.switch_num_real[self.Smac_Sid[mac]]
                    aim = self.switch_num_real[self.Smac_Sid[self.mac_mac[mac]]]
                    port = self.Smac_Sport[mac]
                    table[start].append([aim, port])
        return table

    def get_hostTable(self):
        table = []
        for i in self.Hip_Hid:
            mac = self.Hip_Hmac[i]
            aimMac = self.Hmac_Smac[mac]
            aimFake = self.Smac_Sid[aimMac]
            aim = self.switch_num_real[aimFake]
            port = self.Smac_Sport[aimMac]
            table.append((i, aim, port))
        return table
