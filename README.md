# CS305-2023Spring-Project


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
