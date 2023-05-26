from ryu.lib import addrconv
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.lib.packet import dhcp
from ryu.lib.packet.dhcp import options
import socket
import binascii

'''
sudo mn -c

conda activate cs305
ryu-manager --observe-links controller.py 

cd ./tests/dhcp_test/
sudo env "PATH=$PATH" python test_network.py 
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
    def assemble_nak(cls, pkt):
        # TODO: Generate DHCP ACK packet here
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        # pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]
        pkt_dhcp = pkt.get_protocols(dhcp.dhcp)[0]
        # pkt_udp = pkt.get_protocols(udp.udp)[0]

        # Generate DHCP OFFER packet
        dhcp_ack = dhcp.dhcp(
            op=2,                       # BOOTREPLY
            htype=1,                    # Ethernet
            xid=pkt_dhcp.xid,
            chaddr=pkt_ethernet.src,
            hops=1,
        )
        
        dhcp_option_list = [
            dhcp.option(length=1,tag=53, value=(6).to_bytes(1,"big")),  # DHCP NAK
        ]
        options = dhcp.options(
            option_list=dhcp_option_list
        )
        dhcp_ack.options = options

        # Generate Ethernet/IP/UDP headers

        eth_pkt = ethernet.ethernet(
            dst=pkt_ethernet.src,
            src=cls.hardware_addr,
            ethertype=0x0800
        )
        ip_pkt = ipv4.ipv4(
            src='192.168.1.255',
            proto=17,
            option=None,
        )
        udp_pkt = udp.udp(
            dst_port=68,
            src_port=67
        )

        # Assemble the packet
        nak_packet = packet.Packet()
        nak_packet.add_protocol(eth_pkt)
        nak_packet.add_protocol(ip_pkt)
        nak_packet.add_protocol(udp_pkt)
        nak_packet.add_protocol(dhcp_ack)
        return nak_packet

    @classmethod
    def assemble_ack(cls, pkt, ip):
        # TODO: Generate DHCP ACK packet here
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        # pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]
        pkt_dhcp = pkt.get_protocols(dhcp.dhcp)[0]
        # pkt_udp = pkt.get_protocols(udp.udp)[0]

        # Generate DHCP OFFER packet
        dhcp_ack = dhcp.dhcp(
            op=2,                       # BOOTREPLY
            htype=1,                    # Ethernet
            xid=pkt_dhcp.xid,
            yiaddr=ip,                  # Offered IP address
            chaddr=pkt_ethernet.src,
            hops=1,
        )
        
        dhcp_option_list = [
            dhcp.option(length=4,tag=1, value=addrconv.ipv4.text_to_bin(cls.netmask)),  # Subnet mask
            dhcp.option(length=4,tag=3, value=addrconv.ipv4.text_to_bin('192.168.1.255')),  # Router
            # dhcp.option(length=4,tag=6, value=cls.dns.encode()),  # DNS server
            dhcp.option(length=4,tag=51, value=(3600).to_bytes(4, byteorder='big')),  # Lease time
            dhcp.option(length=1,tag=53, value=binascii.a2b_hex("05")),  # DHCP ACK
            # dhcp.option(length=4,tag=54, value='192.168.1.255'.encode()),  # DHCP server
        ]
        options = dhcp.options(
            option_list=dhcp_option_list
        )
        dhcp_ack.options = options

        # Generate Ethernet/IP/UDP headers

        eth_pkt = ethernet.ethernet(
            dst=pkt_ethernet.src,
            src=cls.hardware_addr,
            ethertype=0x0800
        )
        ip_pkt = ipv4.ipv4(
            dst="0.0.0.0",
            src='192.168.1.255',
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
        ack_packet.add_protocol(dhcp_ack)

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
            hops=1,
        )
        
        dhcp_option_list = [
            dhcp.option(length=4,tag=1, value=addrconv.ipv4.text_to_bin(cls.netmask)),  # Subnet mask
            dhcp.option(length=4,tag=3, value=addrconv.ipv4.text_to_bin("192.168.1.255")),  # Router
            # dhcp.option(length=4,tag=6, value=cls.dns.encode()),  # DNS server
            dhcp.option(length=4,tag=51, value=(3600).to_bytes(4, byteorder='big')),  # Lease time
            dhcp.option(length=1,tag=53, value=binascii.a2b_hex("02")),  # DHCP OFFER
            # dhcp.option(length=4,tag=54, value='192.168.1.255'.encode()),  # DHCP server
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
            dst="0.0.0.0",
            src='192.168.1.255',
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
        pkt_dhcp = pkt.get_protocols(dhcp.dhcp)[0]
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]

        # Get client MAC address and requested IP address
        client_mac = pkt_ethernet.src

        type_msg = pkt_dhcp.options.option_list[0].value
        if type_msg == b'\x03':
            for i in pkt_dhcp.options.option_list:
                if i.tag == 50:
                    assigned_ip = socket.inet_ntoa(i.value)
         
            # Client has already been assigned the requested IP address or request
            if client_mac in cls.CLIENTS:
                print("============ sending ack packets ============")
                res = cls.assemble_ack(pkt, assigned_ip)
            else: 
                print("============ sending nak packets ============")
                res = cls.assemble_nak(pkt)
            cls._send_packet(datapath, port, res)
 
        elif(type_msg == b'\x01'):

            # Assign a new IP address to the client
            assigned_ip = cls.IP_POOL.pop(0)
            cls.CLIENTS[client_mac] = assigned_ip
            print("============== send offer ==============")
            res = cls.assemble_offer(pkt, assigned_ip)
            cls._send_packet(datapath, port, res)
        else:
            print(type_msg)


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

