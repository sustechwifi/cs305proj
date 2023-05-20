from ryu.lib import addrconv
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.lib.packet import dhcp

'''
sudo mn -c

D
ryu-manager --observe-links controller.py 

cd ./tests/dhcp_test/
sudo env "PATH=$PATH" python test_network.py 
'''


       
'''
fields

ipv4(
    csum=14742,
    dst='255.255.255.255',
    flags=0,
    header_length=5,
    identification=0,
    offset=0,
    option=None,
    proto=17,
    src='0.0.0.0',
    tos=16,
    total_length=328,
    ttl=128,
    version=4
)

ethernet(
    dst='ff:ff:ff:ff:ff:ff',
    ethertype=2048,
    src='00:00:00:00:00:01'
)

dhcp(
    boot_file='0x00',
    chaddr='00:00:00:00:00:01',
    ciaddr='0.0.0.0',
    flags=0,
    giaddr='0.0.0.0',
    hlen=6,
    hops=0,
    htype=1,
    op=1,
    options=options(
        magic_cookie='99.130.83.99',
        option_list=[
            option(length=1,tag=53,value=b'\x01'), 
            option(length=10,tag=12,value=b'mininet-vm'), 
            option(length=13,tag=55,value='')
            ],
        options_len=64
        ),
    secs=11,
    siaddr='0.0.0.0',
    sname='\\x00',
    xid=2320355658,
    yiaddr='0.0.0.0'
)

udp(
    csum=31329,
    dst_port=67,
    src_port=68,
    total_length=308
)
'''


class Config():
    controller_macAddr = '7e:49:b3:f0:f9:99' # don't modify, a dummy mac address for fill the mac enrty
    dns = '8.8.8.8' # don't modify, just for the dns entry
    start_ip = '192.168.1.2' # can be modified
    end_ip = '192.168.1.100' # can be modified
    netmask = '255.255.255.0' # can be modified

    # You may use above attributes to configure your DHCP server.
    # You can also add more attributes like "lease_time" to support bouns function.


class DHCPServer():
    hardware_addr = Config.controller_macAddr
    start_ip = Config.start_ip
    end_ip = Config.end_ip
    netmask = Config.netmask
    dns = Config.dns

    IP_POOL = ['192.168.1.{}'.format(i) for i in range(2, 100)]
    CLIENTS = {}


    @classmethod
    def assemble_ack(cls, pkt, ip):
        # TODO: Generate DHCP ACK packet here
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        # pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]
        pkt_dhcp = pkt.get_protocols(dhcp.dhcp)[0]
        # pkt_udp = pkt.get_protocols(udp.udp)[0]

        # Generate DHCP OFFER packet
        dhcp_offer = dhcp.dhcp(
            op=2,                       # BOOTREPLY
            htype=1,                    # Ethernet
            xid=pkt_dhcp.xid,
            yiaddr=ip,                  # Offered IP address
            chaddr=pkt_ethernet.src,
            ciaddr='0.0.0.0',
            hops=1,
        )
        
        dhcp_option_list = [
            dhcp.option(length=4,tag=1, value=cls.netmask.encode()),  # Subnet mask
            # dhcp.option(length=4,tag=3, value='192.168.1.1'.encode()),  # Router
            # dhcp.option(length=4,tag=6, value=cls.dns.encode()),  # DNS server
            dhcp.option(length=4,tag=51, value=(259200).to_bytes(4, byteorder='big')),  # Lease time
            dhcp.option(length=1,tag=53, value=(5).to_bytes(1,"big")),  # DHCP ACK
            # dhcp.option(length=4,tag=54, value='192.168.1.1'.encode()),  # DHCP server
        ]
        options = dhcp.options(
            option_list=dhcp_option_list
        )
        dhcp_offer.options = options

        # Generate Ethernet/IP/UDP headers

        eth_pkt = ethernet.ethernet(
            dst=pkt_ethernet.src,
            src=cls.hardware_addr,
            ethertype=0x0800
        )
        ip_pkt = ipv4.ipv4(
            dst=ip,
            src='192.168.1.1',
            proto=17,
            option=None,
        )
        udp_pkt = udp.udp(
            dst_port=68,
            src_port=67
        )

        # Assemble the packet
        ack_packet = packet.Packet()
        ack_packet.add_protocol(eth_pkt)
        ack_packet.add_protocol(ip_pkt)
        ack_packet.add_protocol(udp_pkt)
        ack_packet.add_protocol(dhcp_offer)
        return ack_packet

    @classmethod
    def assemble_offer(cls, pkt, ip):
        # TODO: Generate DHCP OFFER packet here
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        # pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]
        pkt_dhcp = pkt.get_protocols(dhcp.dhcp)[0]
        # pkt_udp = pkt.get_protocols(udp.udp)[0]

        # Generate DHCP OFFER packet
        dhcp_offer = dhcp.dhcp(
            op=2,                       # BOOTREPLY
            htype=1,                    # Ethernet
            xid=pkt_dhcp.xid,
            yiaddr=ip,                  # Offered IP address
            chaddr=pkt_ethernet.src,
            ciaddr='0.0.0.0',
            hops=1,
        )
        
        dhcp_option_list = [
            dhcp.option(length=4,tag=1, value=cls.netmask.encode()),  # Subnet mask
            # dhcp.option(length=4,tag=3, value='192.168.1.1'.encode()),  # Router
            # dhcp.option(length=4,tag=6, value=cls.dns.encode()),  # DNS server
            dhcp.option(length=4,tag=51, value=(259200).to_bytes(4, byteorder='big')),  # Lease time
            dhcp.option(length=1,tag=53, value=(2).to_bytes(1,"big")),  # DHCP OFFER
            # dhcp.option(length=4,tag=54, value='192.168.1.1'.encode()),  # DHCP server
        ]
        options = dhcp.options(
            option_list=dhcp_option_list
        )
        dhcp_offer.options = options

        # Generate Ethernet/IP/UDP headers

        eth_pkt = ethernet.ethernet(
            dst=pkt_ethernet.src,
            src=cls.hardware_addr,
            ethertype=0x0800
        )
        ip_pkt = ipv4.ipv4(
            dst=ip,
            src='192.168.1.1',
            proto=17,
            option=None,
        )
        udp_pkt = udp.udp(
            dst_port=68,
            src_port=67
        )
        # Assemble the packet
        offer_pkt = packet.Packet()
        offer_pkt.add_protocol(eth_pkt)
        offer_pkt.add_protocol(ip_pkt)
        offer_pkt.add_protocol(udp_pkt)
        offer_pkt.add_protocol(dhcp_offer)
        return offer_pkt


    @classmethod
    def handle_dhcp(cls, datapath, port, pkt):
        # TODO: Specify the type of received DHCP packet
        # You may choose a valid IP from IP pool and genereate DHCP OFFER packet
        # Or generate a DHCP ACK packet
        # Finally send the generated packet to the host by using _send_packet method
        # pkt_dhcp = pkt.get_protocols(dhcp.dhcp)[0]
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]
        
        # Get client MAC address and requested IP address
        client_mac = pkt_ethernet.src
        requested_ip = pkt_ipv4.src

        # Check if the client has already been assigned an IP address
        if client_mac in cls.CLIENTS:
            assigned_ip = cls.CLIENTS[client_mac]
            if assigned_ip == requested_ip or requested_ip == "0.0.0.0":
                # Client has already been assigned the requested IP address or request
                print("============ sending ack packets ============")
                res = cls.assemble_ack(pkt, assigned_ip)
                print(res)
                cls._send_packet(datapath, port, res)
            else:
                print("================== send nak =================")
                # Client has been assigned a different IP address
                cls._send_packet(datapath, port, cls._generate_dhcp_nak(pkt))
        else:
            # Assign a new IP address to the client
            if requested_ip in cls.IP_POOL:
                assigned_ip = requested_ip
            else:
                assigned_ip = cls.IP_POOL.pop(0)
            cls.CLIENTS[client_mac] = assigned_ip
            print("============== send offer ==============")
            res = cls.assemble_offer(pkt, assigned_ip)
            print(res)
            cls._send_packet(datapath, port, res)

    @classmethod
    def _generate_dhcp_nak(cls, pkt):
        # TODO: Generate DHCP NAK packet
        return pkt 
       

    @classmethod
    def _send_packet(cls, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if isinstance(pkt, str):
            pkt = pkt.encode()
        pkt.serialize()
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)


