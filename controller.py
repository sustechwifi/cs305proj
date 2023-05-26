from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.ofproto import ofproto_v1_0
from ryu.lib.packet import packet, ethernet, ether_types, arp
from ryu.lib.packet import dhcp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import packet
from ryu.lib.packet import udp
from dhcp import DHCPServer
import heapq

from collections import defaultdict


# conda activate cs305
# ryu-manager --observe-links controller.py 

# cd ./tests/switching_test/
# sudo env "PATH=$PATH" python test_network.py # share the PATN env with sudo user


class ControllerApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ControllerApp, self).__init__(*args, **kwargs)
        self.datapath_list = defaultdict(dict)
        self.switches = defaultdict(dict)
        self.host = defaultdict(dict) #ip -> mac
        self.graph = defaultdict(dict) 
        self.host_switch = defaultdict(dict)  # host_ip->switch_id
        self.switch_mac = defaultdict(dict)  # switch_id->host_mac
        

    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev):
        switch = ev.switch.dp

        if switch.id not in self.switches:
            self.switches[switch.id]=switch.ports
            self.datapath_list[switch.id] = switch


        print("switch_enter_handler called \n\n")

        pass


    # @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    # def switch_features_handler(self, ev):

    #     print("switch_features_handler called\n")

    #     print("\n")

    #     switch = ev.msg.datapath

    #     # 获取交换机特性信息
    #     # datapath_id = switch.id
    #     # n_buffers = ev.msg.n_buffers
    #     # n_tables = ev.msg.n_tables
    #     # capabilities = ev.msg.capabilities

    #     ofproto = switch.ofproto
    #     parser = switch.ofproto_parser

    #     match = parser.OFPMatch()

    #     actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]

    #     mod = parser.OFPFlowMod(
    #         datapath=switch,
    #         match=match,
    #         command=ofproto_v1_0.OFPFC_ADD,
    #         idle_timeout=0,
    #         hard_timeout=0,
    #         priority=0,
    #         actions=actions
    #     )

            
    #     switch.send_msg(mod)

    #     pass



    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev):

        print("handle_switch_delete called \n  ")

        """
        Event handler indicating a switch has been removed
        """

        switch = ev.switch.dp
        if switch.id in self.switches:
            del self.switches[switch.id]
            del self.datapath_list[switch.id]
            del self.graph[switch.id]

        for i in self.graph:
            if switch.id in self.graph[i]:
                del self.graph[i][switch.id]
            
        if len(self.switches) >=3:   
            for i in self.switches:
                for j in self.switches:
                    if i!=j:
                        path = self.dijkstra(i,j)

                        if path:
                            src_mac = self.switch_mac[i]
                            dst_mac = self.switch_mac[j]
                            
                            print("The distance from host_"+str(src_mac)+" to host_"+str(dst_mac)+" : "+str(len(path)+2))
                            s="Path : host_"
                            s+=str(src_mac)
                            for p in path:
                                s+=" -> swtich_"
                                s+=str(p[1])
                            s+=" -> host_"
                            s+=str(dst_mac)                        
                            print(s)
        

        pass


    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev):

        host =ev.host
        ip = host.ipv4[0]
        mac =host.mac
        switch = host.port.dpid

        self.switch_mac[switch]=mac

        self.host_switch[ip] = switch

        self.host[ip]=mac

        print("handle_host_add called \n  ")

        """
        Event handler indiciating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """ 
        # TODO:  Update network topology and flow rules

        pass

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        """
        Event handler indicating a link between two switches has been added
        """
        # TODO:  Update network topology and flow rules
        link = ev.link

        print(link)

        src_dpid = link.src.dpid
        dst_dpid = link.dst.dpid
        src_port = link.src.port_no
        dst_port = link.dst.port_no
        
        self.graph[src_dpid][dst_dpid] = (src_port,1)
        self.graph[dst_dpid][src_dpid] = (dst_port,1)

        print("handle_link_add called \n  ")

        pass



    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):

        s1 = ev.link.src
        s2 = ev.link.dst
        try:
            del self.graph[s1.dpid][s2.dpid]
            del self.graph[s2.dpid][s1.dpid]
        except KeyError:
            pass

        print("handle_link_delete called \n  ")

        pass
   
        

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):

        print("handle_port_modify called \n  ")

        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        # TODO:  Update network topology and flow rules
        pass



    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        try:
            msg = ev.msg
            datapath = msg.datapath
            pkt1 = packet.Packet(data=msg.data)
            pkt_dhcp = pkt1.get_protocols(dhcp.dhcp)
            inPort = msg.in_port
           
            arp_pkt = pkt1.get_protocol(arp.arp)

            if not pkt_dhcp:
                # TODO: handle other protocols like ARP 
                if arp_pkt:
                    pkt = packet.Packet(msg.data)
                    eth_pkt = pkt.get_protocol(ethernet.ethernet)

                    print("arp pkt called\n")
                    if arp_pkt.opcode == arp.ARP_REQUEST:
                        src_ip = arp_pkt.src_ip
                        dst_ip = arp_pkt.dst_ip
                        src_mac = eth_pkt.src
                        dst_mac = self.host.get(dst_ip)
                        
                        if dst_mac is not None:
                            path = self.dijkstra(self.host_switch[src_ip], self.host_switch[dst_ip])
                            self.add_flow(path,src_ip,dst_ip)

                            print("The distance from host_"+str(src_mac)+" to host_"+str(dst_mac)+" : "+str(len(path)+2))
                            s="Path : host_"
                            s+=str(src_mac)
                            for p in path:
                                s+=" -> swtich_"
                                s+=str(p[1])
                            s+=" -> host_"
                            s+=str(dst_mac)                        
                            print(s)
                pass
            else:
                DHCPServer.handle_dhcp(datapath, inPort, pkt1)      
            return 
        except Exception as e:
            self.logger.error(e)




    def add_flow(self, path, src_ip,dst_ip):
        print("add flow called\n\n")

        for switch_id, out_port in path:
            datapath = self.datapath_list[switch_id]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            match = datapath.ofproto_parser.OFPMatch(
                nw_src=src_ip,
                nw_dst=dst_ip
            )

            actions = [parser.OFPActionOutput(out_port)]
            mod = parser.OFPFlowMod(
                datapath=datapath,
                match=match,
                command=ofproto.OFPFC_ADD,
                idle_timeout=0,
                hard_timeout=0,
                priority=1,
                actions=actions
            )

            datapath.send_msg(mod)


       
    def dijkstra(self, src_id, dst_id):
    
        distances = {dpid: float('inf') for dpid in self.graph}
        previous = {dpid: None for dpid in self.graph}
        distances[src_id] = 0
        queue = [(0, src_id)]
        
        while queue:
            dist, dpid = heapq.heappop(queue)
            
            if dist > distances[dpid]:
                continue
            
            for neighbor, (out_port, weight) in self.graph[dpid].items():
                new_dist = dist + weight

                if new_dist < distances[neighbor]:

                    distances[neighbor] = new_dist
                    previous[neighbor] = (dpid, out_port)
                    heapq.heappush(queue, (new_dist, neighbor))

    
        path = []
        curr_dpid = dst_id
        
        while curr_dpid != src_id:
            prev_dpid, out_port = previous[curr_dpid]
            path.append((prev_dpid, out_port))
            curr_dpid = prev_dpid
        path.reverse()
        return path

