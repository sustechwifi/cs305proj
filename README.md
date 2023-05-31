# CS305 Project:SDN

游俊涛：DHCP server

刘俊麟：Shortest path

汪清扬：flow table distribution

## DHCP Server

### screen shot

![result](https://api.apifox.cn/api/v1/projects/2429766/resources/383797/image-preview)


### tasks

+ implement `handle_dhcp(cls, datapath, port, pkt)`
+ generate DHCP OFFER packet
+ generate DHCP ack packet
+ *generate DHCP nak packet 

### implement detail

+ task 1: handle_dhcp

In this part, decode the packet and vertify its type.

Judge option(tag = 53) code in dhcp header(1 means DHCP DISCOVER packet, while 3 means DHCP REQUEST);

If rescive a dhcp discover packet:

Use `IP_POOL = ['192.168.1.{}'.format(i) for i in range(2, 100)]` and ` assigned_ip = cls.IP_POOL.pop(0)` to allocte new IP address for the coming host.

If get a dhcp request packet and the host's mac address is in the `CLIENTS` map, send a ack packet to the host.

If get a dhcp request packet and the host's mac address is not in the `CLIENTS` map, send a nak packet and let it send a dhcp discover packet again. 

``` python
        type_msg = pkt_dhcp.options.option_list[0].value
        if type_msg == b'\x03':
            if client_mac in cls.CLIENTS:
                res = cls.assemble_ack(pkt, assigned_ip)
            else: 
                res = cls.assemble_nak(pkt)
            cls._send_packet(datapath, port, res)
        elif(type_msg == b'\x01'):
            # Assign a new IP address to the client
            assigned_ip = cls.IP_POOL.pop(0)
            cls.CLIENTS[client_mac] = assigned_ip
            res = cls.assemble_offer(pkt, assigned_ip)
            cls._send_packet(datapath, port, res)
```


+ task 2 generate packets

Suppose that the dhcp server's addrss is `192.168.1.255`.

set up dhcp:

fill dhcp header including `yiaddr = assigned_ip`.

fill dhcp options:

\* noticed that the value in option entry should be set in bytes.

\* noticed that the ip address and netmask should be encode by `addrconv.ipv4.text_to_bin` method.

\* noticed that in option(tag = 53) indicate the type of message, 2 for dhcp offer, 5 for dhcp ack, 6 for dhcp nak

```python
dhcp_option_list = [
            dhcp.option(length=4,tag=1, value=addrconv.ipv4.text_to_bin(cls.netmask)),      # Subnet mask
            dhcp.option(length=4,tag=3, value=addrconv.ipv4.text_to_bin('192.168.1.255')),  # Router
            dhcp.option(length=4,tag=51, value=(259200).to_bytes(4, byteorder='big')),      # Lease time
            dhcp.option(length=1,tag=53, value=binascii.a2b_hex("05")),                     # DHCP message Type
        ]
```

set up ethernet/ip/udp

``` python
eth_pkt = ethernet.ethernet(
            dst=pkt_ethernet.src,         # host's mac address
            src=cls.hardware_addr,        # dhcp server's mac address
            ethertype=0x0800
)

ip_pkt = ipv4.ipv4(
            dst="0.0.0.0",              # broadcast
            src='192.168.1.255',        # server's ip
            proto=17,                   # udp 
            option=None,
)

udp_pkt = udp.udp(
            dst_port=68,
            src_port=67
)
```


### bonus 

1. DHCP Lease time:

In the offer packet, the Lease time field(default value is 3600 seconds, e.g 1 hour) is set in option_list. The mapping {client_mac_addr : assigned_ip} in ip pool will be erased if time pass.   

```python
dhcp.option(length=4,tag=51, value=(3600).to_bytes(4, byteorder='big')),      # Lease time

t = threading.Thread(target=remove_mapping, args=(cls.CLIENT, assigned_ip))
t.start()

def remove_mapping(dict, key):
    time.sleep(3600)  # wait 1 hour
    del dict[key]  # delete mapping
```


2. DHCP ip address collision avoidance:

In this dhcp server implement process, we use ip pool to handle ip from "192.168.1.2" to "192.168.1.100".

```python
IP_POOL = ['192.168.1.{}'.format(i) for i in range(2, 100)]   # ip pool/stack

CLIENTS = {}  # store the mapping relation {client_mac_addr : assigned_ip}
```

when need to allocte a new ip, pop one from the head of IP_POOL. e.g in dhcp offer.

```python
assigned_ip = cls.IP_POOL.pop(0)
cls.CLIENTS[client_mac] = assigned_ip
```

### problems

1. Must find out usage of API through docs
2. Some usage is hidden and hard to understand. e.g In DHCP options_list, all the value of ip or subnet mask must be encode with `addrconv.ipv4.text_to_bin` rather than "ip".encode().
3. 

## Controller

This part explains the architecture and detailed implementations of  Controller.py.   
Source code: https://github.com/sustechwifi/cs305proj/blob/ljl/controller.py

### Architecture

In the implementation of SDN using Ryu, the controller listens for the events that switch, host, link, port added or deleted, as well as the packet sent in. According to these events that affect the network composition, the relational map dictionaries, and furthermore the topology graph and the flow tables could be updated. When sending data, switches perform actions according to its flowtable, forwarding to the next switch by forwarding rules. If the switch does not know the mac address of the destination host, it will send an ARP request to the controller, and the controller will reply the mac address. The forwarding rule is set by the shortest path.

### Implementation

#### Attributes:

- **switchNum:** the number of switches
- **s_s:** a two-dimensional matrix of switches, recording links of switch id and their distance
- **mac_mac:** a two-dimensional matrix of ports, recording links of port mac
- **numInfo:** record the port mac address of each switch
- **leaveSwitchList:** switches that have left
- **DelPortList:** ports that are closed
- **other dictionaries that maps host ip, host mac, switch id, switch mac, switch port, switch datapath, etc.**

#### Functions:  

- **\_\_init__:**   
  Initialize the arrtibutes. 

- **handle_switch_add:**    
  It is called when a switch is added to the net. Relative tables are updated, including switchNum, s_s, numInfo, and other map dictionaries. The topology graph and the flow table are also updated.

- **handle_switch_delete:**   
  It is called when a switch is shut off. Relative tables are updated, including leaveSwitchList, mac_mac. The topology graph and the flow table are also updated.

- **handle_host_add:**   
  It is called when a host is added to the net. Some map dictionaries are updated. The topology graph and the flow table are also updated.

- **handle_link_add:**   
  It is called when a link is added to the net. The mac_mac is updated, and the topology graph and the flow table are also updated.

- **handle_link_delete:**   
  It is called when a link is deleted. The mac_mac is updated, and the topology graph and the flow table are also updated.

- **handle_port_modify:**   
  It is called when a port is shut off or opened. The DelPortList and s_s is updated. The topology graph and the flow table are also updated.

- **packet_in_handler:**   
  It is called when a packet is received by the controller. The controller will firstly extract informations of the packet, then handle it according to its ptotocol type. If it is a DHCP request, DHCPServer.handle_dhcp will be called; if is is a ARP request, the shortest path will be calculated using get_path function, and the mac address of the destination host will be returned.

- **update:**    
  It is called by other event-triggered functions, and used to update the topology graph and flow tables. To update the topology graph, it firstly initialize the topology graph, in which every node has a distance 0 to itself, and a big enough distance to other nodes. Secondly, it iterates through the mac_mac to get link informations, according which to update s_s. Thirdly, it compute the distance between any two switches using DIjikstra algorithm. That is, in the nested loop, it iterates over all pairs of switches and compares the distances between the paths that pass through the k-th switch and those that do not. If the path through the k-th switch is shorter, it updates the value of self.s_s[i][j] to the new shortest distance. To update the flow tables, it calls set_flowtable function.

- **add_forwarding_rule:**   
  It is called to add a fowarding rule in the flow table. OfCtl is used here to communicate.

- **delete_forwarding_rule:**   
  It is similar to the previous method, but to delete a forwarding rule.

- **print_path:**   
  It is a method to print path, making the implementation intuitive.

  It will be called after each update, so as to inform the user of the status of each switch

- **get_path:**   
  It is used to get the shortest path between two hosts. To achieve this, it uses an iterative approach to find the path from the source switch to the destination switch. In each iteration, it searches for the switches connected to the current temp_Num, which represents the current switch identifier. It selects the next switch and the corresponding output port for the path. During this process, it compares the distances of the shortest paths and chooses the shorter path to update nextNum and outputPort. Then, it appends the output result to the ans_list. If, during the iteration, it finds that testNum (used to detect if it is trapped in an infinite loop) is equal to temp_Num, it means that it is unable to find the next node and complete the path. In such cases, it returns an empty list.

- **set_flowtable:**   
  It sets the forwarding rule for every two switches, by calling delete_forwarding_rule function followed by add_forwarding_rule function iteratively. 

- **get_linkTable:**   
  It returns the information that for each switch, it links to which other switches through which port.

- **get_hostTable:**   
  It returns the information that for each host, it links to which switche through which port.

### TestCase

The result of the basic testcase:

![test1_pingall11](C:\Users\m1599\Desktop\CS305 project\CS305projController.assets\test1_pingall11.png)



![test1_pingall12](C:\Users\m1599\Desktop\CS305 project\CS305projController.assets\test1_pingall12-1685355642025-6.png)



We also created a more complex testcase as the diagram below:

```python
# test2
class Topo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        self.addLink(h1, s1)
        self.addLink(h3, s5)
        self.addLink(h4, s4)
        self.addLink(h5, s6)
        self.addLink(h2, s2)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s4)
        self.addLink(s3, s6)
        self.addLink(s2, s5)
        self.addLink(s5, s4)
        self.addLink(s4, s6)
        self.addLink(s6, s1)
```

After adding every link and switch:

![test2](C:\Users\m1599\Desktop\CS305 project\CS305projController.assets\test2.png)

This is the topology graph:

![test2_topo](C:\Users\m1599\Desktop\CS305 project\CS305projController.assets\test2_topo.jpg)

Pingall1:
![test2_pingall_11](C:\Users\m1599\Desktop\CS305 project\CS305projController.assets\test2_pingall_11.png)

![test2_pingall12](C:\Users\m1599\Desktop\CS305 project\CS305projController.assets\test2_pingall12.png)

